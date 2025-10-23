"""Lightweight FastAPI application optimized for Vercel serverless deployment.

This module avoids heavy AI orchestration dependencies so the serverless bundle
stays below the 250 MB limit. It provides the same REST surface as
``src.main.app`` but relies on transparent heuristics instead of CrewAI agents.
"""
from __future__ import annotations

from statistics import mean
from typing import Optional

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .app.config import settings
from .app.filters import (
    load_city_name,
    load_filters,
    reset_filters,
    save_filters,
    update_filters,
)
from .app.loopnet_client import LoopNetAPIError, LoopNetClient
from .app.models import (
    AgentSummary,
    AnalysisPayload,
    AnalyzeSelectionRequest,
    FinalSummary,
    FilterUpdate,
    Listing,
    ListingPreview,
    SearchParams,
)

CREW_KEY_MAP: dict[str, str] = {
    "Investment": "investment",
    "LocationRisk": "location",
    "NewsReddit": "news",
    "VCRiskReturn": "vc_risk",
    "Construction": "construction",
    "LACityData": "la_city",
    "investment": "investment",
    "location": "location",
    "news": "news",
    "vc_risk": "vc_risk",
    "construction": "construction",
    "la_city": "la_city",
}

AGENT_LABELS: dict[str, str] = {
    "investment": "Investment",
    "location": "Location Risk",
    "news": "News / Reddit",
    "vc_risk": "VC Risk / Return",
    "construction": "Construction",
}

LA_DATASET_LABELS: dict[str, str] = {
    "permits": "Building Permits",
    "inspections": "Inspections",
    "coo": "Certificates of Occupancy",
    "code_open": "Open Code Violations",
    "code_closed": "Closed Code Violations",
}

app = FastAPI(
    title="Real Estate Scout API (Lite)",
    description="Lightweight analysis service for demo deployments.",
    version="0.1.0-lite",
)

