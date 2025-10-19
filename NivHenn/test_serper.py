#!/usr/bin/env python3
"""
Serper News Testing Tool
Test what news/sentiment data the Serper agent is finding for a property.
"""
import asyncio
import json
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from src.app.serper_news import search_news
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def test_serper_for_address(address: str, city: str, state: str):
    """Test Serper news search for a specific property."""
    
    console.print(Panel.fit(
        f"[bold cyan]Serper News Test[/bold cyan]\n"
        f"[dim]Testing news/sentiment for: {address}, {city}, {state}[/dim]",
        border_style="cyan"
    ))
    
    # Check API key
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        console.print("[red]✗ SERPER_API_KEY not set in environment![/red]")
        console.print("[yellow]Set it with: export SERPER_API_KEY='your-key'[/yellow]")
        return
    
    console.print(f"[green]✓ API Key found: {api_key[:10]}...[/green]\n")
    
    # Test 1: Property-specific news
    console.print("\n[bold yellow]1️⃣  Property-Specific News Search[/bold yellow]")
    query1 = f"{address} {city} {state}"
    console.print(f"[dim]Query: '{query1}'[/dim]\n")
    
    try:
        result1 = search_news(query1, num=5)
        
        if result1.get("note"):
            console.print(f"[yellow]⚠ {result1['note']}[/yellow]")
        
        items1 = result1.get("items", [])
        
        if items1:
            table = Table(show_header=True, header_style="bold magenta", show_lines=True)
            table.add_column("#", style="dim", width=3)
            table.add_column("Title", style="cyan", width=50)
            table.add_column("Source", style="green", width=20)
            table.add_column("Date", style="yellow", width=12)
            
            for idx, item in enumerate(items1, 1):
                table.add_row(
                    str(idx),
                    item.get("title", "N/A")[:50],
                    item.get("source", "N/A"),
                    item.get("date", "N/A")
                )
            
            console.print(table)
            console.print(f"\n[green]✓ Found {len(items1)} property-specific results[/green]")
            
            # Show full snippet of first result
            if items1[0].get("snippet"):
                console.print("\n[bold]First Result Snippet:[/bold]")
                console.print(Panel(items1[0]["snippet"], border_style="dim"))
        else:
            console.print("[yellow]⚠ No property-specific news found[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    
    # Test 2: Neighborhood news
    console.print("\n[bold yellow]2️⃣  Neighborhood News Search[/bold yellow]")
    query2 = f"{city} {state} real estate development"
    console.print(f"[dim]Query: '{query2}'[/dim]\n")
    
    try:
        result2 = search_news(query2, num=5)
        items2 = result2.get("items", [])
        
        if items2:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim", width=3)
            table.add_column("Title", style="cyan", width=60)
            table.add_column("Source", style="green", width=20)
            
            for idx, item in enumerate(items2, 1):
                table.add_row(
                    str(idx),
                    item.get("title", "N/A"),
                    item.get("source", "N/A")
                )
            
            console.print(table)
            console.print(f"\n[green]✓ Found {len(items2)} neighborhood results[/green]")
        else:
            console.print("[yellow]⚠ No neighborhood news found[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
    
    # Test 3: Market sentiment
    console.print("\n[bold yellow]3️⃣  Market Sentiment Search[/bold yellow]")
    query3 = f"{city} {state} housing market 2025"
    console.print(f"[dim]Query: '{query3}'[/dim]\n")
    
    try:
        result3 = search_news(query3, num=5)
        items3 = result3.get("items", [])
        
        if items3:
            console.print("[green]✓ Found market sentiment articles:[/green]\n")
            for idx, item in enumerate(items3[:3], 1):
                console.print(f"[bold cyan]{idx}. {item.get('title', 'N/A')}[/bold cyan]")
                console.print(f"   [dim]{item.get('snippet', 'No snippet')[:150]}...[/dim]\n")
        else:
            console.print("[yellow]⚠ No market sentiment found[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
    
    # Show what agent would receive
    console.print("\n[bold yellow]4️⃣  Formatted Output (What Agent Receives)[/bold yellow]\n")
    
    all_items = result1.get("items", [])[:3] + result2.get("items", [])[:2]
    
    if all_items:
        formatted = "Recent news and market signals:\n\n"
        for item in all_items:
            formatted += f"• {item.get('title', 'N/A')}\n"
            formatted += f"  Source: {item.get('source', 'N/A')} | Date: {item.get('date', 'N/A')}\n"
            if item.get("snippet"):
                formatted += f"  {item.get('snippet', '')[:200]}...\n"
            formatted += "\n"
        
        console.print(Panel(formatted, title="📰 Agent Input", border_style="blue"))
        console.print(f"\n[green]✓ Agent receives {len(formatted)} characters of news context[/green]")
    else:
        console.print("[yellow]⚠ No formatted news available[/yellow]")


def test_from_filters():
    """Test using current filters from config."""
    from src.app.filters import load_city_name, load_filters
    from src.app.loopnet_client import LoopNetClient
    from src.app.models import SearchParams
    
    city_name = load_city_name()
    if not city_name:
        console.print("[red]No city name found in config/filters.json[/red]")
        return
    
    # Fetch a sample listing
    filters_dict = load_filters()  # This returns a dict
    params_dict = {k: v for k, v in filters_dict.items() if v is not None}
    
    # Add dummy locationId if not present
    if "locationId" not in params_dict:
        params_dict["locationId"] = "00000"
    
    params = SearchParams(**params_dict)
    
    console.print(f"[dim]Fetching sample listing from {city_name}...[/dim]\n")
    
    client = LoopNetClient()
    listings = asyncio.run(client.search_properties(params, city_name=city_name))
    
    if not listings:
        console.print("[red]No listings found to test[/red]")
        return
    
    # Test first listing
    listing = listings[0]
    console.print(f"\n[bold green]Testing with listing:[/bold green] {listing.address}")
    console.print(f"[dim]Price: ${listing.ask_price:,.0f} | Cap Rate: {listing.cap_rate:.1f}%[/dim]\n")
    
    test_serper_for_address(
        listing.address or "",
        listing.city or city_name,
        listing.state or "CA"
    )


def main():
    """Main entry point."""
    
    if len(sys.argv) > 1:
        # Manual address provided
        if len(sys.argv) < 4:
            console.print("[red]Usage: python test_serper.py <address> <city> <state>[/red]")
            console.print("[yellow]Or run without args to test with current filters[/yellow]")
            return 1
        
        address = sys.argv[1]
        city = sys.argv[2]
        state = sys.argv[3]
        
        test_serper_for_address(address, city, state)
    else:
        # Use current filters
        test_from_filters()
    
    console.print("\n[bold green]✓ Serper test complete![/bold green]\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

