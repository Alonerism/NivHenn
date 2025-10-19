#!/usr/bin/env python3
"""
Interactive Property Analyzer
Allows user to select listings and agents before running expensive AI analysis.
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()
BASE_URL = "http://127.0.0.1:8000"


def format_price(price: Optional[float]) -> str:
    """Format price for display."""
    if price is None:
        return "N/A"
    if price >= 1_000_000:
        return f"${price/1_000_000:.2f}M"
    return f"${price:,.0f}"


def build_loopnet_url(listing) -> str:
    """Build LoopNet URL from listing data."""
    listing_id = listing.listing_id
    
    # Try to build pretty URL with address
    if listing.address and listing.city and listing.state:
        street = listing.address.replace(' ', '-').replace(',', '')
        city_state = f"{listing.city}-{listing.state}".replace(' ', '-').replace(',', '')
        return f"https://www.loopnet.com/Listing/{street}-{city_state}/{listing_id}/"
    
    # Fallback to simple URL
    return f"https://www.loopnet.com/Listing/{listing_id}/"


async def fetch_listings():
    """Fetch listings without running AI analysis."""
    console.print("\n[bold cyan]Step 1: Fetching listings from LoopNet...[/bold cyan]")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get current filters
        response = await client.get(f"{BASE_URL}/filters")
        filters = response.json()
        
        console.print(f"[dim]Using filters from config/filters.json[/dim]")
        
        # Load cityName directly from filters.json (not from API response)
        from src.app.filters import load_city_name
        city_name = load_city_name()
        
        if city_name:
            console.print(f"[dim]City: {city_name}[/dim]")
        
        # Fetch listings via our LoopNet client directly
        from src.app.loopnet_client import LoopNetClient
        from src.app.models import SearchParams
        
        # Build params, excluding cityName
        params_dict = {k: v for k, v in filters.items() if v is not None}
        
        # If no locationId but we have cityName, set a dummy one (will be overridden)
        if "locationId" not in params_dict and city_name:
            params_dict["locationId"] = "00000"  # Dummy ID, will be replaced by city_name
            console.print(f"[dim]Set dummy locationId since cityName is present[/dim]")
        
        console.print(f"[dim]Calling search with city_name={city_name}[/dim]")
        params = SearchParams(**params_dict)
        
        client_ln = LoopNetClient()
        listings = await client_ln.search_properties(params, city_name=city_name)
        
        return listings


def display_listings(listings):
    """Display listings in a nice table."""
    console.print("\n[bold green]✓ Found listings:[/bold green]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Address", style="cyan")
    table.add_column("Price", justify="right", style="green")
    table.add_column("Cap Rate", justify="right")
    table.add_column("Units", justify="right")
    table.add_column("Size (SF)", justify="right")
    table.add_column("Listing ID", style="dim")
    
    for idx, listing in enumerate(listings, 1):
        cap_rate = f"{listing.cap_rate:.2f}%" if listing.cap_rate else "N/A"
        units = str(listing.units) if listing.units else "N/A"
        size = f"{listing.building_size:,.0f}" if listing.building_size else "N/A"
        
        table.add_row(
            str(idx),
            listing.address or "No address",
            format_price(listing.ask_price),
            cap_rate,
            units,
            size,
            listing.listing_id
        )
    
    console.print(table)


def select_listings(listings):
    """Ask user which listings to analyze."""
    console.print("\n[bold cyan]Step 2: Select listings to analyze[/bold cyan]")
    console.print("[dim]Enter listing numbers separated by commas (e.g., 1,3,4) or 'all'[/dim]")
    
    while True:
        selection = Prompt.ask("Which listings do you want to analyze?", default="all")
        
        if selection.lower() == "all":
            return list(range(len(listings)))
        
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(",")]
            # Validate indices
            if all(0 <= idx < len(listings) for idx in indices):
                return indices
            else:
                console.print("[red]Invalid listing numbers. Please try again.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter numbers separated by commas.[/red]")


def select_agents_for_listing(listing, listing_num):
    """Ask user which agents to run for a specific listing."""
    console.print(f"\n[bold cyan]Step 3.{listing_num}: Select agents for {listing.address}[/bold cyan]")
    console.print("[dim]Available agents:[/dim]")
    console.print("  1. Investment Agent (Financial analysis)")
    console.print("  2. Location Risk Agent (Area analysis)")
    console.print("  3. News/Reddit Agent (Market sentiment)")
    console.print("  4. VC Risk/Return Agent (Risk assessment)")
    console.print("  5. Construction Agent (Physical condition)")
    console.print("\n[dim]Enter agent numbers separated by commas (e.g., 1,2,5) or 'all'[/dim]")
    
    agent_names = {
        1: "investment",
        2: "location",
        3: "news",
        4: "vc_risk",
        5: "construction"
    }
    
    while True:
        selection = Prompt.ask("Which agents?", default="all")
        
        if selection.lower() == "all":
            return list(agent_names.values())
        
        try:
            indices = [int(x.strip()) for x in selection.split(",")]
            if all(1 <= idx <= 5 for idx in indices):
                return [agent_names[idx] for idx in indices]
            else:
                console.print("[red]Invalid agent numbers (1-5 only). Please try again.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter numbers separated by commas.[/red]")


def get_next_run_number(outputs_dir: Path) -> int:
    """Get the next run number by checking existing run directories."""
    if not outputs_dir.exists():
        return 1
    
    existing_runs = [d.name for d in outputs_dir.iterdir() if d.is_dir() and d.name.startswith("run")]
    if not existing_runs:
        return 1
    
    # Extract numbers from run directories (e.g., "run1" -> 1)
    run_numbers = []
    for run_dir in existing_runs:
        try:
            num = int(run_dir.replace("run", ""))
            run_numbers.append(num)
        except ValueError:
            continue
    
    return max(run_numbers) + 1 if run_numbers else 1


async def analyze_listing_with_agents(listing, enabled_agents, run_dir: Path):
    """Run analysis on a single listing with selected agents."""
    from src.app.crew import PropertyAnalysisCrew
    
    console.print(f"\n[yellow]⏳ Analyzing {listing.address}...[/yellow]")
    console.print(f"[dim]Enabled agents: {', '.join(enabled_agents)}[/dim]")
    
    crew = PropertyAnalysisCrew()
    
    # TODO: Modify crew to accept enabled_agents parameter
    # For now, run full analysis
    report = await crew.analyze_listing(listing)
    
    # Save report to run directory
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    json_path = run_dir / f"{report.listing_id}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))
    
    # Save human-readable markdown
    md_path = run_dir / f"{report.listing_id}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Property Analysis: {report.address}\n\n")
        f.write(f"**Listing ID:** {report.listing_id}\n")
        f.write(f"**Price:** {format_price(report.ask_price)}\n")
        f.write(f"**Overall Score:** {report.scores.overall}/100\n\n")
        f.write("---\n\n")
        
        # Investment Agent
        if report.investment_output and "investment" in enabled_agents:
            f.write(f"## 💰 Investment Agent (Score: {report.scores.investment}/100)\n\n")
            f.write(f"**Rationale:** {report.investment_output.rationale}\n\n")
            f.write("**Key Notes:**\n")
            for note in report.investment_output.notes:
                f.write(f"- {note}\n")
            f.write("\n---\n\n")
        
        # Location Agent
        if report.location_output and "location" in enabled_agents:
            f.write(f"## 📍 Location Risk Agent (Score: {report.scores.location}/100)\n\n")
            f.write(f"**Rationale:** {report.location_output.rationale}\n\n")
            f.write("**Key Notes:**\n")
            for note in report.location_output.notes:
                f.write(f"- {note}\n")
            f.write("\n---\n\n")
        
        # News Agent
        if report.news_output and "news" in enabled_agents:
            f.write(f"## 📰 News/Reddit Agent (Score: {report.scores.news_signal}/100)\n\n")
            f.write(f"**Rationale:** {report.news_output.rationale}\n\n")
            f.write("**Key Notes:**\n")
            for note in report.news_output.notes:
                f.write(f"- {note}\n")
            f.write("\n---\n\n")
        
        # VC Risk Agent
        if report.vc_risk_output and "vc_risk" in enabled_agents:
            f.write(f"## 📊 VC Risk/Return Agent (Score: {report.scores.risk_return}/100)\n\n")
            f.write(f"**Rationale:** {report.vc_risk_output.rationale}\n\n")
            f.write("**Key Notes:**\n")
            for note in report.vc_risk_output.notes:
                f.write(f"- {note}\n")
            f.write("\n---\n\n")
        
        # Construction Agent
        if report.construction_output and "construction" in enabled_agents:
            f.write(f"## 🏗️ Construction Agent (Score: {report.scores.construction}/100)\n\n")
            f.write(f"**Rationale:** {report.construction_output.rationale}\n\n")
            f.write("**Key Notes:**\n")
            for note in report.construction_output.notes:
                f.write(f"- {note}\n")
            f.write("\n---\n\n")
        
        # Consolidated Memo
        f.write("## 📝 Investment Memo\n\n")
        f.write(report.memo_markdown)
    
    # Generate HTML report for easy viewing
    from src.app.html_report import generate_html_report
    html_path = run_dir / f"{report.listing_id}.html"
    generate_html_report(report, listing, html_path)
    
    console.print(f"[green]✓ Analysis complete for {listing.address}[/green]")
    console.print(f"[dim]  JSON: {json_path}[/dim]")
    console.print(f"[dim]  Markdown: {md_path}[/dim]")
    console.print(f"[dim]  HTML: {html_path}[/dim]")
    
    return report


async def main():
    """Main interactive flow."""
    console.print(Panel.fit(
        "[bold cyan]Interactive Property Analyzer[/bold cyan]\n"
        "[dim]Select listings and agents before running AI analysis[/dim]",
        border_style="cyan"
    ))
    
    try:
        # Step 1: Fetch listings
        listings = await fetch_listings()
        
        if not listings:
            console.print("[red]No listings found. Check your filters in config/filters.json[/red]")
            return 1
        
        # Display listings
        display_listings(listings)
        
        # Step 2: Select listings
        selected_indices = select_listings(listings)
        selected_listings = [listings[i] for i in selected_indices]
        
        console.print(f"\n[green]✓ Selected {len(selected_listings)} listing(s) for analysis[/green]")
        
        # Step 3: Select agents for each listing
        analysis_plan = []
        for idx, listing in enumerate(selected_listings, 1):
            agents = select_agents_for_listing(listing, idx)
            analysis_plan.append((listing, agents))
        
        # Confirm before running
        console.print("\n[bold yellow]Analysis Plan:[/bold yellow]")
        for listing, agents in analysis_plan:
            console.print(f"  • {listing.address} → {', '.join(agents)}")
        
        if not Confirm.ask("\nProceed with analysis?", default=True):
            console.print("[yellow]Analysis cancelled.[/yellow]")
            return 0
        
        # Prepare run directory
        outputs_dir = Path.cwd() / "outputs"
        run_number = get_next_run_number(outputs_dir)
        run_dir = outputs_dir / f"run{run_number}"
        
        console.print(f"\n[dim]Saving to: {run_dir}[/dim]")
        
        # Step 4: Run analysis
        console.print("\n[bold cyan]Step 4: Running AI agent analysis...[/bold cyan]")
        reports = []
        
        for listing, agents in analysis_plan:
            report = await analyze_listing_with_agents(listing, agents, run_dir)
            reports.append((report, listing))  # Keep original listing for extra data
        
        # Step 5: Summary
        console.print("\n[bold green]✓ Analysis Complete![/bold green]\n")
        
        summary_table = Table(
            show_header=True, 
            header_style="bold magenta", 
            title=f"📊 Analysis Summary - Run #{run_number}",
            title_style="bold cyan"
        )
        summary_table.add_column("Address", style="cyan", width=22, no_wrap=True)
        summary_table.add_column("Price", justify="right", style="green", width=10)
        summary_table.add_column("Cap%", justify="right", width=7)
        summary_table.add_column("Units", justify="right", width=6)
        summary_table.add_column("SF", justify="right", width=9)
        summary_table.add_column("Score", justify="center", style="yellow", width=8)
        
        for report, listing in reports:
            cap_rate = f"{listing.cap_rate:.1f}%" if listing.cap_rate else "N/A"
            units = str(listing.units) if listing.units else "N/A"
            size = f"{listing.building_size:,.0f}" if listing.building_size else "N/A"
            
            summary_table.add_row(
                report.address or "N/A",
                format_price(listing.ask_price),
                cap_rate,
                units,
                size,
                f"{report.scores.overall}/100"
            )
        
        console.print(summary_table)
        
        # Print URLs separately for better readability
        console.print("\n[bold cyan]🔗 Property Links:[/bold cyan]")
        for report, listing in reports:
            loopnet_url = build_loopnet_url(listing)
            console.print(f"  • [cyan]{report.address}[/cyan]: [blue underline]{loopnet_url}[/blue underline]")
        
        console.print(f"\n[dim]📁 Reports saved to: {run_dir}[/dim]")
        console.print(f"[dim]📋 Files created: {len(reports)} × (JSON + Markdown)[/dim]")
        
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
