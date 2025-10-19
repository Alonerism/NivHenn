"""LoopNet API client with retry logic."""
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Optional

from .config import settings
from .models import SearchParams, Listing


class LoopNetAPIError(Exception):
    """Custom exception for LoopNet API errors."""
    pass


class LoopNetClient:
    """Client for LoopNet RapidAPI with automatic retries."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize client with API key from settings or override."""
        self.api_key = api_key or settings.rapidapi_key
        if not self.api_key or self.api_key == "__SET_ME__":
            raise ValueError("RAPIDAPI_KEY must be set in environment variables")
        
        self.base_url = settings.loopnet_base_url
        self.host = settings.loopnet_host
        self.headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": self.host,
            "x-rapidapi-key": self.api_key,
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _make_request(self, endpoint: str, payload: dict) -> dict:
        """Make HTTP POST request with retry logic."""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            
            # Handle rate limiting and server errors
            if response.status_code in [429, 500, 502, 503, 504]:
                response.raise_for_status()
            
            # Handle client errors (don't retry)
            if response.status_code >= 400:
                raise LoopNetAPIError(
                    f"LoopNet API error {response.status_code}: {response.text}"
                )
            
            return response.json()
    
    async def resolve_city_id(self, city_name: str) -> tuple[str, str]:
        """
        Resolve a city name to a LoopNet location ID.
        
        Args:
            city_name: City name (e.g., "Los Angeles", "Miami")
        
        Returns:
            Tuple of (locationId, display_name)
        """
        endpoint = "/loopnet/helper/findCity"
        payload = {"keywords": city_name}
        
        try:
            response_data = await self._make_request(endpoint, payload)
            results = response_data.get("data", [])
            
            if not results:
                raise LoopNetAPIError(f"No city results found for '{city_name}'")
            
            # Try to find exact match, otherwise use first result
            exact_match = next(
                (x for x in results if x.get("display", "").lower().startswith(city_name.lower())), 
                None
            )
            best_match = exact_match or results[0]
            
            location_id = best_match.get("id")
            display_name = best_match.get("display")
            
            if not location_id:
                raise LoopNetAPIError(f"Could not extract location ID for '{city_name}'")
            
            return location_id, display_name
            
        except LoopNetAPIError:
            raise
        except Exception as e:
            raise LoopNetAPIError(f"Error resolving city name: {e}")
    
    async def search_properties(self, params: SearchParams, city_name: Optional[str] = None) -> list[Listing]:
        """
        Search for commercial properties on LoopNet.
        
        Args:
            params: Search parameters (location, filters, pagination)
            city_name: Optional city name to resolve to locationId (overrides params.locationId)
        
        Returns:
            List of Listing objects
        """
        endpoint = "/loopnet/sale/advanceSearch"
        
        # Build payload from params, excluding None values
        payload = {
            k: v for k, v in params.model_dump().items() 
            if v is not None
        }
        
        # If city_name provided, resolve it to locationId
        if city_name:
            location_id, display_name = await self.resolve_city_id(city_name)
            payload["locationId"] = location_id
            payload["locationType"] = "city"
        
        # Ensure locationId is present
        if not payload.get("locationId"):
            raise LoopNetAPIError("locationId is required (provide locationId or city_name)")
        
        try:
            response_data = await self._make_request(endpoint, payload)
            listings = self._parse_listings(response_data)
            return listings
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise LoopNetAPIError("Rate limit exceeded. Please try again later.")
            raise LoopNetAPIError(f"HTTP error: {e}")
        except httpx.TimeoutException:
            raise LoopNetAPIError("Request timeout. Please try again.")
        except Exception as e:
            raise LoopNetAPIError(f"Unexpected error: {e}")
    
    def _parse_listings(self, response_data: dict) -> list[Listing]:
        """
        Parse LoopNet API response into Listing objects.
        Based on actual API response structure from /loopnet/sale/advanceSearch.
        """
        listings = []
        
        # LoopNet API returns data in response_data["data"]
        results = response_data.get("data", [])
        
        if not results:
            # No listings found
            return listings
        
        for item in results:
            # Extract address from title array: ["street", "city, state zip"]
            address = None
            city = None
            state = None
            zip_code = None
            
            title = item.get("title", [])
            if isinstance(title, list) and len(title) >= 2:
                address = title[0]  # Street address
                # Parse "Los Angeles, CA 90047" format
                city_state_zip = title[1]
                parts = city_state_zip.split(", ")
                if len(parts) >= 2:
                    city = parts[0]
                    state_zip = parts[1].split()
                    if state_zip:
                        state = state_zip[0]
                        if len(state_zip) > 1:
                            zip_code = state_zip[1]
            
            # Extract price (can be string like "$1.699M" or number)
            price_str = item.get("price") or item.get("fullPrice")
            ask_price = self._parse_price(price_str)
            
            # Extract property details from shortPropertyFacts nested structure
            cap_rate = None
            units = None
            building_size = None
            year_built = None
            
            facts = item.get("shortPropertyFacts", [])
            for fact_group in facts:
                if isinstance(fact_group, list):
                    for fact in fact_group:
                        if isinstance(fact, str):
                            if "%" in fact and "Cap" not in fact:
                                cap_rate = self._parse_percentage(fact)
                            elif "Built in" in fact:
                                year_built = self._safe_int(fact.replace("Built in ", ""))
                        elif isinstance(fact, list):
                            for i, field in enumerate(fact):
                                if isinstance(field, str):
                                    if "Cap Rate" in field and i > 0:
                                        cap_rate = self._parse_percentage(str(fact[i-1]))
                                    elif "Units" in field and i > 0:
                                        units = self._safe_int(fact[i-1])
                                    elif "SF Bldg" in field and i > 0:
                                        building_size = self._safe_float(str(fact[i-1]).replace(",", ""))
            
            # Get property type from location.availableSpace or shortPropertyFacts
            property_type = None
            location = item.get("location", {})
            available_space = location.get("availableSpace", "")
            if "Multi-Family" in available_space or "Apartments" in available_space:
                property_type = "multifamily"
            
            listing = Listing(
                listing_id=str(item.get("listingId", "unknown")),
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                ask_price=ask_price,
                building_size=building_size,
                property_type=property_type,
                cap_rate=cap_rate,
                year_built=year_built,
                units=units,
                raw=item,  # Store full raw data for agent analysis
            )
            listings.append(listing)
        
        return listings
    
    @staticmethod
    def _parse_price(price_str) -> Optional[float]:
        """Parse price string like '$1.699M' to float."""
        if not price_str:
            return None
        if isinstance(price_str, (int, float)):
            return float(price_str)
        
        # Handle strings like "$1.699M", "$2.35M", etc.
        price_str = str(price_str).replace("$", "").replace(",", "").strip()
        try:
            if "M" in price_str.upper():
                return float(price_str.upper().replace("M", "")) * 1_000_000
            elif "K" in price_str.upper():
                return float(price_str.upper().replace("K", "")) * 1_000
            else:
                return float(price_str)
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def _parse_percentage(percent_str) -> Optional[float]:
        """Parse percentage string like '5.72%' to float."""
        if not percent_str:
            return None
        try:
            return float(str(percent_str).replace("%", "").strip())
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """Safely convert value to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _safe_int(value) -> Optional[int]:
        """Safely convert value to int."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
