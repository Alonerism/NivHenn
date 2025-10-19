#!/usr/bin/env python3
"""Simple test to show listing selection works"""
import asyncio
from interactive_analyzer import fetch_listings, display_listings

async def test():
    print("Testing listing fetch...")
    listings = await fetch_listings()
    print(f"\n✅ Got {len(listings)} listings!")
    display_listings(listings)
    
    print("\n📋 Full details of first listing:")
    if listings:
        listing = listings[0]
        print(f"  Address: {listing.address}")
        print(f"  Price: ${listing.ask_price:,.0f}" if listing.ask_price else "  Price: N/A")
        print(f"  Cap Rate: {listing.cap_rate}%" if listing.cap_rate else "  Cap Rate: N/A")
        print(f"  Units: {listing.units}" if listing.units else "  Units: N/A")
        print(f"  Size: {listing.building_size:,.0f} SF" if listing.building_size else "  Size: N/A")
        print(f"  Listing ID: {listing.listing_id}")

asyncio.run(test())
