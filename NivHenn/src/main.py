"""FastAPI application for real estate analysis API."""
import html
import json
from typing import Optional

from fastapi import Body, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import ValidationError

from .app.config import settings
from .app.filters import load_filters, update_filters, reset_filters, save_filters, load_city_name
from .app.models import SearchParams, FinalReport, FilterUpdate
from .app.loopnet_client import LoopNetClient, LoopNetAPIError
from .app.crew import PropertyAnalysisCrew


app = FastAPI(
    title="Real Estate Scout API",
    description="Multi-agent property analysis using LoopNet + CrewAI",
    version="0.1.0"
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
        raise HTTPException(status_code=502, detail=f"LoopNet API error: {str(e)}")
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
                f.write(report.json(indent=2))
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
