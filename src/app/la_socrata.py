"""LA City Socrata data fetcher used by crew agents."""
from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional
import requests

logger = logging.getLogger(__name__)

DEFAULT_HOST = "data.lacity.org"
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 2


class LASocrataError(RuntimeError):
    """Raised when a Socrata dataset request fails."""


@dataclass(frozen=True)
class DatasetConfig:
    """Configuration for an LA Open Data dataset."""

    dataset_id: str
    zip_fields: Iterable[tuple[str, str]]
    result_key: str


DATASETS: tuple[DatasetConfig, ...] = (
    DatasetConfig("pi9x-tg5x", [("zip_code", "eq")], "permits"),
    DatasetConfig("9w5z-rg2h", [], "inspections"),
    DatasetConfig("3f9m-afei", [("zip_code", "eq_numeric")], "coo"),
    DatasetConfig("u82d-eh7z", [("zip", "like_prefix")], "code_open"),
    DatasetConfig("rken-a55j", [("zip", "like_prefix")], "code_closed"),
)


class LASocrataTool:
    """Fetches LA City permit and code datasets via Socrata."""

    def __init__(
        self,
        *,
        app_token: Optional[str] = None,
        host: Optional[str] = None,
        session: Optional[requests.Session] = None,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
    ) -> None:
        token = app_token or os.getenv("SOCRATA_APP_TOKEN")
        if not token:
            raise LASocrataError("SOCRATA_APP_TOKEN missing; set it in .env")

        self.host = host or DEFAULT_HOST
        self.app_token = token
        self.timeout = timeout
        self.retries = retries
        self.session = session or requests.Session()
        self.user_agent = "LAPropertyDataTool/1.0"

    def fetch_all(self, address: str, zip_code: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Fetch all configured datasets for an address/zip pair."""
        if not address:
            raise ValueError("address must be provided")
        if limit <= 0:
            raise ValueError("limit must be positive")

        results: dict[str, list[dict]] = {}
        errors: dict[str, str] = {}
        counts: dict[str, int] = {}

        for cfg in DATASETS:
            try:
                rows = self._fetch_dataset(cfg, address, zip_code, limit)
            except LASocrataError as exc:  # pragma: no cover - defensive
                logger.warning("Socrata dataset %s failed: %s", cfg.dataset_id, exc)
                errors[cfg.result_key] = str(exc)
                rows = []
            results[cfg.result_key] = rows
            counts[cfg.result_key] = len(rows)

        payload = {
            "query": {"address": address, "zip": zip_code, "limit": limit},
            "results": results,
            "meta": {"counts": counts},
        }
        if errors:
            payload["errors"] = errors
        return payload

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_dataset(
        self,
        cfg: DatasetConfig,
        address: str,
        zip_code: Optional[str],
        limit: int,
    ) -> list[dict]:
        url = f"https://{self.host}/resource/{cfg.dataset_id}.json"
        params: dict[str, Any] = {"$limit": limit, "$q": address}
        where_clause = self._build_where_clause(cfg, zip_code)
        if where_clause:
            params["$where"] = where_clause

        headers = {
            "X-App-Token": self.app_token,
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }

        for attempt in range(self.retries + 1):
            response = self.session.get(url, headers=headers, params=params, timeout=self.timeout)
            if response.status_code == 403:
                params_with_token = dict(params)
                params_with_token["$$app_token"] = self.app_token
                fallback_headers = {"Accept": "application/json", "User-Agent": self.user_agent}
                response = self.session.get(
                    url,
                    headers=fallback_headers,
                    params=params_with_token,
                    timeout=self.timeout,
                )

            try:
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list):
                    return data
                logger.debug("Unexpected payload for %s: %s", cfg.dataset_id, data)
                return []
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response else None
                if status in {429, 500, 502, 503, 504} and attempt < self.retries:
                    sleep_for = 1.5 * (attempt + 1)
                    logger.debug(
                        "Retrying dataset %s after HTTP %s (sleep %.1fs)",
                        cfg.dataset_id,
                        status,
                        sleep_for,
                    )
                    time.sleep(sleep_for)
                    continue
                raise LASocrataError(
                    f"{cfg.dataset_id} request failed with status {status}"
                ) from exc
            except ValueError as exc:
                raise LASocrataError(
                    f"{cfg.dataset_id} returned invalid JSON"
                ) from exc
        return []

    def _build_where_clause(
        self,
        cfg: DatasetConfig,
        zip_code: Optional[str],
    ) -> Optional[str]:
        if not zip_code:
            return None

        escaped = zip_code.replace("'", "''")
        clauses: list[str] = []

        for field_name, mode in cfg.zip_fields:
            if not field_name:
                continue
            mode = mode or "like_prefix"
            if mode == "eq_numeric" and escaped.isdigit():
                clauses.append(f"{field_name} = {escaped}")
            elif mode == "eq":
                clauses.append(f"{field_name} = '{escaped}'")
            else:
                clauses.append(f"{field_name} like '{escaped}%'")

        if clauses:
            return " OR ".join(clauses)
        return None