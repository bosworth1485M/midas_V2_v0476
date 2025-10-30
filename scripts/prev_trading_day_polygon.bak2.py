#!/usr/bin/env python3
# scripts/prev_trading_day_polygon.py — resolve previous TRADING day (header auth + sanitized key)

import os, sys, json, urllib.request
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parents[1]
try:
    from dotenv import load_dotenv
    # Load from project root; override any stale machine env var
    load_dotenv(ROOT / ".env", override=True)
except Exception as e:
    sys.stderr.write(f"[WARN] dotenv load failed: {e}\n")

def load_key() -> str:
    k = (os.environ.get("POLYGON_API_KEY") or "").strip().strip('"').strip("'")
    if not k:
        print("[ERR] POLYGON_API_KEY missing", file=sys.stderr)
        sys.exit(1)
    return k

def http_get_json(url: str, key: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}", "User-Agent": "midas_v2/1.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))

def previous_trading_day(date_iso: str, key: str) -> str:
    # Walk back up to 7 days; treat a 200 on grouped endpoint as a trading day
    d = datetime.fromisoformat(date_iso).date() - timedelta(days=1)
    for _ in range(7):
        u = f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{d.isoformat()}?adjusted=true"
        try:
            http_get_json(u, key)  # 200 => good day
            return d.isoformat()
        except urllib.error.HTTPError as e:
            if e.code == 401:
                print("[ERR] Polygon 401 Unauthorized — check POLYGON_API_KEY", file=sys.stderr)
                raise
        d -= timedelta(days=1)
    # Fallback (should rarely hit)
    return (datetime.fromisoformat(date_iso).date() - timedelta(days=1)).isoformat()

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()
    k = load_key()
    prev = previous_trading_day(args.date, k)
    print(f"Previous trading day for {args.date} is {prev}")