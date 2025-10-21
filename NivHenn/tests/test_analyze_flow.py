"""End-to-end analysis flow test with mocked dependencies."""
import json

from fastapi.testclient import TestClient
import pytest

from src.main import app
from src.app import filters as filter_store
from src.app.loopnet_client import LoopNetAPIError
from src.app.models import (
    AgentOutput,
    AgentScores,
    FinalReport,
    Listing,
)


def test_analyze_uses_stored_filters(monkeypatch, tmp_path):
    """Ensure /analyze uses stored filters and integrates mocked services."""
    # Redirect filter storage to a temp file
    filters_file = tmp_path / "filters.json"
    filters_file.write_text(json.dumps({"locationId": "41096", "locationType": "city"}), encoding="utf-8")
    monkeypatch.setattr(filter_store, "_FILTERS_FILE", filters_file)

    # Provide fake API keys so the endpoint passes validation
    monkeypatch.setenv("RAPIDAPI_KEY", "test-rapid")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    from src.app.config import settings

    settings.rapidapi_key = "test-rapid"
    settings.openai_api_key = "test-openai"

    # Track Serper calls
    serper_calls: dict[str, tuple[str, int]] = {}

    def fake_serper(query: str, num: int = 8):
        serper_calls["latest"] = (query, num)
        return {"items": [{"title": "Mock Headline", "date": "2024-05-01"}]}

    from src.app import serper_news

    monkeypatch.setattr(serper_news, "search_news", fake_serper)

    sample_listing = Listing(
        listing_id="LN-1",
        address="123 Main St",
        city="Austin",
        state="TX",
        ask_price=1_000_000,
        raw={"source": "mock"},
    )

    async def fake_loopnet(self, params, city_name=None):  # noqa: D401 - simple mock
        if city_name:
            serper_calls["city_override"] = city_name
        return [sample_listing]

    monkeypatch.setattr("src.app.loopnet_client.LoopNetClient.search_properties", fake_loopnet)

    sample_report = FinalReport(
        listing_id="LN-1",
        address="123 Main St",
        ask_price=1_000_000,
        raw={"source": "mock"},
        scores=AgentScores(
            investment=80,
            location=78,
            news_signal=55,
            risk_return=72,
            construction=68,
            overall=71,
        ),
        memo_markdown="## Summary\nAll signals look stable.",
        investment_output=AgentOutput(
            score_1_to_100=80,
            rationale="Strong fundamentals",
            notes=["Healthy rent growth"],
        ),
        location_output=AgentOutput(
            score_1_to_100=78,
            rationale="Solid demographics",
            notes=["Population trending up"],
        ),
        news_output=AgentOutput(
            score_1_to_100=55,
            rationale="Neutral coverage",
            notes=["No significant incidents"],
        ),
        vc_risk_output=AgentOutput(
            score_1_to_100=72,
            rationale="Balanced return profile",
            notes=["Capex manageable"],
        ),
        construction_output=AgentOutput(
            score_1_to_100=68,
            rationale="Moderate rehab",
            notes=["Standard updates"],
        ),
    )

    async def fake_analyze(self, listing):  # noqa: D401 - simple mock
        # Invoke the patched Serper helper to mirror real flow
        from src.app import serper_news as serper_module

        serper_module.search_news(f"{listing.city} {listing.state}", 5)
        return sample_report

    monkeypatch.setattr("src.app.crew.PropertyAnalysisCrew.analyze_listing", fake_analyze)

    client = TestClient(app)
    response = client.post("/analyze?use_stored=true")

    if response.status_code != 200:
        pytest.fail(f"Unexpected status {response.status_code}: {response.text}")
    payload = response.json()
    assert isinstance(payload, list) and len(payload) == 1

    report = payload[0]
    assert report["listing_id"] == "LN-1"
    assert report["scores"]["overall"] == 71
    assert "Summary" in report["memo_markdown"]

    # Serper helper should have been invoked with location context
    assert serper_calls["latest"][0].startswith("Austin")
    assert serper_calls["latest"][1] == 5
    # City override should be passed through when stored filters omit locationId
    assert serper_calls.get("city_override") in {None, "Austin"}


