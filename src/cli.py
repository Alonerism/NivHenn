"""CLI interface for real estate analysis."""
import argparse
import asyncio
import json
from pathlib import Path

from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from .app.config import settings
from .app.filters import load_filters, save_filters, load_city_name
from .app.models import SearchParams
from .app.loopnet_client import LoopNetClient, LoopNetAPIError
from .app.crew import PropertyAnalysisCrew


console = Console()

CLI_TO_MODEL_FIELD = {
    "location_id": "locationId",
    "location_type": "locationType",
    "page": "page",
    "size": "size",
    "price_min": "priceMin",
    "price_max": "priceMax",
    "building_size_min": "buildingSizeMin",
    "building_size_max": "buildingSizeMax",
    "property_type": "propertyType",
    "cap_rate_min": "capRateMin",
    "cap_rate_max": "capRateMax",
    "year_built_min": "yearBuiltMin",
    "year_built_max": "yearBuiltMax",
    "auctions": "auctions",
    "exclude_pending_sales": "excludePendingSales",
}


def create_results_table(reports: list) -> Table:
    """Create a Rich table for displaying results."""
    table = Table(title="Real Estate Analysis Results", show_header=True, header_style="bold magenta")
    
    table.add_column("Address", style="cyan", no_wrap=False, width=25)
    table.add_column("Ask Price", justify="right", style="green")
    table.add_column("Invest", justify="center", width=7)
    table.add_column("Location", justify="center", width=8)
    table.add_column("News", justify="center", width=6)
    table.add_column("VC Risk", justify="center", width=8)
    table.add_column("Constr.", justify="center", width=8)
    table.add_column("Overall", justify="center", style="bold yellow", width=7)
    
    for report in reports:
        address = report.address or "Unknown"
        price = f"${report.ask_price:,.0f}" if report.ask_price else "N/A"
        
        # Color code overall score
        overall = report.scores.overall
        if overall >= 75:
            overall_str = f"[bold green]{overall}[/bold green]"
        elif overall >= 60:
            overall_str = f"[yellow]{overall}[/yellow]"
        else:
            overall_str = f"[red]{overall}[/red]"
        
        table.add_row(
            address,
            price,
            str(report.scores.investment),
            str(report.scores.location),
            str(report.scores.news_signal),
            str(report.scores.risk_return),
            str(report.scores.construction),
            overall_str
        )
    
    return table


