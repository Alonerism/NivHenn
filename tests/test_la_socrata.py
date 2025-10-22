"""Tests for LASocrataTool and LAPropertyIngestorAgent."""
from __future__ import annotations

import pytest
import requests

from src.app.la_socrata import LASocrataTool, LASocrataError
from src.agents.la_property_ingestor import LAPropertyIngestorAgent
from src.app.models import Listing


class FakeResponse:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = ""

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    def get(self, url, headers=None, params=None, timeout=None):  # noqa: D401 - test helper
        dataset = url.rsplit("/", 1)[-1].split(".")[0]
        self.calls.append((dataset, params))
        payload = [{"dataset": dataset, "where": params.get("$where")}] if params else [{"dataset": dataset}]
        return FakeResponse(200, payload)


def test_fetch_all_builds_expected_where_clauses():
    session = FakeSession()
    tool = LASocrataTool(app_token="token", session=session, host="data.lacity.org")

    payload = tool.fetch_all("5020 Noble", zip_code="91403", limit=5)

    assert payload["query"] == {"address": "5020 Noble", "zip": "91403", "limit": 5}
    assert payload["results"]["permits"][0]["dataset"] == "pi9x-tg5x"
    assert payload["meta"]["counts"]["permits"] == 1

    params_by_dataset = {dataset: params for dataset, params in session.calls}
    assert params_by_dataset["pi9x-tg5x"]["$where"] == "zip_code = '91403'"
    assert "$where" not in params_by_dataset["9w5z-rg2h"]
    assert params_by_dataset["3f9m-afei"]["$where"] == "zip_code = 91403"
    assert params_by_dataset["u82d-eh7z"]["$where"] == "zip like '91403%'"
    assert params_by_dataset["rken-a55j"]["$where"] == "zip like '91403%'"


def test_tool_requires_token(monkeypatch):
    monkeypatch.delenv("SOCRATA_APP_TOKEN", raising=False)
    with pytest.raises(LASocrataError):
        LASocrataTool()


def test_agent_uses_tool_for_listing(monkeypatch):
    captured: dict[str, tuple[str, str | None, int]] = {}

    class DummyTool:
        def fetch_all(self, address: str, zip_code: str | None = None, limit: int = 50):  # noqa: D401 - simple stub
            captured["call"] = (address, zip_code, limit)
            return {"results": {"permits": []}}

    listing = Listing(listing_id="LN-123", address="5020 Noble", city="Los Angeles", state="CA", raw={})
    agent = LAPropertyIngestorAgent(tool=DummyTool())

    output = agent.fetch_for_listing(listing, limit=10)
    assert output == {"results": {"permits": []}}
    assert captured["call"] == ("5020 Noble", None, 10)

    arbitrary = agent.fetch(address="123 Test St", zip_code="90001", limit=3)
    assert arbitrary == {"results": {"permits": []}}
    assert captured["call"] == ("123 Test St", "90001", 3)