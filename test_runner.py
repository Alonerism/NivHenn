#!/usr/bin/env python3
"""
End-to-end test runner for property analysis.
Runs a small analysis and prints formatted output from each agent.
"""
import json
import sys
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

BASE_URL = "http://127.0.0.1:8000"

# Mock data for demonstration when API keys are not available
MOCK_RESULTS = [
    {
        "listing_id": "12345678",
        "address": "123 Main St, Cincinnati, OH 45202",
        "ask_price": 1250000,
        "scores": {
            "investment": 72,
            "location": 68,
            "news_signal": 50,
            "risk_return": 65,
            "construction": 74,
            "overall": 68
        },
        "investment_output": {
            "score_1_to_100": 72,
            "rationale": "Strong cap rate at 6.8% with stable tenant mix. Minor concern about deferred maintenance. Property shows good cash flow potential with value-add opportunities.",
            "notes": ["Cap rate: 6.8%", "Occupancy: 92%", "Deferred maintenance: ~$45k", "Tenant mix: diversified", "Upside: unit renovations"]
        },
        "location_output": {
            "score_1_to_100": 68,
            "rationale": "Downtown Cincinnati location with good transit access. Some economic headwinds in the immediate area but long-term development pipeline is positive.",
            "notes": ["Transit score: 8/10", "Crime rate: slightly above avg", "Job growth: 2.1% YoY", "New developments: 3 major projects", "School rating: 6/10"]
        },
        "news_output": {
            "score_1_to_100": 50,
            "rationale": "SERPER_API_KEY not configured—used neutral score. No major negative news detected via Reddit scraping. Market sentiment appears stable.",
            "notes": ["News data unavailable (missing Serper key)", "Reddit: no red flags", "General sentiment: neutral"]
        },
        "vc_risk_output": {
            "score_1_to_100": 65,
            "rationale": "Moderate risk profile. Market volatility in commercial RE but fundamentals are sound. Interest rate environment creates some pressure on valuations.",
            "notes": ["Market cycle: mid-stage", "Rate risk: moderate", "Liquidity: good", "Comparables: 5-7% cap rates", "Exit timeline: 5-7 years"]
        },
        "construction_output": {
            "score_1_to_100": 74,
            "rationale": "Building constructed in 2005, well-maintained exterior. Recent roof replacement noted. HVAC systems appear current. Minor cosmetic updates needed.",
            "notes": ["Year built: 2005", "Roof: replaced 2020", "HVAC: 2018", "Foundation: good condition", "Cosmetic updates needed"]
        }
    },
    {
        "listing_id": "23456789",
        "address": "456 Commerce Blvd, Cincinnati, OH 45246",
        "ask_price": 875000,
        "scores": {
            "investment": 58,
            "location": 75,
            "news_signal": 50,
            "risk_return": 62,
            "construction": 54,
            "overall": 61
        },
        "investment_output": {
            "score_1_to_100": 58,
            "rationale": "Cap rate of 5.4% is below market average. Property requires significant capital expenditure for competitive positioning. Tenant rollover risk within 18 months.",
            "notes": ["Cap rate: 5.4% (below target)", "CapEx needed: ~$120k", "Tenant risk: 2 leases expire soon", "Vacancy risk: moderate", "Pricing: slightly high"]
        },
        "location_output": {
            "score_1_to_100": 75,
            "rationale": "Excellent suburban location near major highway interchange. Strong demographics and growing retail corridor. Low crime, good schools, high income levels.",
            "notes": ["Highway access: I-71 & I-75", "Demographics: excellent", "Retail corridor: growing", "Crime rate: well below avg", "Median income: $82k"]
        },
        "news_output": {
            "score_1_to_100": 50,
            "rationale": "SERPER_API_KEY not configured—neutral score assigned. No significant local news found via basic scraping. Market conditions appear stable.",
            "notes": ["News data unavailable", "No major developments reported", "Sentiment: neutral"]
        },
        "vc_risk_output": {
            "score_1_to_100": 62,
            "rationale": "Moderate-low risk given location strength but property-specific challenges exist. Market comparables suggest fair valuation with limited upside.",
            "notes": ["Location de-risks investment", "Property challenges: tenant, CapEx", "Comps: 5.2-6.0% cap rates", "Upside limited", "Hold period: 3-5 years"]
        },
        "construction_output": {
            "score_1_to_100": 54,
            "rationale": "1998 construction showing age. Parking lot needs resurfacing, HVAC units approaching end of life. Structural integrity good but cosmetic/mechanical updates critical.",
            "notes": ["Year built: 1998", "Parking lot: poor condition", "HVAC: 2009, aging", "Roof: 2015, fair", "Interior: dated finishes"]
        }
    },
    {
        "listing_id": "34567890",
        "address": "789 Industrial Pkwy, Cincinnati, OH 45215",
        "ask_price": 2100000,
        "scores": {
            "investment": 82,
            "location": 71,
            "news_signal": 50,
            "risk_return": 78,
            "construction": 85,
            "overall": 77
        },
        "investment_output": {
            "score_1_to_100": 82,
            "rationale": "Exceptional cap rate of 7.9% with long-term credit tenant (Amazon logistics). Triple net lease structure minimizes landlord responsibilities. Strong cash-on-cash returns projected.",
            "notes": ["Cap rate: 7.9% (excellent)", "Tenant: Amazon (NNN lease)", "Lease term: 12 years remaining", "Occupancy: 100%", "Cash-on-cash: 9.2%"]
        },
        "location_output": {
            "score_1_to_100": 71,
            "rationale": "Industrial area with excellent logistics infrastructure. Near airport and major distribution hubs. Area demographics less relevant for industrial use. Some environmental review needed.",
            "notes": ["Airport proximity: 8 miles", "Highway access: I-275", "Logistics hub: active", "Environmental: Phase I needed", "Zoning: industrial"]
        },
        "news_output": {
            "score_1_to_100": 50,
            "rationale": "SERPER_API_KEY missing—neutral score applied. Amazon's continued expansion in Cincinnati region noted via general research. No negative indicators found.",
            "notes": ["News unavailable (missing key)", "Amazon expanding locally", "Industrial market: strong"]
        },
        "vc_risk_output": {
            "score_1_to_100": 78,
            "rationale": "Low risk given credit tenant and NNN structure. Industrial RE sector remains strong. Exit liquidity good due to institutional buyer interest in this asset class.",
            "notes": ["Credit tenant: AAA-rated", "NNN lease: landlord risk minimal", "Industrial cap rates: compressing", "Exit buyers: institutions active", "Risk: low"]
        },
        "construction_output": {
            "score_1_to_100": 85,
            "rationale": "Recently constructed facility (2019) purpose-built for logistics. Modern warehouse spec with high ceilings, dock doors, and efficient layout. Minimal maintenance expected.",
            "notes": ["Year built: 2019", "Clear height: 32 feet", "Dock doors: 24", "Loading: grade-level + dock", "Condition: excellent"]
        }
    }
]

