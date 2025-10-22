#!/usr/bin/env python3
"""
Interactive Property Analyzer
Allows user to select listings and agents before running expensive AI analysis.
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional


def ensure_project_python() -> None:
    """Re-exec into the project virtual environment if available."""

    flag = "INTERACTIVE_ANALYZER_REEXEC"

    # If we're already running inside the managed interpreter, clear the flag and continue.
    if os.environ.get(flag) == "1":
        os.environ.pop(flag, None)
        return

    project_root = Path(__file__).resolve().parent
    candidates: list[Path] = []

    # POSIX virtualenv locations
    candidates.append(project_root / ".venv" / "bin" / "python")
    candidates.append(project_root / "venv" / "bin" / "python")

    # Windows virtualenv locations
    candidates.append(project_root / ".venv" / "Scripts" / "python.exe")
    candidates.append(project_root / "venv" / "Scripts" / "python.exe")

    target = next((candidate for candidate in candidates if candidate.exists()), None)
    if not target:
        return

    try:
        current = Path(sys.executable).resolve()
    except FileNotFoundError:
        current = Path(sys.executable)

    if current == target.resolve():
        return

    env = os.environ.copy()
    env[flag] = "1"
    os.execve(str(target), [str(target), *sys.argv], env)


ensure_project_python()

import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TimeElapsedColumn,
    TextColumn,
)

console = Console()
BASE_URL = "http://127.0.0.1:8000"

AGENT_LABELS = {
    "investment": ("💰", "Investment Agent"),
    "location": ("📍", "Location Risk Agent"),
    "news": ("📰", "News/Reddit Agent"),
    "vc_risk": ("📊", "VC Risk/Return Agent"),
    "construction": ("🏗️", "Construction Agent"),
    "la_city": ("🏛️", "LA City Data Agent"),
}


LA_DATASET_LABELS = {
    "permits": "Building Permits",
    "inspections": "Inspections",
    "coo": "Certificates of Occupancy",
    "code_open": "Open Code Violations",
    "code_closed": "Closed Code Violations",
}


def display_la_city_summary(records: dict[str, Any]) -> None:
    """Render an overview of LA City Socrata records in the console."""

    results = records.get("results") or {}
    counts = (records.get("meta") or {}).get("counts") or {}
    errors = records.get("errors") or {}

    if not results and not counts and not errors:
        console.print("[dim]No LA city datasets returned for this listing.[/dim]")
        return

    table = Table(
        show_header=True,
        header_style="bold magenta",
        title="🏛️ LA City Records",
        title_style="bold cyan",
    )
    table.add_column("Dataset", style="cyan", no_wrap=True)
    table.add_column("Records", justify="right", style="yellow")
    table.add_column("Sample Fields", style="green")

    for key, label in LA_DATASET_LABELS.items():
        rows = results.get(key) or []
        count = counts.get(key, len(rows))

        if rows:
            sample_item = rows[0]
            preview_parts = []
            for field, value in list(sample_item.items())[:3]:
                preview_parts.append(f"{field}={value}")
            preview = ", ".join(preview_parts)
        elif key in errors:
            preview = f"Error: {errors[key]}"
        else:
            preview = "(no matches)"

        table.add_row(label, str(count), preview)

    console.print("\n[bold cyan]📂 LA City records snapshot[/bold cyan]")
    console.print(table)

    if errors:
        error_lines = "\n".join(f"• {LA_DATASET_LABELS.get(k, k)}: {v}" for k, v in errors.items())
        console.print(
            Panel(
                f"[yellow]Partial data returned.[/yellow]\n{error_lines}",
                title="Socrata warnings",
                border_style="yellow",
            )
        )


from src.app.models import FinalReport, Listing
from src.app.crew import PropertyAnalysisCrew


def format_price(price: Optional[float]) -> str:
    """Format price for display."""
    if price is None:
        return "N/A"
    if price >= 1_000_000:
        return f"${price/1_000_000:.2f}M"
    return f"${price:,.0f}"


def format_price_per_unit(price: Optional[float], units: Optional[int]) -> str:
    """Format price per unit."""
    if price is None or not units:
        return "N/A"
    return f"${price/units:,.0f}/unit"


def format_price_per_sf(price: Optional[float], size: Optional[float]) -> str:
    """Format price per square foot."""
    if price is None or not size:
        return "N/A"
    return f"${price/size:,.0f}/SF"


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

    from src.app.filters import load_filters, load_city_name
    from src.app.loopnet_client import LoopNetClient, LoopNetAPIError
    from src.app.models import SearchParams

    filters_dict: dict[str, object]
    city_name = load_city_name()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BASE_URL}/filters")
            response.raise_for_status()
            payload = response.json()
            filters_dict = {k: v for k, v in payload.items() if k != "cityName"}
            city_name = city_name or payload.get("cityName")
            console.print("[dim]Loaded filters from running API server[/dim]")
    except (httpx.HTTPError, OSError):
        stored = load_filters()
        filters_dict = stored.model_dump(exclude_none=True)
        console.print("[dim]API server not reachable; using stored filters locally[/dim]")

    if city_name:
        console.print(f"[dim]City: {city_name}[/dim]")

    params = SearchParams(**filters_dict)

    def _has_numeric_location(value: str | None) -> bool:
        return value is not None and str(value).isdigit()

    city_for_request = city_name

    if params.locationId and not _has_numeric_location(params.locationId):
        city_for_request = params.locationId
        params = params.model_copy(update={"locationId": None})

    if params.locationId:
        console.print(f"[dim]Using locationId {params.locationId} ({params.locationType})[/dim]")
    elif city_for_request:
        console.print(f"[dim]Calling search with city_name={city_for_request}[/dim]")
    else:
        console.print("[dim]No location supplied; running nationwide search[/dim]")

    client_ln = LoopNetClient()
    try:
        listings = await client_ln.search_properties(params, city_name=city_for_request)
    except LoopNetAPIError as exc:
        message = str(exc)
        if "No data found" in message:
            console.print(
                "[yellow]No listings matched the current filters. "
                "Try loosening price, cap rate, or size constraints, or add a location filter.[/yellow]"
            )
            return []
        console.print(f"[bold red]LoopNet error:[/bold red] {message}")
        return []

    if not listings:
        console.print(
            "[yellow]LoopNet returned zero listings. Adjust your filters or add a city to broaden results.[/yellow]"
        )

    return listings


def display_listings(listings):
    """Display listings in a nice table."""
    console.print("\n[bold green]✓ Found listings:[/bold green]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Address", style="cyan")
    table.add_column("State", style="cyan", width=6)
    table.add_column("Price", justify="right", style="green")
    table.add_column("Cap Rate", justify="right")
    table.add_column("Units", justify="right")
    table.add_column("Size (SF)", justify="right")
    table.add_column("Price Ratios", justify="left", width=16)
    
    for idx, listing in enumerate(listings, 1):
        cap_rate = f"{listing.cap_rate:.2f}%" if listing.cap_rate else "N/A"
        units = str(listing.units) if listing.units else "N/A"
        size = f"{listing.building_size:,.0f}" if listing.building_size else "N/A"
        per_unit = format_price_per_unit(listing.ask_price, listing.units)
        per_sf = format_price_per_sf(listing.ask_price, listing.building_size)
        ratios = f"{per_unit}\n{per_sf}"
        
        table.add_row(
            str(idx),
            listing.address or "No address",
            listing.state or "N/A",
            format_price(listing.ask_price),
            cap_rate,
            units,
            size,
            ratios,
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
    console.print("  6. LA City Data Agent (Permits & violations)")
    console.print("\n[dim]Enter agent numbers separated by commas (e.g., 1,2,5) or 'all'[/dim]")
    
    agent_names = {
        1: "investment",
        2: "location",
        3: "news",
        4: "vc_risk",
        5: "construction",
        6: "la_city",
    }
    
    while True:
        selection = Prompt.ask("Which agents?", default="all")
        
        if selection.lower() == "all":
            return list(agent_names.values())
        
        try:
            indices = [int(x.strip()) for x in selection.split(",")]
            if all(1 <= idx <= 6 for idx in indices):
                return [agent_names[idx] for idx in indices]
            else:
                console.print("[red]Invalid agent numbers (1-6 only). Please try again.[/red]")
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


async def analyze_listing_with_agents(
    crew,
    listing,
    enabled_agents,
    run_dir: Path,
) -> tuple[FinalReport, Optional[dict[str, Any]]]:
    """Run analysis on a single listing with selected agents."""
    enabled_set = set(enabled_agents)
    la_city_enabled = "la_city" in enabled_set

    console.print(f"\n[yellow]⏳ Analyzing {listing.address}...[/yellow]")
    console.print(f"[dim]Enabled agents: {', '.join(enabled_agents)}[/dim]")

    specialist_result = await crew.run_specialists(listing, enabled_set)
    la_city_records = specialist_result.la_city_records

    if la_city_enabled and la_city_records:
        display_la_city_summary(la_city_records)
    elif la_city_enabled:
        console.print("[yellow]LA City Data Agent did not return any records for this listing.[/yellow]")

    # Display specialist summaries before aggregator
    console.print("\n[bold cyan]Specialist agent summaries:[/bold cyan]")
    for agent_key in enabled_agents:
        output = specialist_result.outputs.get(agent_key)
        if not output:
            continue
        emoji, title = AGENT_LABELS.get(agent_key, ("🤖", agent_key.title()))
        notes_preview = "\n".join(f"- {note}" for note in output.notes[:3]) or "- No notes provided"
        console.print(
            Panel(
                f"[green]Score:[/green] {output.score_1_to_100}/100\n"
                f"[cyan]Rationale:[/cyan] {output.rationale}\n"
                f"[dim]Key Notes:[/dim]\n{notes_preview}",
                title=f"{emoji} {title}",
                border_style="cyan",
            )
        )

    # Generate final report (aggregator stage)
    report = await crew.build_final_report(listing, specialist_result)

    # Save report to run directory
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    json_path = run_dir / f"{report.listing_id}.json"
    payload = report.model_dump()
    if la_city_records is not None:
        payload["la_city_records"] = la_city_records

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    
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
        
        if la_city_records is not None:
            counts = (la_city_records.get("meta") or {}).get("counts") or {}
            errors = la_city_records.get("errors") or {}

            f.write("## 🏛️ LA City Records\n\n")
            f.write("| Dataset | Records |\n")
            f.write("| --- | ---: |\n")
            for key, label in LA_DATASET_LABELS.items():
                count = counts.get(key, 0)
                f.write(f"| {label} | {count} |\n")

            if errors:
                f.write("\n**Warnings:**\n")
                for key, message in errors.items():
                    label = LA_DATASET_LABELS.get(key, key)
                    f.write(f"- {label}: {message}\n")
                f.write("\n")

        # Consolidated Memo
        f.write("## 📝 Investment Memo\n\n")
        f.write(report.memo_markdown)
    
    # Generate HTML report for easy viewing
    from src.app.html_report import generate_html_report
    html_path = run_dir / f"{report.listing_id}.html"
    generate_html_report(report, listing, html_path)

    la_json_path: Optional[Path] = None
    if la_city_records is not None:
        la_json_path = run_dir / f"{report.listing_id}_la_city.json"
        with open(la_json_path, "w", encoding="utf-8") as f:
            json.dump(la_city_records, f, indent=2)
    
    console.print(f"[green]✓ Analysis complete for {listing.address}[/green]")
    console.print(f"[dim]  JSON: {json_path}[/dim]")
    console.print(f"[dim]  Markdown: {md_path}[/dim]")
    console.print(f"[dim]  HTML: {html_path}[/dim]")
    if la_json_path:
        console.print(f"[dim]  LA data: {la_json_path}[/dim]")
    
    return report, la_city_records


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
            return 0
        
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
        reports: list[tuple[FinalReport, Listing, list[str], Optional[dict[str, Any]]]] = []
        crew = PropertyAnalysisCrew()

        with Progress(
            SpinnerColumn(),
            BarColumn(),
            TextColumn("{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task("Analyzing listings...", total=len(analysis_plan))

            for idx, (listing, agents) in enumerate(analysis_plan, 1):
                progress.console.print(
                    f"\n[bold]Listing {idx} of {len(analysis_plan)}:[/bold] {listing.address or listing.listing_id}"
                )
                report, la_city_records = await analyze_listing_with_agents(
                    crew, listing, agents, run_dir
                )
                reports.append((report, listing, agents, la_city_records))
                progress.update(task_id, advance=1)
        
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
        
        for report, listing, _agents, _la_data in reports:
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
        for report, listing, _agents, _la_data in reports:
            loopnet_url = build_loopnet_url(listing)
            console.print(f"  • [cyan]{report.address}[/cyan]: [blue underline]{loopnet_url}[/blue underline]")
        
        console.print(f"\n[dim]📁 Reports saved to: {run_dir}[/dim]")
        any_la_records = any(la_data for *_rest, la_data in reports)
        file_summary = "JSON + Markdown + HTML"
        if any_la_records:
            file_summary += " + LA data"
        console.print(f"[dim]📋 Files created: {len(reports)} × ({file_summary})[/dim]")
        
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
