"""
LoopNet minimal flow:
1) Load filters from config/filters.json
2) If cityName is provided, resolve it to locationId using /loopnet/helper/findCity
3) Query /loopnet/sale/advanceSearch with all filters
4) Display results in a clean, readable format
"""
import os, json, httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-host": "loopnet-api.p.rapidapi.com",
    "x-rapidapi-key": RAPIDAPI_KEY or ""
}

FIND_CITY_URL = "https://loopnet-api.p.rapidapi.com/loopnet/helper/findCity"
SEARCH_URL    = "https://loopnet-api.p.rapidapi.com/loopnet/sale/advanceSearch"
FILTERS_FILE = Path(__file__).parent / "config" / "filters.json"

def fmt_price(item: dict) -> str:
    # Prefer numeric; fallback to marketing string
    full = item.get("fullPrice")
    if isinstance(full, (int, float)):
        return f"${full:,.0f}"
    s = item.get("price")
    return s if s else "N/A"

def fmt_address(item: dict) -> str:
    # title is typically ["street", "City, ST ZIP"]
    t = item.get("title")
    if isinstance(t, list) and t:
        return ", ".join([x for x in t if isinstance(x, str) and x.strip()])
    # Some payloads have 'address' in later endpoints—fallback:
    return item.get("address") or "N/A"