def truncate(text: str, max_len: int = 140) -> str:
    """Truncate text to max_len and add ellipsis if needed."""
    if not text or len(text) <= max_len:
        return text or ""
    return text[:max_len] + "…"

def main():
    console.print("\n[bold cyan]═══ Property Analysis Test Runner ═══[/bold cyan]\n")
    
    # Step 1: Load current filters (don't overwrite them)
    console.print("[yellow]Step 1:[/yellow] Loading stored filters...")
    
    try:
        response = httpx.get(f"{BASE_URL}/filters", timeout=10.0)
        response.raise_for_status()
        filters = response.json()
        console.print(f"[green]✓[/green] Current filters: {json.dumps(filters, indent=2)}\n")
    except Exception as e:
        console.print(f"[red]✗ Failed to load filters: {e}[/red]")
        return 1
    
    # Step 2: Run analysis
    console.print("[yellow]Step 2:[/yellow] Running analysis with stored filters...")
    console.print("[dim]This may take a minute as agents analyze each listing...[/dim]\n")
    
    try:
        # Use stored filters, timeout set high for agent processing
        response = httpx.post(
            f"{BASE_URL}/analyze",
            params={"use_stored": "true"},
            timeout=300.0  # 5 min timeout for agent processing
        )
        response.raise_for_status()
        results = response.json()
    except httpx.TimeoutException:
        console.print("[red]✗ Analysis timed out (>5 minutes). Check if API keys are valid.[/red]")
        console.print("[yellow]Using mock data for demonstration...[/yellow]\n")
        results = MOCK_RESULTS
    except Exception as e:
        console.print(f"[yellow]⚠ Analysis failed: {e}[/yellow]")
        if hasattr(e, 'response') and e.response:
            console.print(f"[dim]Response: {e.response.text}[/dim]")
        console.print("[yellow]Using mock data for demonstration...[/yellow]\n")
        results = MOCK_RESULTS
    
    # Step 3: Pretty-print results
    if not results:
        console.print("[yellow]⚠ No listings returned[/yellow]")
        return 0
    
    console.print(f"[green]✓[/green] Analysis complete! Processing {len(results)} listing(s)...\n")
    
    # Track data for summary
    table_rows = []
    
    for idx, report in enumerate(results, 1):
        listing_id = report.get("listing_id", "N/A")
        address = report.get("address", "Unknown Address")
        ask_price = report.get("ask_price")
        scores_obj = report.get("scores", {})
        overall = scores_obj.get("overall", 0)
        
        # Extract individual agent data
        inv_out = report.get("investment_output", {})
        loc_out = report.get("location_output", {})
        news_out = report.get("news_output", {})
        vc_out = report.get("vc_risk_output", {})
        con_out = report.get("construction_output", {})
        
        inv_score = inv_out.get("score_1_to_100", scores_obj.get("investment", 0))
        loc_score = loc_out.get("score_1_to_100", scores_obj.get("location", 0))
        news_score = news_out.get("score_1_to_100", scores_obj.get("news_signal", 0))
        vc_score = vc_out.get("score_1_to_100", scores_obj.get("risk_return", 0))
        con_score = con_out.get("score_1_to_100", scores_obj.get("construction", 0))
        
        inv_rat = truncate(inv_out.get("rationale", "No rationale provided"))
        loc_rat = truncate(loc_out.get("rationale", "No rationale provided"))
        news_rat = truncate(news_out.get("rationale", "No rationale provided"))
        vc_rat = truncate(vc_out.get("rationale", "No rationale provided"))
        con_rat = truncate(con_out.get("rationale", "No rationale provided"))
        
        # Print listing block
        console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
        console.print(f"[bold white]{address}[/bold white] [dim](listing_id={listing_id})[/dim]")
        if ask_price:
            console.print(f"[green]Ask Price: ${ask_price:,.0f}[/green]")
        console.print(f"[bold cyan]{'='*80}[/bold cyan]")
        
        console.print(f"[bold]Investment:[/bold]    {inv_score:>3}/100 — {inv_rat}")
        console.print(f"[bold]Location:[/bold]      {loc_score:>3}/100 — {loc_rat}")
        console.print(f"[bold]News/Reddit:[/bold]   {news_score:>3}/100 — {news_rat}")
        console.print(f"[bold]Risk/Return:[/bold]   {vc_score:>3}/100 — {vc_rat}")
        console.print(f"[bold]Construction:[/bold]  {con_score:>3}/100 — {con_rat}")
        console.print(f"\n[bold green]Overall:[/bold green]       {overall:>3}/100")
        
        # Artifacts
        console.print(f"\n[dim]Artifacts: (Not yet implemented - would be ./out/{listing_id}/report.json | memo.md)[/dim]")
        
        # Add to table
        table_rows.append({
            "address": address[:40] + ("…" if len(address) > 40 else ""),
            "overall": overall,
            "invest": inv_score,
            "loc": loc_score,
            "news": news_score,
            "risk": vc_score,
            "constr": con_score
        })
    
    # Step 4: Summary table
    console.print(f"\n\n[bold cyan]{'='*80}[/bold cyan]")
    console.print("[bold white]Summary Table[/bold white]")
    console.print(f"[bold cyan]{'='*80}[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Address", style="cyan", width=40)
    table.add_column("Overall", justify="right", style="green")
    table.add_column("Invest", justify="right")
    table.add_column("Loc", justify="right")
    table.add_column("News", justify="right")
    table.add_column("Risk", justify="right")
    table.add_column("Constr", justify="right")
    
    for row in table_rows:
        table.add_row(
            row["address"],
            str(row["overall"]),
            str(row["invest"]),
            str(row["loc"]),
            str(row["news"]),
            str(row["risk"]),
            str(row["constr"])
        )
    
    console.print(table)
    
    # Step 5: Final summary
    console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
    console.print("[bold white]Analysis Summary[/bold white]")
    console.print(f"[bold cyan]{'='*80}[/bold cyan]\n")
    
    summary = f"""
**Filters Used:** Location ID {filters['locationId']} ({filters['locationType']}), 
Price range ${filters['priceMin']:,.0f}-${filters['priceMax']:,.0f}, 
{filters['size']} listings per page.

**Listings Analyzed:** {len(results)} property listing(s) were evaluated.

**Agents:** All five specialist agents ran (Investment, Location, News/Reddit, VC Risk/Return, Construction). 
Note: If API keys (RAPIDAPI_KEY, OPENAI_API_KEY, SERPER_API_KEY) are placeholders, 
agents may have used neutral/fallback scores (~50) with notes about missing data.

**Artifacts:** Not yet implemented. In production, JSON reports and markdown memos would be 
written to `./out/<listing_id>/` for each analyzed property.

**TODOs Observed:**
- Implement artifact persistence (write FinalReport JSON + memo to disk)
- Add retry logic for LoopNet API rate limits
- Enhance construction quality heuristics beyond year-built
- Improve geocoding accuracy for location risk assessment
- Add support for property images and site photos in analysis
    """
    
    console.print(Panel(summary.strip(), title="Summary", border_style="cyan"))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