_default_cors_origins = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}
if settings.frontend_origins:
    _default_cors_origins.update(settings.frontend_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(_default_cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StripAPIPrefixMiddleware(BaseHTTPMiddleware):
    """Allow the app to serve both `/` and `/api` prefixed routes.

    Vercel rewrites requests to the Python function with their original path
    preserved (for example, `/api/health`). The FastAPI app historically served
    endpoints without the `/api` prefix, so those requests returned 404s once
    deployment protection was bypassed. This middleware trims the `/api`
    segment before routing so existing handlers continue to work without code
    duplication.
    """

    def __init__(self, app, prefix: str = "/api"):
        super().__init__(app)
        self.prefix = prefix

    async def dispatch(self, request, call_next):  # type: ignore[override]
        scope = request.scope
        path = scope.get("path", "")

        if path == self.prefix:
            scope["path"] = "/"
        elif path.startswith(self.prefix + "/"):
            scope["path"] = path[len(self.prefix) :]

        raw_path = scope.get("raw_path")
        if raw_path:
            raw_str = raw_path.decode("latin-1")
            if raw_str == self.prefix:
                scope["raw_path"] = b"/"
            elif raw_str.startswith(self.prefix + "/"):
                scope["raw_path"] = raw_str[len(self.prefix) :].encode("latin-1")

        return await call_next(request)


app.add_middleware(StripAPIPrefixMiddleware)


def _build_listing_preview(listing: Listing) -> ListingPreview:
    raw = listing.raw or {}
    photo = raw.get("photo") or raw.get("primaryPhoto")
    if isinstance(photo, dict):
        photo = photo.get("url") or photo.get("image")

    return ListingPreview(
        id=listing.listing_id,
        address=listing.address,
        price=listing.ask_price,
        capRate=listing.cap_rate,
        units=listing.units,
        size=listing.building_size,
        city=listing.city,
        state=listing.state,
        photoUrl=photo,
    )


def _score_cap_rate(cap_rate: Optional[float]) -> tuple[int, str]:
    if cap_rate is None:
        return 55, "Cap rate unavailable; using neutral stance."
    score = max(35, min(95, int(round(cap_rate * 10))))
    rationale = f"Cap rate of {cap_rate:.1f}% implies{' strong' if score >= 70 else ' moderate' if score >= 55 else ' limited'} yield potential."
    return score, rationale


def _score_location(listing: Listing) -> tuple[int, str]:
    metro_bonus = {
        "los angeles": 10,
        "santa monica": 8,
        "pasadena": 6,
    }
    city = (listing.city or "").lower()
    base = 60
    bonus = metro_bonus.get(city, 0)
    if listing.zip_code and listing.zip_code.startswith("90"):
        bonus = max(bonus, 7)
    score = max(40, min(92, base + bonus))
    rationale = (
        f"{listing.city or 'Unknown city'}, {listing.state or 'N/A'} with"
        f" {('favorable demographics' if bonus else 'limited market data')}"
    )
    return score, rationale


def _score_risk_return(listing: Listing) -> tuple[int, str]:
    size = listing.building_size or 0
    units = listing.units or 0
    year = listing.year_built or 0
    cap_rate = listing.cap_rate or 0

    score = 55
    if size > 20000 or units > 20:
        score += 8
    if year and year < 1970:
        score -= 6
    if cap_rate >= 8:
        score += 10
    score = max(35, min(90, score))
    rationale = "Balanced risk/return profile with "
    if cap_rate >= 8:
        rationale += "above-market yield signals."
    elif size > 20000:
        rationale += "institutional scale benefits."
    else:
        rationale += "limited quantitative inputs available."
    return score, rationale


def _score_construction(listing: Listing) -> tuple[int, str]:
    year = listing.year_built
    if not year:
        return 58, "No year built data; recommend exterior envelope inspection."
    if year >= 2010:
        return 75, "Recent construction vintage; major systems likely modernized."
    if year >= 1990:
        return 68, "Post-1990 asset; systems approaching mid-life, budget CapEx."
    if year >= 1970:
        return 55, "1970s-1980s structure; review seismic retrofits and deferred CapEx."
    return 45, "Pre-1970 asset; expect structural and building-system upgrades."


def _news_summary(listing: Listing) -> tuple[int, str]:
    location = f"{listing.city}, {listing.state}" if listing.city and listing.state else listing.city or "the market"
    return 50, f"Live news sentiment unavailable in lite mode; monitor headlines for {location}."


def _make_agent_payload(agent_key: str, score: int, summary: str) -> AgentSummary:
    return AgentSummary(name=AGENT_LABELS.get(agent_key, agent_key.title()), score=score, summary=summary)


def _build_analysis_payload(listing: Listing, selected_crews: list[str]) -> AnalysisPayload:
    agent_summaries: list[AgentSummary] = []
    score_values: list[int] = []

    for crew_name in selected_crews:
        if crew_name == "investment":
            score, summary = _score_cap_rate(listing.cap_rate)
        elif crew_name == "location":
            score, summary = _score_location(listing)
        elif crew_name == "vc_risk":
            score, summary = _score_risk_return(listing)
        elif crew_name == "construction":
            score, summary = _score_construction(listing)
        elif crew_name == "news":
            score, summary = _news_summary(listing)
        elif crew_name == "la_city":
            score = 45
            summary = "LA City dataset integration is disabled in the demo deployment."
        else:
            score = 50
            summary = "Crew not recognized; defaulting to neutral observation."

        agent_summaries.append(_make_agent_payload(crew_name, score, summary))
        score_values.append(score)

    overall = int(round(mean(score_values))) if score_values else 50
    summary_lines = [
        f"Cap rate: {listing.cap_rate:.1f}%" if listing.cap_rate else "Cap rate unavailable",
        f"Asking price: ${listing.ask_price:,.0f}" if listing.ask_price else "Price TBD",
        f"Units: {listing.units}" if listing.units else "Units not provided",
    ]
    final_summary = FinalSummary(
        summary="; ".join(summary_lines),
        overallScore=overall,
    )

    raw_json = {
        "listing_id": listing.listing_id,
        "address": listing.address,
        "city": listing.city,
        "state": listing.state,
        "cap_rate": listing.cap_rate,
        "ask_price": listing.ask_price,
        "units": listing.units,
        "notes": [agent.summary for agent in agent_summaries],
    }

    return AnalysisPayload(
        listingId=listing.listing_id,
        agents=agent_summaries,
        final=final_summary,
        rawJson=raw_json,
    )


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "analysis_mode": "lite",
        "rapidapi_configured": bool(settings.rapidapi_key and settings.rapidapi_key != "__SET_ME__"),
    }


@app.get("/filters", response_model=SearchParams)
async def get_filters():
    return load_filters()


@app.post("/filters", response_model=SearchParams)
async def set_filters(update: FilterUpdate):
    updated = update_filters(update.model_dump(exclude_unset=True))
    return updated


@app.post("/filters/reset", response_model=SearchParams)
async def reset_filters_route():
    return reset_filters()


@app.get("/search", response_model=list[ListingPreview])
async def search_properties_endpoint(
    city_name: Optional[str] = Query(default=None, alias="cityName"),
    location_id: Optional[str] = Query(default=None, alias="locationId"),
    location_type: str = Query(default="city", alias="locationType"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=5, ge=1, le=100),
    price_min: Optional[float] = Query(default=None, alias="priceMin"),
    price_max: Optional[float] = Query(default=None, alias="priceMax"),
    building_size_min: Optional[float] = Query(default=None, alias="buildingSizeMin"),
    building_size_max: Optional[float] = Query(default=None, alias="buildingSizeMax"),
    property_type: Optional[str] = Query(default=None, alias="propertyType"),
    cap_rate_min: Optional[float] = Query(default=None, alias="capRateMin"),
    cap_rate_max: Optional[float] = Query(default=None, alias="capRateMax"),
    year_built_min: Optional[int] = Query(default=None, alias="yearBuiltMin"),
    year_built_max: Optional[int] = Query(default=None, alias="yearBuiltMax"),
    auctions: Optional[bool] = Query(default=None, alias="auctions"),
    exclude_pending_sales: Optional[bool] = Query(default=None, alias="excludePendingSales"),
):
    if not settings.rapidapi_key or settings.rapidapi_key == "__SET_ME__":
        raise HTTPException(status_code=500, detail="RAPIDAPI_KEY not configured. Set it in environment variables.")

    search_params = SearchParams(
        locationId=location_id,
        locationType=location_type,
        page=page,
        size=size,
        priceMin=price_min,
        priceMax=price_max,
        buildingSizeMin=building_size_min,
        buildingSizeMax=building_size_max,
        propertyType=property_type,
        capRateMin=cap_rate_min,
        capRateMax=cap_rate_max,
        yearBuiltMin=year_built_min,
        yearBuiltMax=year_built_max,
        auctions=auctions,
        excludePendingSales=exclude_pending_sales,
    )

    client = LoopNetClient()
    active_city = city_name or load_city_name()

    try:
        listings = await client.search_properties(search_params, city_name=active_city)
    except LoopNetAPIError as exc:
        raise HTTPException(status_code=502, detail=f"LoopNet API error: {exc}")
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")

    return [_build_listing_preview(listing) for listing in listings]


@app.post("/analyze/listings", response_model=list[AnalysisPayload])
async def analyze_selected_listings(request: AnalyzeSelectionRequest = Body(...)):
    if not request.listingIds:
        raise HTTPException(status_code=400, detail="listingIds must not be empty")
    if not request.crews:
        raise HTTPException(status_code=400, detail="At least one crew must be provided")

    normalized_crews: list[str] = []
    include_la_city = False
    for crew_name in request.crews:
        mapped = CREW_KEY_MAP.get(crew_name)
        if not mapped:
            raise HTTPException(status_code=400, detail=f"Unknown crew '{crew_name}'")
        if mapped == "la_city":
            include_la_city = True
        else:
            normalized_crews.append(mapped)

    if include_la_city:
        normalized_crews.append("la_city")

    if not settings.rapidapi_key or settings.rapidapi_key == "__SET_ME__":
        raise HTTPException(status_code=500, detail="RAPIDAPI_KEY not configured. Set it in environment variables.")

    filters = request.filters or load_filters()
    active_city = request.cityName or (request.filters is None and load_city_name()) or None

    client = LoopNetClient()
    try:
        listings = await client.search_properties(filters, city_name=active_city)
    except LoopNetAPIError as exc:
        raise HTTPException(status_code=502, detail=f"LoopNet API error: {exc}")
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")

    listing_map = {listing.listing_id: listing for listing in listings}
    missing = [listing_id for listing_id in request.listingIds if listing_id not in listing_map]
    if missing:
        raise HTTPException(status_code=404, detail={"missingListingIds": missing})

    results: list[AnalysisPayload] = []
    for listing_id in request.listingIds:
        listing = listing_map[listing_id]
        results.append(_build_analysis_payload(listing, normalized_crews))

    return results


@app.post("/analyze", response_model=list[AnalysisPayload])
async def analyze_properties(
    params: Optional[SearchParams] = Body(default=None),
    use_stored: bool = False,
    persist_filters: bool = False,
):
    if params is None or use_stored:
        filters = load_filters()
    else:
        filters = params
        if persist_filters:
            save_filters(filters)

    request = AnalyzeSelectionRequest(listingIds=[], crews=["investment", "location", "news", "vc_risk", "construction"], filters=filters)

    client = LoopNetClient()
    city_name = load_city_name()
    try:
        listings = await client.search_properties(filters, city_name=city_name)
    except LoopNetAPIError as exc:
        raise HTTPException(status_code=502, detail=f"LoopNet API error: {exc}")

    request.listingIds = [listing.listing_id for listing in listings]
    request.cityName = city_name

    return await analyze_selected_listings(request)


@app.get("/")
async def root():
    return {
        "service": "Real Estate Scout API (Lite)",
        "version": "0.1.0-lite",
        "analysis": "heuristic",
    }
