# src/midas_v2/data/polygon_micro_loader.py
from __future__ import annotations

import os
import sys
import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable

# -----------------------------------------------------------------------------
# Bootstrap: add src/ to PYTHONPATH and load .env from *project root*
# (This mirrors your working pattern from scripts that hit Polygon.)
# -----------------------------------------------------------------------------
# File is at: <project_root>/src/midas_v2/data/polygon_micro_loader.py
# project root is three levels up from here.
ROOT = Path(__file__).resolve().parents[3]  # <-- IMPORTANT: points to project root
SRC  = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Load .env (optional; env may already be set by your shell)
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv(ROOT / ".env", override=True)
except Exception:
    # Non-fatal: if dotenv is missing, caller can rely on environment variables
    pass


# -----------------------------------------------------------------------------
# Internal helpers (key handling + HTTP)
# -----------------------------------------------------------------------------
def _load_key() -> str:
    """
    Read POLYGON_API_KEY from environment, strip quotes/whitespace.
    Raise if missing. Never print or log the key.
    """
    k = (os.environ.get("POLYGON_API_KEY") or "").strip().strip('"').strip("'")
    if not k:
        raise RuntimeError(
            "POLYGON_API_KEY missing. Set it in your project-root .env or process environment."
        )
    return k


def _http_get_json(url: str, key: str) -> Dict:
    """
    GET JSON with header-based auth (Authorization: Bearer <key>).
    Do NOT put the key in the query string.
    """
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {key}",  # header auth (matches your policy)
            "User-Agent": "midas_v2/1.0",
            "Accept": "application/json",
        },
        method="GET",
    )
    # Keep a sensible timeout; caller should catch exceptions upstream if desired.
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return json.loads(data.decode("utf-8"))


def _to_ms(epoch_seconds: int) -> int:
    """Seconds (UTC) -> milliseconds (UTC) for Polygon v2 aggs path."""
    return int(epoch_seconds) * 1000


# -----------------------------------------------------------------------------
# Public loader
# -----------------------------------------------------------------------------
def polygon_1s_loader(symbol: str, minute_close_epoch: int, seconds: int) -> Iterable[Dict]:
    """
    Yield raw *1-second* bars from Polygon for the window:
      [minute_close_epoch, minute_close_epoch + seconds)

    Output schema per row (dict):
      { "ts": epoch_seconds_utc, "open": float, "high": float, "low": float, "close": float, "volume": float }

    Notes:
    - Auth via Authorization header only (no apiKey in URL).
    - Endpoint: /v2/aggs/ticker/{symbol}/range/1/second/{from_ms}/{to_ms}
    - Sorted ascending.
    """
    key = _load_key()

    start_ms = _to_ms(int(minute_close_epoch))
    end_ms   = _to_ms(int(minute_close_epoch) + int(seconds))

    # Polygon v2 per-second aggregates
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/second/"
        f"{start_ms}/{end_ms}?adjusted=true&sort=asc&limit=50000"
    )

    data = _http_get_json(url, key)
    results = data.get("results") or []

    for r in results:
        # Polygon fields: t (ms), o,h,l,c,v
        yield {
            "ts": int(r.get("t", 0) // 1000),
            "open": float(r.get("o", 0.0)),
            "high": float(r.get("h", 0.0)),
            "low":  float(r.get("l", 0.0)),
            "close":float(r.get("c", 0.0)),
            "volume": float(r.get("v", 0.0)),
        }


# -----------------------------------------------------------------------------
# Optional: tiny CLI dev check (disabled by default)
# To use:
#   python -m midas_v2.data.polygon_micro_loader STTK 2025-08-05T13:41:00Z 60
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    import time

    ap = argparse.ArgumentParser(description="Quick dev check for Polygon 1s loader")
    ap.add_argument("symbol", help="Ticker, e.g., STTK")
    ap.add_argument("minute_close_utc", help="UTC minute close, e.g., 2025-08-05T13:41:00Z")
    ap.add_argument("seconds", type=int, help="Window seconds, e.g., 60")
    args = ap.parse_args()

    # Parse UTC time
    minute_dt = datetime.fromisoformat(args.minute_close_utc.replace("Z", "+00:00"))
    minute_epoch = int(minute_dt.timestamp())

    print("Symbol:", args.symbol)
    print("Minute close (UTC):", minute_dt.isoformat())
    print("Window seconds:", args.seconds)
    print("POLYGON_API_KEY present:", bool(os.environ.get("POLYGON_API_KEY")))
    t0 = time.time()
    rows = list(polygon_1s_loader(args.symbol, minute_epoch, args.seconds))
    t1 = time.time()
    print(f"Fetched {len(rows)} rows in {t1 - t0:.2f}s")
    if rows[:1]:
        print("First row:", rows[0])