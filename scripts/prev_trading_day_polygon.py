#!/usr/bin/env python3
# scripts/prev_trading_day_polygon.py — resolve previous TRADING day
# Logic unchanged (walk back until resultsCount > 0). Auth fixed:
# - Load ROOT/.env with override=True
# - Sanitize POLYGON_API_KEY (strip quotes/whitespace)
# - Use Authorization: Bearer <key> header (no ?apiKey= in URL)

import os, sys, json, urllib.request
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parents[1]

# Load .env from project root; override any stale machine env var
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=True)
except Exception as e:
    sys.stderr.write(f"[WARN] dotenv load failed: {e}\n")

def load_key() -> str:
    k = (os.environ.get("POLYGON_API_KEY") or "").strip().strip('"').strip("'")
    if not k:
        print("[ERR] POLYGON_API_KEY missing", file=sys.stderr)
        sys.exit(1)
    return k

# URL without apiKey query — we’ll send key in the header
API_FMT = "https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{date}?adjusted=true"

def grouped_count(date_str: str, key: str) -> int:
    url = API_FMT.format(date=date_str)
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}", "User-Agent": "midas_v2/prevday/1.0"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    # Prefer resultsCount when present; fall back to len(results)
    if "resultsCount" in data:
        try:
            return int(data["resultsCount"])
        except Exception:
            pass
    results = data.get("results") or []
    return len(results) if isinstance(results, list) else 0

def previous_trading_day(date_iso: str, key: str) -> str:
    """
    Walk back from (date - 1) until the grouped endpoint returns non-empty results.
    This skips weekends/US holidays like Labor Day correctly.
    """
    d = datetime.fromisoformat(date_iso).date() - timedelta(days=1)
    for _ in range(10):  # safety bound
        try:
            if grouped_count(d.isoformat(), key) > 0:
                return d.isoformat()
        except urllib.error.HTTPError as e:
            if e.code == 401:
                print("[ERR] Polygon 401 Unauthorized — check POLYGON_API_KEY", file=sys.stderr)
                raise
        # holiday/weekend or transient => step back a day
        d -= timedelta(days=1)
    # Fallback (should rarely hit)
    return (datetime.fromisoformat(date_iso).date() - timedelta(days=1)).isoformat()

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()
    key = load_key()
    prev = previous_trading_day(args.date, key)
    print(f"Previous trading day for {args.date} is {prev}")