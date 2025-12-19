"""
v0.8.1.0.0: Lightweight Polygon.io data loader for TWCS and scanners.
Provides helpers to load API key, perform authenticated GETs, and fetch
1-minute and 1-second aggregate bars. Matches scripts/topgappers.py
semantics for .env loading, key sanitization, and Authorization header.
"""

# v0.8.1.0.0: Standard imports
from __future__ import annotations
import os
import sys
import json
import urllib.request
from pathlib import Path
from typing import Any, Dict

# v0.8.1.0.0: dotenv import if available
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None  # type: ignore

# v0.8.1.0.0: Project root (src/midas_v2/dataio -> project root)
ROOT = Path(__file__).resolve().parents[2]

# v0.8.1.0.0: Initialize .env if possible (do not fail import)
def _init_dotenv() -> None:
    """v0.8.1.0.0: Load .env from project root if python-dotenv is available."""
    try:
        if load_dotenv is None:
            print("[WARN] python-dotenv not installed; skipping .env load", file=sys.stderr)
            return
        # load_dotenv accepts a path-like; override=True to prefer .env values
        load_dotenv(str(ROOT / ".env"), override=True)
    except Exception as e:
        # v0.8.1.0.0: warn but continue
        print(f"[WARN] failed to load .env: {e}", file=sys.stderr)


# initialize at import time (safe)
_init_dotenv()

# v0.8.1.0.0: Polygon key loader for TWCS and scanners.
def load_polygon_key() -> str:
    """
    v0.8.1.0.0: Load and sanitize POLYGON_API_KEY from environment/.env.
    Must match scripts/topgappers.py semantics exactly.
    """
    k = (os.environ.get("POLYGON_API_KEY") or "")
    # sanitize: strip whitespace and optional surrounding quotes
    k = k.strip().strip('"').strip("'")
    if not k:
        print("[ERR] POLYGON_API_KEY missing (set it in .env)", file=sys.stderr)
        sys.exit(1)
    return k


# v0.8.1.0.0: Perform a GET request to Polygon and return parsed JSON.
def polygon_get_json(url: str, key: str) -> Dict[str, Any]:
    """
    v0.8.1.0.0: Perform an authenticated GET request to Polygon and return parsed JSON.
    Uses Authorization: Bearer <key> header and a simple User-Agent.
    """
    headers = {
        "Authorization": f"Bearer {key}",
        "User-Agent": "midas_v2/1.0",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            try:
                return json.loads(raw.decode("utf-8"))
            except Exception as je:
                print(f"[ERR] Failed to parse JSON from {url}: {je}", file=sys.stderr)
                return {}
    except Exception as e:
        print(f"[ERR] Polygon request failed for {url}: {e}", file=sys.stderr)
        return {}


# v0.8.1.0.0: Fetch 1-minute aggregate bars for a symbol on a given date.
def fetch_agg_bars_minute(symbol: str, date_iso: str, key: str) -> Dict[str, Any]:
    """
    v0.8.1.0.0: Fetch 1-minute aggregate bars for a symbol on a given date.
    Returns raw JSON from Polygon. Uses Authorization header only (no apiKey query).
    """
    # Build Polygon v2 aggs URL (no apiKey query parameter)
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{date_iso}/{date_iso}"
    return polygon_get_json(url, key)


# v0.8.1.0.0: Fetch 1-second aggregate bars for a symbol on a given date.
def fetch_agg_bars_second(symbol: str, date_iso: str, key: str) -> Dict[str, Any]:
    """
    v0.8.1.0.0: Fetch 1-second aggregate bars for a symbol on a given date.
    Returns raw JSON from Polygon. Uses Authorization header only (no apiKey query).
    """
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/second/{date_iso}/{date_iso}"
    return polygon_get_json(url, key)


# v0.8.1.0.0: Public API
__all__ = [
    "load_polygon_key",
    "polygon_get_json",
    "fetch_agg_bars_minute",
    "fetch_agg_bars_second",
]