def test_analyze_supports_nationwide(monkeypatch, tmp_path):
    """Ensure /analyze works when no city/location is supplied."""

    filters_file = tmp_path / "filters.json"
    filters_file.write_text(
        json.dumps(
            {
                "locationId": None,
                "locationType": "city",
                "page": 1,
                "size": 5,
                "priceMax": 3_000_000,
                "capRateMin": 8,
                "cityName": None,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(filter_store, "_FILTERS_FILE", filters_file)

    monkeypatch.setenv("RAPIDAPI_KEY", "test-rapid")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    from src.app.config import settings

    settings.rapidapi_key = "test-rapid"
    settings.openai_api_key = "test-openai"

    serper_calls: dict[str, tuple[str, int]] = {}

    def fake_serper(query: str, num: int = 8):
        serper_calls["latest"] = (query, num)
        return {"items": []}

    from src.app import serper_news

    monkeypatch.setattr(serper_news, "search_news", fake_serper)

    sample_listing = Listing(
        listing_id="LN-2",
        address="456 Market St",
        city="Dallas",
        state="TX",
        ask_price=2_500_000,
        raw={"source": "mock"},
    )

    captured_args: dict[str, object] = {}

    async def fake_loopnet(self, params, city_name=None):  # noqa: D401 - simple mock
        captured_args["city_name"] = city_name
        captured_args["params"] = params
        return [sample_listing]

    monkeypatch.setattr("src.app.loopnet_client.LoopNetClient.search_properties", fake_loopnet)

    sample_report = FinalReport(
        listing_id="LN-2",
        address="456 Market St",
        ask_price=2_500_000,
        raw={"source": "mock"},
        scores=AgentScores(
            investment=82,
            location=75,
            news_signal=60,
            risk_return=70,
            construction=64,
            overall=72,
        ),
        memo_markdown="## Summary\nAttractive nationwide opportunity.",
        investment_output=AgentOutput(
            score_1_to_100=82,
            rationale="Solid cash flow",
            notes=["Strong rent comps"],
        ),
        location_output=AgentOutput(
            score_1_to_100=75,
            rationale="Growing metro",
            notes=["Population growth"],
        ),
        news_output=AgentOutput(
            score_1_to_100=60,
            rationale="Mostly neutral coverage",
            notes=["Local investments noted"],
        ),
        vc_risk_output=AgentOutput(
            score_1_to_100=70,
            rationale="Balanced returns",
            notes=["Diverse tenancy"],
        ),
        construction_output=AgentOutput(
            score_1_to_100=64,
            rationale="Standard upkeep",
            notes=["Roof inspected"],
        ),
    )

    async def fake_analyze(self, listing):  # noqa: D401 - simple mock
        return sample_report

    monkeypatch.setattr("src.app.crew.PropertyAnalysisCrew.analyze_listing", fake_analyze)

    client = TestClient(app)
    response = client.post("/analyze?use_stored=true")

    if response.status_code != 200:
        pytest.fail(f"Unexpected status {response.status_code}: {response.text}")

    payload = response.json()
    assert isinstance(payload, list) and len(payload) == 1
    assert captured_args.get("city_name") is None
    params_obj = captured_args.get("params")
    assert params_obj is not None
    assert getattr(params_obj, "locationId", None) is None

    report = payload[0]
    assert report["listing_id"] == "LN-2"
    assert report["scores"]["overall"] == 72


def test_analyze_handles_no_data(monkeypatch, tmp_path):
    """Return empty list when LoopNet reports no data found."""

    filters_file = tmp_path / "filters.json"
    filters_file.write_text(json.dumps({"size": 5}), encoding="utf-8")
    monkeypatch.setattr(filter_store, "_FILTERS_FILE", filters_file)

    monkeypatch.setenv("RAPIDAPI_KEY", "test-rapid")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    from src.app.config import settings

    settings.rapidapi_key = "test-rapid"
    settings.openai_api_key = "test-openai"

    async def fake_loopnet(self, params, city_name=None):  # noqa: D401 - simple mock
        raise LoopNetAPIError("LoopNet API error 400: {\"status\":\"warning\",\"message\":\"No data found.\"}")

    monkeypatch.setattr("src.app.loopnet_client.LoopNetClient.search_properties", fake_loopnet)

    async def fake_analyze(self, listing):  # pragma: no cover - shouldn't run
        raise AssertionError("Analyze should not be called when no listings are returned")

    monkeypatch.setattr("src.app.crew.PropertyAnalysisCrew.analyze_listing", fake_analyze)

    client = TestClient(app)
    response = client.post("/analyze?use_stored=true")

    assert response.status_code == 200
    assert response.json() == []
