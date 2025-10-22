"""CrewAI orchestration - coordinates all agents for property analysis."""
import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Optional, Sequence
from crewai import Crew, Task

from .models import Listing, AgentOutput, FinalReport, AgentScores
from .config import settings
from .scoring import weighted_overall, to_int_1_100
from .serper_news import search_news
from ..agents.investor import create_investor_agent, INVESTOR_TASK_TEMPLATE
from ..agents.location_risk import create_location_agent, LOCATION_TASK_TEMPLATE
from ..agents.news_reddit import create_news_agent, NEWS_TASK_TEMPLATE
from ..agents.vc_risk_return import create_vc_risk_agent, VC_RISK_TASK_TEMPLATE
from ..agents.construction import create_construction_agent, CONSTRUCTION_TASK_TEMPLATE
from ..agents.aggregator import create_aggregator_agent, AGGREGATOR_TASK_TEMPLATE
from ..agents.la_property_ingestor import (
    create_la_property_agent,
    LAPropertyIngestorAgent,
)
from .la_socrata import LASocrataError


ALL_AGENT_KEYS: tuple[str, ...] = (
    "investment",
    "location",
    "news",
    "vc_risk",
    "construction",
)


@dataclass
class SpecialistResult:
    """Intermediate results from specialist agents."""

    outputs: dict[str, AgentOutput]
    raw_outputs: dict[str, str]
    listing_details: str
    location_details: str
    news_context: str
    serper_missing: bool
    la_city_records: Optional[dict[str, Any]] = None


logger = logging.getLogger(__name__)