def save_reports(reports: list, output_dir: str = "./out"):
    """Save reports to JSON and Markdown files."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    for report in reports:
        # Save JSON
        json_file = out_path / f"listing_{report.listing_id}.json"
        with open(json_file, "w") as f:
            json.dump(report.model_dump(), f, indent=2)
        
        # Save Markdown memo
        md_file = out_path / f"listing_{report.listing_id}.md"
        with open(md_file, "w") as f:
            f.write(f"# Property Analysis: {report.address or report.listing_id}\n\n")
            f.write(f"**Ask Price:** ${report.ask_price:,.0f}\n\n" if report.ask_price else "**Ask Price:** N/A\n\n")
            f.write(f"**Overall Score:** {report.scores.overall}/100\n\n")
            f.write("---\n\n")
            f.write(report.memo_markdown)
        
        console.print(f"[green]✓[/green] Saved {json_file.name} and {md_file.name}")


async def analyze_command(args):
    """Execute the analyze command."""
    console.print("[bold cyan]Real Estate Scout - Property Analysis[/bold cyan]\n")
    
    # Validate API keys
    if not settings.rapidapi_key or settings.rapidapi_key == "__SET_ME__":
        console.print("[bold red]Error:[/bold red] RAPIDAPI_KEY not set in .env file")
        return
    
    if not settings.openai_api_key or settings.openai_api_key == "__SET_ME__":
        console.print("[bold red]Error:[/bold red] OPENAI_API_KEY not set in .env file")
        return
    
    # Build search parameters (stored or CLI)
    if args.use_stored:
        console.print("[bold]Using stored filters from config/filters.json[/bold]")
        search_params = load_filters()
        overrides = {}
        for cli_attr, field_name in CLI_TO_MODEL_FIELD.items():
            value = getattr(args, cli_attr, None)
            if value is None:
                continue
            overrides[field_name] = value
        if overrides:
            console.print("[italic]Applying CLI overrides to stored filters...[/italic]")
            merged = search_params.model_dump()
            merged.update(overrides)
            search_params = SearchParams(**merged)
    else:
        if not args.location_id:
            console.print("[bold red]Error:[/bold red] --location-id is required unless --use-stored is provided.")
            return
        payload = {
            "locationId": args.location_id,
            "locationType": args.location_type or "city",
        }
        for cli_attr, field_name in CLI_TO_MODEL_FIELD.items():
            if cli_attr in {"location_id", "location_type"}:
                continue
            value = getattr(args, cli_attr, None)
            if value is not None:
                payload[field_name] = value
        search_params = SearchParams(**payload)

    if args.persist_filters:
        save_filters(search_params)
        console.print("[green]✓ Saved filters to config/filters.json[/green]")

    city_name_hint = load_city_name() if args.use_stored else None

    def _has_numeric_location(value: str | None) -> bool:
        return value is not None and str(value).isdigit()

    city_name_for_request = city_name_hint

    if search_params.locationId and not _has_numeric_location(search_params.locationId):
        city_name_for_request = search_params.locationId
        search_params = search_params.model_copy(update={"locationId": None})
    elif not search_params.locationId and city_name_hint:
        city_name_for_request = city_name_hint

    console.print("[bold]Search Parameters:[/bold]")
    if search_params.locationId:
        console.print(f"  Location: {search_params.locationId} ({search_params.locationType})")
    elif city_name_for_request:
        console.print(f"  Location: {city_name_for_request} (city lookup)")
    else:
        console.print("  Location: Nationwide (no location filter)")
    price_min = search_params.priceMin
    price_max = search_params.priceMax
    if price_min is not None or price_max is not None:
        lo = f"${price_min:,.0f}" if price_min is not None else "Any"
        hi = f"${price_max:,.0f}" if price_max is not None else "Any"
        console.print(f"  Price Range: {lo} - {hi}")
    else:
        console.print("  Price Range: Any")
    console.print(f"  Results: {search_params.size} listings\n")
    
    # Fetch listings
    console.print("[bold]Step 1:[/bold] Fetching listings from LoopNet...")
    client = LoopNetClient()
    
    try:
        listings = await client.search_properties(search_params, city_name=city_name_for_request)
    except LoopNetAPIError as exc:
        message = str(exc)
        if "No data found" in message:
            console.print(
                "[yellow]No listings matched the current filters. "
                "Loosen price, cap rate, or size filters, or supply a specific city.[/yellow]"
            )
            return
        console.print(f"[bold red]LoopNet error:[/bold red] {message}")
        return
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        return

    if not listings:
        console.print(
            "[yellow]LoopNet returned zero listings. Consider broadening your filters or adding a location.[/yellow]"
        )
        return

    console.print(f"[green]✓[/green] Found {len(listings)} listings\n")
    
    if not listings:
        console.print("[yellow]No listings found. Try adjusting your search parameters.[/yellow]")
        return
    
    # Analyze each listing
    console.print("[bold]Step 2:[/bold] Running multi-agent analysis...\n")
    crew = PropertyAnalysisCrew()
    reports = []
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Analyzing properties...", total=len(listings))
        
        for listing in listings:
            try:
                report = await crew.analyze_listing(listing)
                reports.append(report)
                progress.update(task, advance=1)
            except Exception as e:
                console.print(f"[red]Error analyzing {listing.listing_id}:[/red] {e}")
                progress.update(task, advance=1)
    
    console.print(f"\n[green]✓[/green] Analysis complete!\n")
    
    # Display results table
    if reports:
        table = create_results_table(reports)
        console.print(table)
        console.print()
        
        # Save reports
        console.print("[bold]Step 3:[/bold] Saving reports...")
        save_reports(reports, args.output_dir)
        console.print(f"\n[bold green]✓ All done![/bold green] Reports saved to {args.output_dir}/")
    else:
        console.print("[yellow]No reports generated.[/yellow]")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Real Estate Scout - LoopNet + Multi-Agent Analysis")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze properties")
    analyze_parser.add_argument("--location-id", help="LoopNet location ID")
    analyze_parser.add_argument("--location-type", help="Location type (city, state, zipcode)")
    analyze_parser.add_argument("--page", type=int, help="Page number")
    analyze_parser.add_argument("--size", type=int, help="Results per page")
    analyze_parser.add_argument("--price-min", type=float, help="Minimum price")
    analyze_parser.add_argument("--price-max", type=float, help="Maximum price")
    analyze_parser.add_argument("--building-size-min", type=float, help="Minimum building size (SF)")
    analyze_parser.add_argument("--building-size-max", type=float, help="Maximum building size (SF)")
    analyze_parser.add_argument("--property-type", help="Property type filter")
    analyze_parser.add_argument("--use-stored", action="store_true", help="Use filters from config/filters.json (CLI values override when provided)")
    analyze_parser.add_argument("--persist-filters", action="store_true", help="Persist the effective filters back to config/filters.json")
    analyze_parser.add_argument("--output-dir", default="./out", help="Output directory for reports")
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        asyncio.run(analyze_command(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
