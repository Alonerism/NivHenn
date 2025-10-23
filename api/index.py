"""Vercel entrypoint exposing the FastAPI application."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure the project root (containing the `src` package) is on the path when
# running in Vercel's serverless environment.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MODE = os.getenv("LIGHTWEIGHT_API", "0").lower()

if MODE in {"1", "true", "lite"}:
    from src.vercel_app import app  # noqa: E402
else:
    from src.main import app  # noqa: E402

__all__ = ["app"]
