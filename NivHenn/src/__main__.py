"""Convenience entry point for running default analysis."""
from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace

from .cli import analyze_command, main as cli_main


def _default_args() -> SimpleNamespace:
    """Build argument namespace for running stored filters."""
    return SimpleNamespace(
        command="analyze",
        location_id=None,
        location_type=None,
        page=None,
        size=None,
        price_min=None,
        price_max=None,
        building_size_min=None,
        building_size_max=None,
        property_type=None,
        cap_rate_min=None,
        cap_rate_max=None,
        year_built_min=None,
        year_built_max=None,
        auctions=None,
        exclude_pending_sales=None,
        use_stored=True,
        persist_filters=False,
        output_dir="./out",
    )


def main() -> None:
    """Run CLI normally when args provided, otherwise use stored filters."""
    if len(sys.argv) > 1:
        cli_main()
        return

    asyncio.run(analyze_command(_default_args()))


if __name__ == "__main__":
    main()
