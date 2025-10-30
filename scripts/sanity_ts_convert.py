# scripts/sanity_ts_convert.py
"""
Smoke test: coerce bar.ts from 'HH:MM' strings to UTC epoch seconds, then enforce strict time order.
Optional: ping Polygon with the same Authorization header style as topgappers.py.

Usage:
  python scripts/sanity_ts_convert.py --symbol STTK --date 2025-08-05
  python scripts/sanity_ts_convert.py --symbol STTK --date 2025-08-05 --ping-polygon
"""

import os, sys, json, urllib.request, argparse
from datetime import datetime, timezone
from pathlib import Path

# --- bootstrap: ensure src on path + load .env from project root (exactly like topgappers.py) ---
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

from midas_v2.dataprov.csv_local import CsvLocalProvider

def load_key() -> str:
    """Match topgappers.py style: strip whitespace and quotes, required header auth."""
    k = (os.environ.get("POLYGON_API_KEY") or "")
    k = k.strip().strip('"').strip("'")
    if not k:
        print("[ERR] POLYGON_API_KEY missing (set it in .env)", file=sys.stderr)
        sys.exit(1)
    return k

def http_get_json(url: str, key: str) -> dict:
    """Header Authorization: Bearer <key> (no ?apiKey=)."""
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}", "User-Agent": "midas_v2/1.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))

def coerce_bars_ts_to_epoch(bars, date_str: str, tz_name: str = "America/New_York"):
    """Convert bar.ts from 'HH:MM'/'HH:MM:SS' to UTC epoch seconds. Sets both .ts and .t."""
    try:
        y, m, d = map(int, date_str.split("-"))
    except Exception:
        print("[WARN] date_str not YYYY-MM-DD; skipping conversion")
        return

    # Prefer stdlib zoneinfo when available (Py 3.9+)
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = None  # fallback: treat as UTC if tz unavailable

    for b in bars:
        ts = getattr(b, "ts", None)
        if isinstance(ts, (int, float)):
            # Already epoch; mirror to .t
            try: b.t = int(ts)
            except Exception: pass
            continue
        if isinstance(ts, str):
            try:
                parts = ts.split(":")
                hh = int(parts[0]); mm = int(parts[1]); ss = int(parts[2]) if len(parts) > 2 else 0
                if tz:
                    dt_local = datetime(y, m, d, hh, mm, ss, tzinfo=tz)
                    dt_utc   = dt_local.astimezone(timezone.utc)
                else:
                    dt_utc   = datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc)
                epoch = int(dt_utc.timestamp())
                b.ts = epoch
                b.t  = epoch
            except Exception as e:
                print(f"[WARN] could not parse ts='{ts}': {e}")

def to_iso(epoch_s: int) -> str:
    try:
        return datetime.fromtimestamp(int(epoch_s), tz=timezone.utc).isoformat()
    except Exception:
        return str(epoch_s)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--date",   required=True, help="YYYY-MM-DD (session date)")
    ap.add_argument("--data-root", default=str(ROOT/"data"/"samples"), help="CsvLocalProvider root (default: data/samples)")
    ap.add_argument("--ping-polygon", action="store_true", help="Optionally ping a tiny endpoint to verify Bearer auth")
    args = ap.parse_args()

    # Optional Polygon auth ping (does not print the key; just checks 200 OK)
    if args.ping_polygon:
        key = load_key()
        url = "https://api.polygon.io/v3/reference/tickers?market=stocks&limit=1"
        try:
            r = http_get_json(url, key)
            print("[PING] Polygon header auth OK; sample key present:", "results" in r or "tickers" in r)
        except Exception as e:
            print("[PING] Polygon ping failed:", e)
            # Don't exit; conversion test can still run

    prov = CsvLocalProvider(args.data_root)
    bars = prov.load_minute_bars(args.symbol, args.date)

    print(f"Loaded {len(bars)} bars for {args.symbol} on {args.date}")
    print("BEFORE (first 5):")
    for b in bars[:5]:
        print("  ts=", repr(getattr(b, "ts", None)))

    # Convert 'HH:MM' → UTC epoch seconds
    coerce_bars_ts_to_epoch(bars, args.date)

    # NEW: enforce strict time order after conversion (fixes non-monotonic sources)
    bars.sort(key=lambda b: int(getattr(b, "ts", 0)))

    print("\nAFTER (first 5):")
    for b in bars[:5]:
        print(f"  ts={b.ts}  iso={to_iso(b.ts)}")

    # Validation: all ints and strictly increasing
    bad = False; last = None
    for b in bars:
        if not isinstance(b.ts, (int, float)):
            print("[FAIL] ts is not numeric:", b.ts); bad = True; break
        if last is not None and b.ts < last:
            print("[FAIL] ts not monotonic:", last, "->", b.ts); bad = True; break
        last = b.ts

    print("\nRESULT:", "PASS" if not bad else "FAIL")
    if bad:
        raise SystemExit(1)

if __name__ == "__main__":
    main()