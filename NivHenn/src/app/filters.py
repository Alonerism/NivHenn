"""Persistent filter state management for LoopNet searches."""
from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any, Dict

from pydantic import ValidationError

from .models import SearchParams

_FILTERS_FILE = Path(__file__).resolve().parents[2] / "config" / "filters.json"
_LOCK = Lock()
_DEFAULT_FILTERS = SearchParams(
    locationId="Los Angeles, CA",
    locationType="city",
    page=1,
    size=20,
)


def _ensure_storage() -> None:
    """Make sure the filters directory exists."""
    _FILTERS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _write_filters(params: SearchParams) -> None:
    """Write filters to disk in a thread-safe manner."""
    _ensure_storage()
    with _LOCK:
        _FILTERS_FILE.write_text(
            json.dumps(params.model_dump(exclude_none=True), indent=2, sort_keys=True),
            encoding="utf-8",
        )


def load_filters() -> SearchParams:
    """Load current filters, falling back to defaults when absent/invalid."""
    _ensure_storage()
    with _LOCK:
        if not _FILTERS_FILE.exists():
            _write_filters(_DEFAULT_FILTERS)
            return _DEFAULT_FILTERS.model_copy(deep=True)
        try:
            raw = json.loads(_FILTERS_FILE.read_text(encoding="utf-8") or "{}")
            params = SearchParams(**raw)
        except (json.JSONDecodeError, ValidationError):
            _write_filters(_DEFAULT_FILTERS)
            params = _DEFAULT_FILTERS.model_copy(deep=True)
    return params


def load_city_name() -> str | None:
    """Load cityName from filters.json (if present) for city resolution."""
    _ensure_storage()
    with _LOCK:
        if not _FILTERS_FILE.exists():
            return None
        try:
            raw = json.loads(_FILTERS_FILE.read_text(encoding="utf-8") or "{}")
            return raw.get("cityName")
        except (json.JSONDecodeError, KeyError):
            return None


def save_filters(params: SearchParams) -> SearchParams:
    """Persist validated filters and return the stored value."""
    _write_filters(params)
    return params


def update_filters(partial: Dict[str, Any]) -> SearchParams:
    """Apply a partial update to stored filters and persist the result."""
    current = load_filters().model_dump()
    for key, value in partial.items():
        if value == "":
            value = None
        current[key] = value
    try:
        params = SearchParams(**current)
    except ValidationError as exc:  # pragma: no cover - re-raise for FastAPI to handle
        raise ValueError(str(exc)) from exc
    return save_filters(params)


def reset_filters() -> SearchParams:
    """Restore default filters and persist them."""
    _write_filters(_DEFAULT_FILTERS)
    return _DEFAULT_FILTERS.model_copy(deep=True)


__all__ = [
    "load_filters",
    "save_filters",
    "update_filters",
    "reset_filters",
    "load_city_name",
    "_FILTERS_FILE",
]