def resolve_city_id(keywords: str) -> tuple[str, str]:
    """Return (locationId, display) from /helper/findCity."""
    payload = {"keywords": keywords}
    r = httpx.post(FIND_CITY_URL, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    body = r.json()
    arr = (body or {}).get("data") or []
    if not arr:
        raise RuntimeError(f"No city results for '{keywords}'")
    # Pick the best match: first exact match if present, else first item
    exact = next((x for x in arr if x.get("display", "").lower().startswith(keywords.lower())), None)
    best = exact or arr[0]
    return best.get("id"), best.get("display")

def load_filters_from_file() -> dict:
    """Load filters from config/filters.json."""
    if not FILTERS_FILE.exists():
        raise FileNotFoundError(f"Filters file not found: {FILTERS_FILE}")
    with open(FILTERS_FILE, 'r') as f:
        return json.load(f)

def search_listings(filters: dict):
    """
    Search LoopNet using filters from config/filters.json.
    If cityName is present, resolve it to locationId first.
    """
    # Make a copy to avoid modifying the original
    payload = filters.copy()
    
    # If cityName is provided, resolve it to locationId
    if "cityName" in payload:
        city_name = payload.pop("cityName")
        print(f"🔍 Resolving city: {city_name}")
        location_id, display = resolve_city_id(city_name)
        print(f"   ✅ Found: {display} -> locationId={location_id}")
        payload["locationId"] = location_id
    
    # Remove any null values for cleaner API request
    payload = {k: v for k, v in payload.items() if v is not None}
    
    print(f"\n📋 Request payload:")
    print(json.dumps(payload, indent=2))
    
    r = httpx.post(SEARCH_URL, headers=HEADERS, json=payload, timeout=30)
    print(f"Status: {r.status_code}")
    body = r.json()
    
    # Show sample keys for debugging
    if (body.get("data") or []):
        print(f"✅ API returned {len(body['data'])} listings")
    else:
        print(f"⚠️  Response: {json.dumps(body, indent=2)}")
    
    return body

def extract_key_fields(item: dict) -> dict:
    """Extract and organize the most important fields from a listing."""
    facts = item.get('shortPropertyFacts', [])
    
    # Parse nested facts array for key metrics
    cap_rate = "N/A"
    units = "N/A"
    building_size = "N/A"
    year_built = "N/A"
    
    # The structure is nested arrays - flatten and search
    for fact_group in facts:
        if isinstance(fact_group, list):
            for fact in fact_group:
                if isinstance(fact, str):
                    # Direct string matches
                    if "%" in fact and "Cap" not in fact:
                        cap_rate = fact
                    elif "Built in" in fact:
                        year_built = fact.replace("Built in ", "")
                elif isinstance(fact, list):
                    # Nested array - check each element
                    for i, field in enumerate(fact):
                        if isinstance(field, str):
                            if "%" in field and "Cap" not in field:
                                cap_rate = field
                            elif "Units" in field:
                                # Previous element is the number
                                if i > 0:
                                    units = str(fact[i-1])
                            elif "SF Bldg" in field:
                                # Previous element is the size
                                if i > 0:
                                    building_size = f"{fact[i-1]} SF"
                            elif "Cap Rate" in field:
                                # Previous element is the percentage
                                if i > 0:
                                    cap_rate = str(fact[i-1])
    
    location = item.get('location', {})
    broker_details = item.get('brokersDetails', [{}])[0]
    
    return {
        'address': fmt_address(item),
        'price': fmt_price(item),
        'cap_rate': cap_rate,
        'units': units,
        'building_size': building_size,
        'year_built': year_built,
        'property_type': location.get('availableSpace', 'N/A'),
        'description': item.get('shortSummary', 'N/A'),
        'broker_name': item.get('brokerName', 'N/A'),
        'company': broker_details.get('company', 'N/A'),
        'photo': item.get('photo', 'N/A')
    }

def print_results(body, label="results"):
    data = body.get("data") or []
    print(f"\n✅ {label}: {len(data)} listing(s) found\n")
    
    for i, it in enumerate(data[:10], 1):
        listing_id = it.get('listingId', 'N/A')
        
        # Correct LoopNet URL format - property ID in path
        # Format: https://www.loopnet.com/Listing/[ADDRESS]/[LISTING_ID]/
        title = it.get('title', [])
        if isinstance(title, list) and len(title) >= 2:
            street = title[0].replace(' ', '-').replace(',', '')
            city_state = title[1].replace(' ', '-').replace(',', '')
            url = f"https://www.loopnet.com/Listing/{street}-{city_state}/{listing_id}/"
        else:
            url = f"https://www.loopnet.com/Listing/{listing_id}/"
        
        # Extract key fields
        fields = extract_key_fields(it)
        
        print(f"{'='*90}")
        print(f"🏢 LISTING #{i}")
        print(f"{'='*90}")
        print(f"📍 Address:        {fields['address']}")
        print(f"💰 Price:          {fields['price']}")
        print(f"📊 Cap Rate:       {fields['cap_rate']}")
        print(f"🏘️  Units:          {fields['units']}")
        print(f"📐 Building Size:  {fields['building_size']}")
        print(f"📅 Year Built:     {fields['year_built']}")
        print(f"🏗️  Type:           {fields['property_type']}")
        print(f"\n👔 Broker:         {fields['broker_name']}")
        print(f"🏢 Company:        {fields['company']}")
        print(f"\n� Listing URL:    {url}")
        print(f"🖼️  Photo:          {fields['photo']}")
        print(f"\n📝 Description:")
        print(f"   {fields['description'][:200]}...")
        print(f"{'='*90}\n")

def main():
    print("="*90)
    print("🧪 LOOPNET FLOW TEST - Loading filters from config/filters.json")
    print("="*90)

    try:
        # Load filters from file
        print(f"\n� Loading filters from: {FILTERS_FILE}")
        filters = load_filters_from_file()
        
        # Display loaded filters
        print(f"\n📋 Loaded filters:")
        for key, value in filters.items():
            if value is not None:
                print(f"   {key}: {value}")
        
        # Search with loaded filters
        print(f"\n{'='*90}")
        body = search_listings(filters)
        print(f"{'='*90}\n")
        
        # Display results
        city_name = filters.get("cityName", "Unknown Location")
        print_results(body, city_name)
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print(f"   Please create {FILTERS_FILE} with your search filters.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*90 + "\n🏁 Done\n" + "="*90)

if __name__ == "__main__":
    main()
