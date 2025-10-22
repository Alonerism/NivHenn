"""Agent wrapper for collecting LA City Socrata records."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
import logging

from ..app.la_socrata import LASocrataTool
from ..app.models import Listing

logger = logging.getLogger(__name__)


@dataclass
class LAPropertyIngestorAgent:
    """Wraps LASocrataTool so crew members can request city records."""

    tool: LASocrataTool

    def fetch_for_listing(self, listing: Listing, *, limit: int = 50) -> dict[str, Any]:
        """Fetch Socrata records for a listing's address and zip."""
        raw_address = None
        if listing.raw and isinstance(listing.raw, dict):
            raw_address = (
                listing.raw.get("address")
                or listing.raw.get("primary_address")
                or listing.raw.get("street")
            )
        address = listing.address or raw_address
        if not address:
            raise ValueError("Listing address is required for LA property ingestion")

        raw_zip: Optional[str] = None
        if listing.raw and isinstance(listing.raw, dict):
            raw_zip = (
                listing.raw.get("zip_code")
                or listing.raw.get("zip")
                or listing.raw.get("postal_code")
            )
        zip_code: Optional[str] = listing.zip_code or raw_zip
        try:
            return self.tool.fetch_all(address=address, zip_code=zip_code, limit=limit)
        except Exception:
            logger.exception("Failed to fetch LA property data for %s", address)
            raise

    def fetch(self, *, address: str, zip_code: Optional[str] = None, limit: int = 50) -> dict[str, Any]:
        """Fetch Socrata records for an arbitrary address."""
        return self.tool.fetch_all(address=address, zip_code=zip_code, limit=limit)


def create_la_property_agent(tool: Optional[LASocrataTool] = None) -> LAPropertyIngestorAgent:
    """Factory matching other crew agent helpers."""
    return LAPropertyIngestorAgent(tool=tool or LASocrataTool())
