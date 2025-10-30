#!/usr/bin/env python3
# scripts/check_polygon_1s.py — verify Polygon 1-second aggregates are available
# - Loads ROOT/.env (override=True) and sanitizes POLYGON_API_KEY
# - Uses Authorization: Bearer <key> (no ?apiKey= in URL), identical to topgappers
# - Queries: /v2/aggs/ticker/{symbol}/range/1/second/{from_ms}/{to_ms}?adjusted=true&limit=50000
# - Exits 0 on success (>=1 result), 2 on empty result set, 1 on error

import os, sys, json, urllib.request
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime, timedelta, timezone
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None  # falls back to naive timestamp math if needed

# --- bootstrap: ensure src on path + load .env from project root (same as topgappers) ---
ROOT = Path(__file__).resolve().parents[1]
SRC  = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv(ROOT / ".env", override=True)
except Exception as e:
    sys.stderr.write(f"[WARN] dotenv load failed: {e}\n")
# --- end bootstrap ---

def load_key() -> str:
    k = (os.environ.get("POLYGON_API_KEY") or "")
    k = k.strip().strip('"').strip("'")
    if not k:
        print("[ERR] POLYGON_API_KEY missing (set it in .env)", file=sys.stderr)
        sys.exit(1)
    return k

def http_get_json(url: str, key: str):
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}", "User-Agent": "midas_v2/1s-check/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8")
        return json.loads(body), dict(r.info())

def to_epoch_ms_utc(date_iso: str, time_hms: str, tz_name: str = "America/New_York") -> int:
    """Compose {date} + {HH:MM:SS} in exchange time and return epoch ms UTC."""
    # Build naive local dt
    dt = datetime.fromisoformat(f"{date_iso}T{time_hms}")
    if ZoneInfo is not None:
        dt = dt.replace(tzinfo=ZoneInfo(tz_name))
    else:
        # Fallback: assume provided time is already local ET; treat as if it's UTC-5/UTC-4 heuristically
        # This is only a fallback; for accuracy ensure Python >=3.9.
        dt = dt.replace(tzinfo=timezone(timedelta(hours=-5)))
    return int(dt.astimezone(timezone.utc).timestamp() * 1000)

def human(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()

def main():
    ap = ArgumentParser(description="Verify Polygon 1-second aggregates availability")
    ap.add_argument("--symbol", "-s", required=False, default="STTK", help="Ticker symbol (e.g., STTK)")
    ap.add_argument("--date", "-d", required=True, help="Session date YYYY-MM-DD (exchange date)")
    ap.add_argument("--start", default="09:30:00", help="Start time (America/New_York) HH:MM:SS (default 09:30:00)")
    ap.add_argument("--window-seconds", type=int, default=60, help="Window length in seconds (default 60)")
    ap.add_argument("--print-samples", type=int, default=5, help="How many rows to preview (default 5)")
    args = ap.parse_args()

    key = load_key()

    start_ms = to_epoch_ms_utc(args.date, args.start)
    end_ms   = start_ms + args.window_seconds * 1000

    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{args.symbol.upper()}"
        f"/range/1/second/{start_ms}/{end_ms}?adjusted=true&limit=50000"
    )

    print(f"[INFO] Querying 1s bars for {args.symbol.upper()} {args.date} "
          f"{args.start} +{args.window_seconds}s "
          f"({human(start_ms)}Z -> {human(end_ms)}Z)")
    print(f"[URL ] {url}")

    try:
        data, headers = http_get_json(url, key)
    except Exception as e:
        print(f"[ERR ] HTTP error: {e}", file=sys.stderr)
        sys.exit(1)

    status = data.get("status")
    rcnt = data.get("resultsCount", 0)
    results = data.get("results") or []

    print(f"[HEAD] X-Rate-Limit-Remaining: {headers.get('X-Rate-Limit-Remaining', 'n/a')}")
    print(f"[RESP] status={status} resultsCount={rcnt}")

    if rcnt == 0 or not results:
        print("[WARN] No 1-second aggregates returned for the given window.")
        sys.exit(2)

    # Preview a few rows
    n = max(0, min(args.print_samples, len(results)))
    if n:
        print(f"\n[PREVIEW] First {n} rows (t=epoch_ms, o/h/l/c, v):")
        for r in results[:n]:
            t = r.get("t"); o = r.get("o"); h = r.get("h"); l = r.get("l"); c = r.get("c"); v = r.get("v")
            print(f"  t={t} ({human(int(t))}Z)  o={o} h={h} l={l} c={c} v={v}")

    # Simple sanity checks
    if any(k not in results[0] for k in ("t", "o", "h", "l", "c", "v")):
        print("[ERR ] Malformed 1s aggregate payload.", file=sys.stderr)
        sys.exit(1)

    print("\n[SUCCESS] Polygon returned 1-second aggregates for the requested window.")
    sys.exit(0)

if __name__ == "__main__":
    main()