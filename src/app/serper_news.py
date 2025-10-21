"""Minimal Serper news client used by the News agent."""
from __future__ import annotations

import os
import random
import time
from typing import Any, Dict, List

import httpx

SERPER_NEWS_ENDPOINT = "https://google.serper.dev/news"
_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 3


def _extract_items(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize Serper payload to the expected list of items."""
    candidates = payload.get("news") or payload.get("items") or []
    normalized: List[Dict[str, Any]] = []
    for raw in candidates:
        normalized.append(
            {
                "title": raw.get("title"),
                "date": raw.get("date") or raw.get("publishedDate"),
                "source": raw.get("source"),
                "link": raw.get("link"),
                "snippet": raw.get("snippet") or raw.get("description"),
            }
        )
    return normalized


def search_news(query: str, num: int = 8) -> Dict[str, Any]:
    """Search Serper news API with basic retry and normalization."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return {"items": [], "note": "SERPER_API_KEY missing"}

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": num}

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = httpx.post(
                SERPER_NEWS_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=20.0,
            )
            if response.status_code in _RETRY_STATUS_CODES:
                response.raise_for_status()
            response.raise_for_status()
            data = response.json()
            return {"items": _extract_items(data)}
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response else "unknown"
            if status in _RETRY_STATUS_CODES and attempt < _MAX_ATTEMPTS:
                sleep_for = 2 ** attempt + random.uniform(0, 1)
                time.sleep(sleep_for)
                continue
            return {"items": [], "note": f"Serper error {status}"}
        except Exception as exc:  # pragma: no cover - defensive
            if attempt < _MAX_ATTEMPTS:
                sleep_for = 2 ** attempt + random.uniform(0, 1)
                time.sleep(sleep_for)
                continue
            return {"items": [], "note": str(exc)}

    return {"items": [], "note": "Unable to fetch Serper news"}
