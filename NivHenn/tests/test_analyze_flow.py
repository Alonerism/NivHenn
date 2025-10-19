"""End-to-end analysis flow test with mocked dependencies."""
import json

from fastapi.testclient import TestClient
import pytest

from src.main import app
from src.app import filters as filter_store
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

    async def fake_loopnet(self, params):  # noqa: D401 - simple mock
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