class PropertyAnalysisCrew:
    """Orchestrates multi-agent analysis of property listings."""
    
    def __init__(self):
        """Initialize all agents once for reuse."""
        self.investor_agent = create_investor_agent()
        self.location_agent = create_location_agent()
        self.news_agent = create_news_agent()
        self.vc_risk_agent = create_vc_risk_agent()
        self.construction_agent = create_construction_agent()
        self.aggregator_agent = create_aggregator_agent()
        self._la_property_agent: Optional[LAPropertyIngestorAgent] = None
        
        self.weights = settings.get_weights()

    @property
    def la_property_agent(self) -> LAPropertyIngestorAgent:
        """Lazy-create the LA property ingestion agent on demand."""
        if self._la_property_agent is None:
            self._la_property_agent = create_la_property_agent()
        return self._la_property_agent

    def fetch_la_city_records(self, listing: Listing, *, limit: int = 50) -> dict[str, Any]:
        """Public helper for retrieving LA records for a listing."""
        return self.la_property_agent.fetch_for_listing(listing, limit=limit)

    def run_la_city_task(
        self,
        *,
        address: str,
        zip_code: Optional[str] = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Fetch LA datasets for an arbitrary address to mirror task wiring."""
        return self.la_property_agent.fetch(address=address, zip_code=zip_code, limit=limit)
    
    def _format_listing_details(self, listing: Listing) -> str:
        """Format listing data for agent consumption."""
        ask_price = f"${listing.ask_price:,.0f}" if listing.ask_price else "N/A"
        building_size = (
            f"{listing.building_size:,.0f} SF" if listing.building_size else "N/A"
        )
        cap_rate = f"{listing.cap_rate}%" if listing.cap_rate else "N/A"
        return (
            "Address: {address}\n"
            "City: {city}, State: {state}\n"
            "Asking Price: {ask_price}\n"
            "Building Size: {building_size}\n"
            "Property Type: {property_type}\n"
            "Cap Rate: {cap_rate}\n"
            "Year Built: {year_built}\n"
            "Units: {units}\n"
        ).format(
            address=listing.address or "N/A",
            city=listing.city or "N/A",
            state=listing.state or "N/A",
            ask_price=ask_price,
            building_size=building_size,
            property_type=listing.property_type or "N/A",
            cap_rate=cap_rate,
            year_built=listing.year_built or "N/A",
            units=listing.units or "N/A",
        )

    def _build_news_query(self, listing: Listing) -> str:
        """Assemble a Serper query using listing metadata."""
        parts = []
        if listing.city:
            parts.append(listing.city)
        if listing.state and listing.state not in parts:
            parts.append(listing.state)
        if listing.property_type:
            parts.append(listing.property_type)
        parts.append("commercial real estate")
        return " ".join(part for part in parts if part).strip()

    def _format_news_context(self, response: dict) -> str:
        """Render Serper response into agent-friendly markdown."""
        items = response.get("items") or []
        note = response.get("note")
        if not items:
            base = "No Serper news items available."
            if note:
                return f"{base}\nNote: {note}"
            return base

        lines = ["Recent Serper news results:"]
        for item in items[:8]:
            title = item.get("title") or "Untitled"
            source = item.get("source") or "Unknown source"
            date = item.get("date") or "Unknown date"
            snippet = item.get("snippet") or ""
            link = item.get("link") or ""
            lines.append(
                f"- [{date}] {source}: {title}\n  Summary: {snippet}\n  Link: {link}"
            )
        if note:
            lines.append(f"Note: {note}")
        return "\n".join(lines)
    
    def _parse_agent_output(self, raw_output: str) -> Optional[AgentOutput]:
        """
        Parse agent output from JSON string.
        
        Handles various formats and extraction issues.
        """
        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in raw_output:
                start = raw_output.find("```json") + 7
                end = raw_output.find("```", start)
                json_str = raw_output[start:end].strip()
            elif "```" in raw_output:
                start = raw_output.find("```") + 3
                end = raw_output.find("```", start)
                json_str = raw_output[start:end].strip()
            else:
                json_str = raw_output.strip()
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Validate and create AgentOutput
            return AgentOutput(
                score_1_to_100=to_int_1_100(data.get("score_1_to_100", 50)),
                rationale=data.get("rationale", "No rationale provided"),
                notes=data.get("notes", [])
            )
        except Exception as e:
            # Fallback to neutral score if parsing fails
            print(f"Warning: Failed to parse agent output: {e}")
            return AgentOutput(
                score_1_to_100=50,
                rationale=f"Parse error: {str(e)}",
                notes=["Failed to parse agent response"]
            )

    @staticmethod
    def _extract_raw_output(task_output) -> str:
        """Extract a raw string representation from a CrewAI TaskOutput."""
        if getattr(task_output, "raw", None):
            return task_output.raw
        if getattr(task_output, "json_dict", None):
            try:
                return json.dumps(task_output.json_dict)
            except Exception:
                return str(task_output.json_dict)
        return str(task_output)
    
    async def run_specialists(
        self,
        listing: Listing,
        enabled_agents: Optional[Sequence[str]] = None,
    ) -> SpecialistResult:
        """Run specialist agents and return their parsed outputs."""

        enabled_set = set(enabled_agents) if enabled_agents else set(ALL_AGENT_KEYS)

        listing_details = self._format_listing_details(listing)
        location_details = (
            f"{listing.city}, {listing.state}"
            if listing.city and listing.state
            else listing.city
            if listing.city
            else "Unknown location"
        )

        include_la_city = listing.address and (
            enabled_agents is None or "la_city" in enabled_set
        )

        la_city_records: Optional[dict[str, Any]] = None
        if include_la_city and listing.address:
            try:
                la_city_records = self.fetch_la_city_records(listing)
            except (LASocrataError, ValueError) as exc:
                logger.warning(
                    "LA city records unavailable for %s (%s)",
                    listing.address,
                    exc,
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Unexpected LA property ingestion failure: %s", exc)

        outputs: dict[str, AgentOutput] = {}
        raw_outputs: dict[str, str] = {}

        if la_city_records is not None:
            try:
                raw_outputs["la_city_records"] = json.dumps(la_city_records)
            except TypeError:
                raw_outputs["la_city_records"] = str(la_city_records)

        # Prepare Serper context only when news agent is enabled
        news_context = ""
        serper_missing = False
        news_response: dict | None = None

        if "news" in enabled_set:
            news_query = self._build_news_query(listing)
            news_response = await asyncio.to_thread(search_news, news_query, 8)
            news_context = self._format_news_context(news_response)
            serper_missing = news_response.get("note") == "SERPER_API_KEY missing"

            if serper_missing:
                outputs["news"] = AgentOutput(
                    score_1_to_100=50,
                    rationale="Serper API key missing; defaulting to neutral score.",
                    notes=[
                        "Set SERPER_API_KEY to enable news sentiment analysis.",
                        "Without news signals, rely on other agents for sentiment.",
                    ],
                )
                raw_outputs["news"] = "Serper API key missing"

        # Build tasks for enabled specialist agents
        tasks: list[Task] = []
        task_labels: list[str] = []
        crew_agents = []

        if "investment" in enabled_set:
            investor_task = Task(
                description=INVESTOR_TASK_TEMPLATE.format(listing_details=listing_details),
                agent=self.investor_agent,
                expected_output="JSON with score_1_to_100, rationale, and notes",
            )
            tasks.append(investor_task)
            task_labels.append("investment")
            crew_agents.append(self.investor_agent)

        if "location" in enabled_set:
            location_task = Task(
                description=LOCATION_TASK_TEMPLATE.format(location_details=location_details),
                agent=self.location_agent,
                expected_output="JSON with score_1_to_100, rationale, and notes",
            )
            tasks.append(location_task)
            task_labels.append("location")
            crew_agents.append(self.location_agent)

        if "news" in enabled_set and not serper_missing:
            news_task = Task(
                description=NEWS_TASK_TEMPLATE.format(
                    area_info=location_details,
                    news_data=news_context,
                ),
                agent=self.news_agent,
                expected_output="JSON with score_1_to_100, rationale, and notes",
            )
            tasks.append(news_task)
            task_labels.append("news")
            crew_agents.append(self.news_agent)

        if "vc_risk" in enabled_set:
            vc_risk_task = Task(
                description=VC_RISK_TASK_TEMPLATE.format(property_details=listing_details),
                agent=self.vc_risk_agent,
                expected_output="JSON with score_1_to_100, rationale, and notes",
            )
            tasks.append(vc_risk_task)
            task_labels.append("vc_risk")
            crew_agents.append(self.vc_risk_agent)

        if "construction" in enabled_set:
            construction_task = Task(
                description=CONSTRUCTION_TASK_TEMPLATE.format(property_info=listing_details),
                agent=self.construction_agent,
                expected_output="JSON with score_1_to_100, rationale, and notes",
            )
            tasks.append(construction_task)
            task_labels.append("construction")
            crew_agents.append(self.construction_agent)

        if tasks:
            specialist_crew = Crew(
                agents=crew_agents,
                tasks=tasks,
                verbose=False,
            )
            crew_output = await asyncio.to_thread(specialist_crew.kickoff)

            for label, task_output in zip(task_labels, crew_output.tasks_output):
                raw_str = self._extract_raw_output(task_output)
                raw_outputs[label] = raw_str
                outputs[label] = self._parse_agent_output(raw_str)

        # Fill in defaults for any agents that were not executed
        skipped_agents = set(ALL_AGENT_KEYS) - set(outputs.keys())
        for agent_key in skipped_agents:
            if agent_key not in enabled_set:
                outputs[agent_key] = AgentOutput(
                    score_1_to_100=50,
                    rationale="Agent not selected for this run; using neutral score.",
                    notes=["Agent skipped by user"],
                )
                raw_outputs[agent_key] = "Agent skipped"
            elif agent_key == "news" and serper_missing:
                # already populated earlier
                continue
            else:
                outputs[agent_key] = AgentOutput(
                    score_1_to_100=50,
                    rationale="Agent failed to produce output; defaulting to neutral score.",
                    notes=["Check agent configuration or API responses."],
                )
                raw_outputs[agent_key] = "Agent output missing"

        return SpecialistResult(
            outputs=outputs,
            raw_outputs=raw_outputs,
            listing_details=listing_details,
            location_details=location_details,
            news_context=news_context,
            serper_missing=serper_missing,
            la_city_records=la_city_records,
        )

    async def analyze_listing(
        self,
        listing: Listing,
        enabled_agents: Optional[Sequence[str]] = None,
    ) -> FinalReport:
        specialist_result = await self.run_specialists(listing, enabled_agents)
        return await self.build_final_report(listing, specialist_result)

    async def build_final_report(
        self,
        listing: Listing,
        specialist_result: SpecialistResult,
    ) -> FinalReport:
        """
        Run full multi-agent analysis on a single listing.
        
        Args:
            listing: Property listing to analyze
        
        Returns:
            FinalReport with scores and memo
        """
        outputs = specialist_result.outputs

        investment_output = outputs["investment"]
        location_output = outputs["location"]
        news_output = outputs["news"]
        vc_risk_output = outputs["vc_risk"]
        construction_output = outputs["construction"]

        scores_dict = {
            "investment": investment_output.score_1_to_100,
            "location": location_output.score_1_to_100,
            "news": news_output.score_1_to_100,
            "vc_risk": vc_risk_output.score_1_to_100,
            "construction": construction_output.score_1_to_100,
        }
        overall_score = weighted_overall(scores_dict, self.weights)
        
        # Prepare aggregator input
        specialist_scores = f"""
Investment Analyst: {investment_output.score_1_to_100}/100
Location Risk: {location_output.score_1_to_100}/100
News Signals: {news_output.score_1_to_100}/100
VC Risk/Return: {vc_risk_output.score_1_to_100}/100
Construction: {construction_output.score_1_to_100}/100
Weighted Overall: {overall_score}/100
"""
        
        specialist_rationales = f"""
**Investment:** {investment_output.rationale}
Notes: {', '.join(investment_output.notes[:3])}

**Location:** {location_output.rationale}
Notes: {', '.join(location_output.notes[:3])}

**News:** {news_output.rationale}
Notes: {', '.join(news_output.notes[:3])}

**VC Risk:** {vc_risk_output.rationale}
Notes: {', '.join(vc_risk_output.notes[:3])}

**Construction:** {construction_output.rationale}
Notes: {', '.join(construction_output.notes[:3])}
"""
        
        # Run aggregator
        aggregator_task = Task(
            description=AGGREGATOR_TASK_TEMPLATE.format(
                property_summary=specialist_result.listing_details,
                specialist_scores=specialist_scores,
                specialist_rationales=specialist_rationales
            ),
            agent=self.aggregator_agent,
            expected_output="JSON with overall score and markdown memo"
        )
        
        aggregator_crew = Crew(
            agents=[self.aggregator_agent],
            tasks=[aggregator_task],
            verbose=False,
        )
        aggregator_result = await asyncio.to_thread(aggregator_crew.kickoff)
        if aggregator_result.tasks_output:
            aggregator_raw = self._extract_raw_output(aggregator_result.tasks_output[-1])
        else:
            aggregator_raw = str(aggregator_result)
        aggregator_output = self._parse_agent_output(aggregator_raw)
        
        # Extract memo from notes
        memo_markdown = "\n".join(aggregator_output.notes) if aggregator_output.notes else "No memo generated"
        summary_text = (
            aggregator_output.rationale
            if aggregator_output and aggregator_output.rationale
            else "Summary unavailable"
        )
        
        # Build final report
        agent_scores = AgentScores(
            investment=investment_output.score_1_to_100,
            location=location_output.score_1_to_100,
            news_signal=news_output.score_1_to_100,
            risk_return=vc_risk_output.score_1_to_100,
            construction=construction_output.score_1_to_100,
            overall=overall_score
        )
        
        return FinalReport(
            listing_id=listing.listing_id,
            address=listing.address,
            ask_price=listing.ask_price,
            raw=listing.raw,
            scores=agent_scores,
            memo_markdown=memo_markdown,
            summary=summary_text,
            investment_output=investment_output,
            location_output=location_output,
            news_output=news_output,
            vc_risk_output=vc_risk_output,
            construction_output=construction_output
        )
