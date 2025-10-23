"""FastAPI application for real estate analysis API."""
import html
import json
from typing import Optional

from fastapi import Body, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import ValidationError

from .app.config import settings
from .app.filters import load_filters, update_filters, reset_filters, save_filters, load_city_name
from .app.models import (
    SearchParams,
    FinalReport,
    FilterUpdate,
    ListingPreview,
    AnalysisPayload,
    AnalyzeSelectionRequest,
    AgentSummary,
    FinalSummary,
    Listing,
)
from .app.loopnet_client import LoopNetClient, LoopNetAPIError
from .app.crew import PropertyAnalysisCrew


app = FastAPI(
    title="Real Estate Scout API",
    description="Multi-agent property analysis using LoopNet + CrewAI",
    version="0.1.0"
)

default_cors_origins = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}

if settings.frontend_origins:
    default_cors_origins.update(settings.frontend_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


def _build_listing_preview(listing: "Listing") -> ListingPreview:
    """Transform internal Listing model into the UI-friendly preview schema."""

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


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Real Estate Scout API",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "filters": {
                "get": "GET /filters",
                "update": "POST /filters",
                "reset": "POST /filters/reset",
                "ui": "GET /filters/ui"
            },
            "analyze": "POST /analyze"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns API status and configuration info.
    """
    # Check if API keys are configured
    rapidapi_configured = bool(settings.rapidapi_key and settings.rapidapi_key != "__SET_ME__")
    openai_configured = bool(settings.openai_api_key and settings.openai_api_key != "__SET_ME__")
    
    return {
        "status": "healthy",
        "rapidapi_configured": rapidapi_configured,
        "openai_configured": openai_configured,
        "weights": settings.get_weights()
    }


def _render_bool_select(name: str, current: Optional[bool]) -> str:
    current_value = "" if current is None else ("true" if current else "false")
    options = [
        ("", "Auto"),
        ("true", "True"),
        ("false", "False"),
    ]
    rendered = []
    for value, label in options:
        selected = " selected" if value == current_value else ""
        rendered.append(f'<option value="{value}"{selected}>{label}</option>')
    return f'<select name="{name}" class="field-input">{"".join(rendered)}</select>'


def _render_filter_form(filters: SearchParams, message: Optional[str] = None, error: Optional[str] = None) -> str:
    data = filters.model_dump()

    def val(field: str) -> str:
        value = data.get(field)
        return "" if value is None else str(value)

    feedback_block = ""
    if message:
        feedback_block = f'<div class="feedback success">{html.escape(message)}</div>'
    if error:
        feedback_block += f'<div class="feedback error">{html.escape(error)}</div>'

    filters_json = html.escape(json.dumps(data, indent=2), quote=False)

    return f"""<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <title>LoopNet Filter Manager</title>
    <style>
      body {{ font-family: 'Inter', Arial, sans-serif; background: #f4f5f7; margin: 0; padding: 32px; color: #1f2933; }}
      h1 {{ margin-bottom: 8px; }}
      p.lead {{ color: #52606d; margin-top: 0; }}
      .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 32px; border-radius: 12px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); }}
      form {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px 24px; margin-top: 24px; }}
      label {{ display: flex; flex-direction: column; font-size: 14px; color: #334155; font-weight: 600; gap: 6px; }}
      .field-input {{ padding: 10px 12px; border-radius: 8px; border: 1px solid #cbd5e1; background: #f8fafc; font-size: 14px; transition: border-color 0.2s ease, box-shadow 0.2s ease; }}
      .field-input:focus {{ outline: none; border-color: #6366f1; box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15); background: white; }}
      .actions {{ grid-column: 1 / -1; display: flex; gap: 12px; margin-top: 8px; flex-wrap: wrap; }}
      button {{ padding: 10px 18px; border-radius: 8px; border: none; cursor: pointer; font-size: 14px; font-weight: 600; }}
      button.primary {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; box-shadow: 0 10px 18px rgba(99, 102, 241, 0.18); }}
      button.secondary {{ background: #e2e8f0; color: #334155; }}
      button.secondary:hover {{ background: #cbd5e1; }}
      .feedback {{ grid-column: 1 / -1; padding: 12px 16px; border-radius: 8px; font-size: 14px; }}
      .feedback.success {{ background: #dcfce7; color: #065f46; }}
      .feedback.error {{ background: #fee2e2; color: #b91c1c; }}
      pre {{ background: #0f172a; color: #e2e8f0; padding: 16px; border-radius: 10px; overflow-x: auto; font-size: 13px; line-height: 1.5; grid-column: 1 / -1; }}
      .help {{ grid-column: 1 / -1; font-size: 13px; color: #475569; margin-bottom: 4px; }}
    </style>
  </head>
  <body>
    <div class=\"container\">
      <h1>LoopNet Filter Manager</h1>
      <p class=\"lead\">Adjust the stored search filters used by the LoopNet analyzer. Leave a field blank to remove that filter.</p>
      {feedback_block}
      <form method=\"post\" action=\"/filters/ui\">
        <label>Location ID<input class=\"field-input\" name=\"locationId\" value=\"{html.escape(val('locationId'))}\" required /></label>
        <label>Location Type<input class=\"field-input\" name=\"locationType\" value=\"{html.escape(val('locationType'))}\" required /></label>
        <label>Page<input class=\"field-input\" type=\"number\" name=\"page\" min=\"1\" value=\"{html.escape(val('page'))}\" /></label>
        <label>Page Size<input class=\"field-input\" type=\"number\" name=\"size\" min=\"1\" max=\"100\" value=\"{html.escape(val('size'))}\" /></label>
        <label>Price Min ($)<input class=\"field-input\" type=\"number\" step=\"1000\" name=\"priceMin\" value=\"{html.escape(val('priceMin'))}\" /></label>
        <label>Price Max ($)<input class=\"field-input\" type=\"number\" step=\"1000\" name=\"priceMax\" value=\"{html.escape(val('priceMax'))}\" /></label>
        <label>Building Size Min (SF)<input class=\"field-input\" type=\"number\" step=\"100\" name=\"buildingSizeMin\" value=\"{html.escape(val('buildingSizeMin'))}\" /></label>
        <label>Building Size Max (SF)<input class=\"field-input\" type=\"number\" step=\"100\" name=\"buildingSizeMax\" value=\"{html.escape(val('buildingSizeMax'))}\" /></label>
        <label>Property Type<input class=\"field-input\" name=\"propertyType\" value=\"{html.escape(val('propertyType'))}\" /></label>
        <label>Cap Rate Min (%)<input class=\"field-input\" type=\"number\" step=\"0.1\" name=\"capRateMin\" value=\"{html.escape(val('capRateMin'))}\" /></label>
        <label>Cap Rate Max (%)<input class=\"field-input\" type=\"number\" step=\"0.1\" name=\"capRateMax\" value=\"{html.escape(val('capRateMax'))}\" /></label>
        <label>Year Built Min<input class=\"field-input\" type=\"number\" name=\"yearBuiltMin\" value=\"{html.escape(val('yearBuiltMin'))}\" /></label>
        <label>Year Built Max<input class=\"field-input\" type=\"number\" name=\"yearBuiltMax\" value=\"{html.escape(val('yearBuiltMax'))}\" /></label>
        <label>Include Auctions{_render_bool_select('auctions', filters.auctions)}</label>
        <label>Exclude Pending Sales{_render_bool_select('excludePendingSales', filters.excludePendingSales)}</label>
        <div class=\"help\">Use the buttons below to save changes or reset to defaults.</div>
                <div class=\"actions\">
                    <button type=\"submit\" class=\"primary\">Save Filters</button>
                    <button type=\"submit\" class=\"secondary\" formaction=\"/filters/ui/reset\" formmethod=\"post\">Reset Defaults</button>
                </div>
      </form>
      <h2>Current Configuration</h2>
      <pre>{filters_json}</pre>
    </div>
  </body>
</html>
"""


@app.get("/filters", response_model=SearchParams)
async def get_filters():
    """Return the currently stored filters."""
    return load_filters()


@app.post("/filters", response_model=SearchParams)
async def set_filters(update: FilterUpdate):
    """Update stored filters using a JSON payload."""
    try:
        updated = update_filters(update.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return updated


@app.post("/filters/reset", response_model=SearchParams)
async def reset_filters_route():
    """Reset filters to their default values."""
    return reset_filters()


@app.get("/filters/ui", response_class=HTMLResponse)
async def filters_ui(request: Request):
    """Render HTML filter editor."""
    saved_state = request.query_params.get("saved")
    message = None
    if saved_state == "1":
        message = "Filters updated successfully."
    elif saved_state == "reset":
        message = "Filters reset to defaults."
    content = _render_filter_form(load_filters(), message=message)
    return HTMLResponse(content=content)


@app.post("/filters/ui")
async def filters_ui_submit(request: Request):
    """Handle HTML form submissions for filter updates."""
    form = await request.form()
    payload = {}
    for field in FilterUpdate.model_fields.keys():
        if field not in form:
            continue
        value = form[field]
        payload[field] = None if value == "" else value
    try:
        update_model = FilterUpdate(**payload)
        update_filters(update_model.model_dump(exclude_unset=True))
    except (ValidationError, ValueError) as exc:
        content = _render_filter_form(load_filters(), error=str(exc))
        return HTMLResponse(content=content, status_code=400)
    return RedirectResponse(url="/filters/ui?saved=1", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/filters/ui/reset")
async def filters_ui_reset():
    """Reset filters via HTML form."""
    reset_filters()
    return RedirectResponse(url="/filters/ui?saved=reset", status_code=status.HTTP_303_SEE_OTHER)


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
    """Expose LoopNet search results for the frontend without triggering analysis."""

    if not settings.rapidapi_key or settings.rapidapi_key == "__SET_ME__":
        raise HTTPException(
            status_code=500,
            detail="RAPIDAPI_KEY not configured. Set it in .env file.",
        )

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
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")

    return [_build_listing_preview(listing) for listing in listings]


@app.post("/analyze/listings", response_model=list[AnalysisPayload])
async def analyze_selected_listings(request: AnalyzeSelectionRequest):
    """Analyze specific listings selected in the UI with chosen crews."""

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

    if not settings.rapidapi_key or settings.rapidapi_key == "__SET_ME__":
        raise HTTPException(
            status_code=500,
            detail="RAPIDAPI_KEY not configured. Set it in .env file.",
        )
    if not settings.openai_api_key or settings.openai_api_key == "__SET_ME__":
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY not configured. Set it in .env file.",
        )

    filters = request.filters or load_filters()
    active_city = request.cityName or (request.filters is None and load_city_name()) or None

    client = LoopNetClient()
    try:
        listings = await client.search_properties(filters, city_name=active_city)
    except LoopNetAPIError as exc:
        raise HTTPException(status_code=502, detail=f"LoopNet API error: {exc}")
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")

    listing_map = {listing.listing_id: listing for listing in listings}
    missing = [listing_id for listing_id in request.listingIds if listing_id not in listing_map]
    if missing:
        raise HTTPException(status_code=404, detail={"missingListingIds": missing})

    crew = PropertyAnalysisCrew()
    results: list[AnalysisPayload] = []

    for listing_id in request.listingIds:
        listing = listing_map[listing_id]
        report = await crew.analyze_listing(listing, enabled_agents=normalized_crews)

        raw_json = report.model_dump()
        agents_payload: list[AgentSummary] = []

        agent_outputs = {
            "investment": report.investment_output,
            "location": report.location_output,
            "news": report.news_output,
            "vc_risk": report.vc_risk_output,
            "construction": report.construction_output,
        }

        for agent_key in normalized_crews:
            output = agent_outputs.get(agent_key)
            if not output:
                continue
            agents_payload.append(
                AgentSummary(
                    name=AGENT_LABELS.get(agent_key, agent_key.title()),
                    score=output.score_1_to_100,
                    summary=output.rationale,
                )
            )

        if include_la_city:
            try:
                la_records = crew.fetch_la_city_records(listing)
            except Exception as exc:  # pragma: no cover - network issues
                la_summary = f"LA City data unavailable: {exc}"
                la_score = 0
            else:
                counts = (la_records.get("meta") or {}).get("counts") or {}
                la_score = sum(counts.values())
                parts = [
                    f"{LA_DATASET_LABELS.get(dataset, dataset)}: {counts.get(dataset, 0)}"
                    for dataset in LA_DATASET_LABELS
                ]
                la_summary = ", ".join(parts) if parts else "No LA dataset counts available."
                raw_json["la_city_records"] = la_records

            agents_payload.append(
                AgentSummary(name="LA City Data", score=la_score, summary=la_summary)
            )

        final_summary_text = (report.summary or "Summary unavailable").strip()
        results.append(
            AnalysisPayload(
                listingId=listing_id,
                agents=agents_payload,
                final=FinalSummary(
                    summary=final_summary_text,
                    overallScore=report.scores.overall,
                ),
                rawJson=raw_json,
            )
        )

    return results


@app.post("/analyze", response_model=list[FinalReport])
async def analyze_properties(
    params: Optional[SearchParams] = Body(default=None),
    use_stored: bool = False,
    persist_filters: bool = False,
):
    """
    Analyze commercial properties from LoopNet.
    
    **Query Parameters:**
    - `use_stored`: Use the saved filters even if a request body is supplied (defaults to `false`)
    - `persist_filters`: Persist the effective filters back to storage when providing a body

    **Process:**
    1. Query LoopNet API with search parameters
    2. Run multi-agent analysis on each listing
    3. Return scored reports with investment memos
    
    **Example Request:**
    ```json
    {
      "locationId": "41096",
      "locationType": "city",
      "page": 1,
      "size": 5,
      "priceMin": 500000,
      "priceMax": 3000000
    }
    ```
    
    **Returns:**
    Array of FinalReport objects with:
    - Individual agent scores (1-100)
    - Overall weighted score (1-100)
    - Investment memo (markdown)
    """
    # Determine search parameters (stored or request body)
    if params is None or use_stored:
        search_params = load_filters()
    else:
        search_params = params
        if persist_filters:
            save_filters(search_params)

    # Validate API keys
    if not settings.rapidapi_key or settings.rapidapi_key == "__SET_ME__":
        raise HTTPException(
            status_code=500,
            detail="RAPIDAPI_KEY not configured. Set it in .env file."
        )
    
    if not settings.openai_api_key or settings.openai_api_key == "__SET_ME__":
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY not configured. Set it in .env file."
        )
    
    # Fetch listings from LoopNet
    client = LoopNetClient()
    try:
        # Check if cityName is provided in filters.json
        city_name = load_city_name()
        if city_name:
            print(f"🔍 Resolving city name: {city_name}")
        
        listings = await client.search_properties(search_params, city_name=city_name)
        
        if city_name:
            print(f"✅ Found {len(listings)} listings")
    except LoopNetAPIError as e:
        message = str(e)
        if "No data found" in message:
            print("⚠️  LoopNet returned no data for the current filters.")
            return []
        raise HTTPException(status_code=502, detail=f"LoopNet API error: {message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    if not listings:
        return []
    
    # Analyze each listing with multi-agent crew
    crew = PropertyAnalysisCrew()
    reports = []
    
    for listing in listings:
        try:
            report = await crew.analyze_listing(listing)
            reports.append(report)
        except Exception as e:
            print(f"Error analyzing listing {listing.listing_id}: {e}")
            continue
    
    # Persist each report to disk for later review
    try:
        from pathlib import Path
        out_dir = Path.cwd() / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        for report in reports:
            file_path = out_dir / f"{report.listing_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))
        print(f"✅ Saved {len(reports)} reports to: {out_dir}")
    except Exception as e:
        print(f"❌ Failed to save reports: {e}")
    
    return reports


@app.exception_handler(LoopNetAPIError)
async def loopnet_exception_handler(request, exc):
    """Handle LoopNet API errors gracefully."""
    return JSONResponse(
        status_code=502,
        content={"error": "LoopNet API error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
