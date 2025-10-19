"""CrewAI orchestration - coordinates all agents for property analysis."""
import asyncio
import json
from typing import Optional
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
        
        self.weights = settings.get_weights()
    
    def _format_listing_details(self, listing: Listing) -> str:
        """Format listing data for agent consumption."""
        return f"""
Address: {listing.address or 'N/A'}
City: {listing.city or 'N/A'}, State: {listing.state or 'N/A'}
Asking Price: ${listing.ask_price:,.0f} if {listing.ask_price} else 'N/A'
Building Size: {listing.building_size:,.0f} SF if {listing.building_size} else 'N/A'
Property Type: {listing.property_type or 'N/A'}
Cap Rate: {listing.cap_rate}% if {listing.cap_rate} else 'N/A'
Year Built: {listing.year_built or 'N/A'}
Units: {listing.units or 'N/A'}
"""

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
    
    async def analyze_listing(self, listing: Listing) -> FinalReport:
        """
        Run full multi-agent analysis on a single listing.
        
        Args:
            listing: Property listing to analyze
        
        Returns:
            FinalReport with scores and memo
        """
        listing_details = self._format_listing_details(listing)
        location_details = f"{listing.city}, {listing.state}" if listing.city else "Unknown location"

        # Prefetch news context (Serper)
        news_query = self._build_news_query(listing)
        news_response = await asyncio.to_thread(search_news, news_query, 8)
        news_context = self._format_news_context(news_response)
        serper_missing = news_response.get("note") == "SERPER_API_KEY missing"

        # Create tasks for all specialist agents
        investor_task = Task(
            description=INVESTOR_TASK_TEMPLATE.format(listing_details=listing_details),
            agent=self.investor_agent,
            expected_output="JSON with score_1_to_100, rationale, and notes"
        )
        
        location_task = Task(
            description=LOCATION_TASK_TEMPLATE.format(location_details=location_details),
            agent=self.location_agent,
            expected_output="JSON with score_1_to_100, rationale, and notes"
        )
        
        news_task = None
        if not serper_missing:
            news_task = Task(
                description=NEWS_TASK_TEMPLATE.format(
                    area_info=location_details,
                    news_data=news_context
                ),
                agent=self.news_agent,
                expected_output="JSON with score_1_to_100, rationale, and notes"
            )
        
        vc_risk_task = Task(
            description=VC_RISK_TASK_TEMPLATE.format(property_details=listing_details),
            agent=self.vc_risk_agent,
            expected_output="JSON with score_1_to_100, rationale, and notes"
        )
        
        construction_task = Task(
            description=CONSTRUCTION_TASK_TEMPLATE.format(property_info=listing_details),
            agent=self.construction_agent,
            expected_output="JSON with score_1_to_100, rationale, and notes"
        )
        
        # Run specialist agents in crew
        agents = [
            self.investor_agent,
            self.location_agent,
            self.vc_risk_agent,
            self.construction_agent
        ]
        if news_task:
            agents.insert(2, self.news_agent)

        tasks = [
            investor_task,
            location_task,
            vc_risk_task,
            construction_task
        ]
        if news_task:
            tasks.insert(2, news_task)

        specialist_crew = Crew(
            agents=agents,
            tasks=tasks,
            verbose=False
        )

        # Execute specialist analysis
        results = await asyncio.to_thread(specialist_crew.kickoff)
        
        # Parse specialist outputs
        investment_output = self._parse_agent_output(investor_task.output.raw_output if hasattr(investor_task.output, 'raw_output') else str(results))
        location_output = self._parse_agent_output(location_task.output.raw_output if hasattr(location_task.output, 'raw_output') else str(results))
        if news_task:
            news_output = self._parse_agent_output(
                news_task.output.raw_output if hasattr(news_task.output, 'raw_output') else str(results)
            )
        else:
            news_output = AgentOutput(
                score_1_to_100=50,
                rationale="Serper API key missing; defaulting to a neutral risk score.",
                notes=[
                    "Serper API key missing; unable to fetch external news signals.",
                    "Please set SERPER_API_KEY to enable news analysis."
                ]
            )
        vc_risk_output = self._parse_agent_output(vc_risk_task.output.raw_output if hasattr(vc_risk_task.output, 'raw_output') else str(results))
        construction_output = self._parse_agent_output(construction_task.output.raw_output if hasattr(construction_task.output, 'raw_output') else str(results))
        
        # Calculate overall score
        scores_dict = {
            "investment": investment_output.score_1_to_100,
            "location": location_output.score_1_to_100,
            "news": news_output.score_1_to_100,
            "vc_risk": vc_risk_output.score_1_to_100,
            "construction": construction_output.score_1_to_100
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
                property_summary=listing_details,
                specialist_scores=specialist_scores,
                specialist_rationales=specialist_rationales
            ),
            agent=self.aggregator_agent,
            expected_output="JSON with overall score and markdown memo"
        )
        
        aggregator_crew = Crew(
            agents=[self.aggregator_agent],
            tasks=[aggregator_task],
            verbose=False
        )
        
        aggregator_result = aggregator_crew.kickoff()
        aggregator_output = self._parse_agent_output(
            aggregator_task.output.raw_output if hasattr(aggregator_task.output, 'raw_output') else str(aggregator_result)
        )
        
        # Extract memo from notes
        memo_markdown = "\n".join(aggregator_output.notes) if aggregator_output.notes else "No memo generated"
        
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
            investment_output=investment_output,
            location_output=location_output,
            news_output=news_output,
            vc_risk_output=vc_risk_output,
            construction_output=construction_output
        )
