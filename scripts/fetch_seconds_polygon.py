"""
TWCS Phase 4 – 1-Second Polygon Data Ingestion (v0.8.1.0.6)

Fetches 1-second aggregate bars from Polygon.io for TWCS microstructure analysis.
Writes CSVs to data/samples/sample_1s_YYYY-MM-DD_SYMBOL.csv

This script follows the same pattern as fetch_minutes_polygon.py but operates at
second-level granularity for detailed entry/exit window analysis.
"""
# v0.8.1.0.6: TWCS Phase 4 1-second Polygon ingestion

# --- bootstrap: ensure src on path + load .env from project root ---  # v0.8.1.0.6
import os
import sys
import argparse
import pathlib
import csv
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta, time, timezone

ROOT = Path(__file__).resolve().parents[1]  # v0.8.1.0.6
SRC = ROOT / "src"  # v0.8.1.0.6
if str(SRC) not in sys.path:  # v0.8.1.0.6
    sys.path.insert(0, str(SRC))  # v0.8.1.0.6
try:  # v0.8.1.0.6
    from dotenv import load_dotenv  # pip install python-dotenv  # v0.8.1.0.6
    load_dotenv(ROOT / ".env", override=True)  # v0.8.1.0.6
except Exception as e:  # v0.8.1.0.6
    sys.stderr.write(f"[WARN] dotenv load failed: {e}\n")  # v0.8.1.0.6
# --- end bootstrap ---  # v0.8.1.0.6

try:  # v0.8.1.0.6
    from zoneinfo import ZoneInfo  # Python 3.9+  # v0.8.1.0.6
except Exception as e:  # v0.8.1.0.6
    raise SystemExit("[ERR] zoneinfo not available (need Python 3.9+)") from e  # v0.8.1.0.6

NY = ZoneInfo("America/New_York")  # v0.8.1.0.6


def load_key():  # v0.8.1.0.6
    """Load and sanitize Polygon API key from environment. v0.8.1.0.6"""
    k = (os.environ.get("POLYGON_API_KEY") or "").strip().strip('"').strip("'")  # v0.8.1.0.6
    if not k:  # v0.8.1.0.6
        raise SystemExit("[ERR] POLYGON_API_KEY missing (set env var or add to .env)")  # v0.8.1.0.6
    return k  # v0.8.1.0.6


def fetch_second_bars_polygon(
    symbol: str,
    date_str: str,
    session: str = "rth",
    key: str = None,  # v0.8.1.0.6: key now passed as parameter
) -> list[dict]:
    """
    Fetch 1-second bars from Polygon for a single symbol/date.
    
    v0.8.1.0.6: Returns list of candle dicts with keys: t, o, h, l, c, v
    Uses Bearer auth pattern matching fetch_minutes_polygon.py
    """
    if key is None:  # v0.8.1.0.6
        key = load_key()  # v0.8.1.0.6
    
    # Build time range
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        print(f"[ERROR] Invalid date format '{date_str}': {e}", file=sys.stderr)
        return []
    
    # RTH session: 09:30-16:00 ET
    if session == "rth":
        rth_start = time(9, 30)  # v0.8.1.0.6
        rth_end = time(16, 0)  # v0.8.1.0.6
    
    # Polygon expects date range (from/to) - use same day for both  # v0.8.1.0.6
    to_date = (dt + timedelta(days=1)).strftime("%Y-%m-%d")  # v0.8.1.0.6
    
    # Build URL with Bearer auth (no apiKey param)  # v0.8.1.0.6
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/second/{date_str}/{to_date}?adjusted=true&sort=asc&limit=50000"  # v0.8.1.0.6
    
    candles = []
    
    try:
        # Use Bearer auth matching fetch_minutes_polygon.py  # v0.8.1.0.6
        req = urllib.request.Request(  # v0.8.1.0.6
            url,  # v0.8.1.0.6
            headers={  # v0.8.1.0.6
                "Authorization": f"Bearer {key}",  # v0.8.1.0.6
                "User-Agent": "midas_v2/seconds/1.0"  # v0.8.1.0.6
            }  # v0.8.1.0.6
        )  # v0.8.1.0.6
        
        with urllib.request.urlopen(req, timeout=60) as r:  # v0.8.1.0.6
            data = json.loads(r.read().decode("utf-8"))  # v0.8.1.0.6
        
        rows = data.get("results") or []  # v0.8.1.0.6
        
        for x in rows:  # v0.8.1.0.6
            # Convert UNIX ms (UTC) to ET  # v0.8.1.0.6
            ts_utc = datetime.fromtimestamp(x["t"] / 1000, tz=timezone.utc)  # v0.8.1.0.6
            ts_et = ts_utc.astimezone(NY)  # v0.8.1.0.6
            
            # Optional RTH filter  # v0.8.1.0.6
            if session == "rth":  # v0.8.1.0.6
                tt = ts_et.timetz()  # v0.8.1.0.6
                tt_naive = time(tt.hour, tt.minute, tt.second)  # v0.8.1.0.6
                if not (rth_start <= tt_naive <= rth_end):  # v0.8.1.0.6
                    continue  # v0.8.1.0.6
            
            candle = {
                "t": ts_et.strftime("%Y-%m-%dT%H:%M:%S"),  # v0.8.1.0.6: ISO format with seconds
                "o": float(x["o"]),
                "h": float(x["h"]),
                "l": float(x["l"]),
                "c": float(x["c"]),
                "v": float(x["v"]),
            }
            candles.append(candle)
    
    except Exception as exc:
        print(f"[WARN] v0.8.1.0.6: Failed to fetch 1s bars for {symbol} on {date_str}: {exc}", file=sys.stderr)
        return []
    
    return candles


def write_second_csv(candles: list[dict], out_path: Path) -> None:
    """
    Write 1-second candles to CSV.
    
    v0.8.1.0.6: CSV columns: t, o, h, l, c, v
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["t", "o", "h", "l", "c", "v"])
        writer.writeheader()
        writer.writerows(candles)
    
    print(f"[INFO] v0.8.1.0.6: Wrote {len(candles)} second-bars to {out_path}")


def main():
    """
    Main CLI entry point for 1-second Polygon ingestion.
    
    v0.8.1.0.6: Fetches second bars for all symbols in universe file.
    """
    parser = argparse.ArgumentParser(
        description="Fetch 1-second Polygon bars for TWCS Phase 4 (v0.8.1.0.6)"
    )
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    parser.add_argument("--session", default="rth", help="Session: 'rth' or 'full' (default: rth)")
    parser.add_argument("--universe", required=True, help="Path to universe.txt file")
    parser.add_argument("--out-dir", default="data/samples", help="Output directory (default: data/samples)")
    
    args = parser.parse_args()
    
    key = load_key()  # v0.8.1.0.6: load key once at startup
    date_str = args.date
    session = args.session
    universe_path = Path(args.universe)
    out_dir = Path(args.out_dir)
    
    # Validate date format
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"[ERROR] Invalid date format: {date_str}. Use YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)
    
    # Load universe
    if not universe_path.exists():
        print(f"[ERROR] Universe file not found: {universe_path}", file=sys.stderr)
        sys.exit(1)
    
    with universe_path.open("r", encoding="utf-8") as fh:
        symbols = [line.strip() for line in fh if line.strip()]
    
    print(f"[INFO] v0.8.1.0.6: Fetching 1-second bars for {len(symbols)} symbols on {date_str} ({session} session)")
    
    wrote = empty = failed = 0  # v0.8.1.0.6: match minutes fetcher stats
    
    # Fetch and write CSVs for each symbol
    for idx, symbol in enumerate(symbols, start=1):
        print(f"[{idx}/{len(symbols)}] Fetching {symbol}...")
        
        try:
            candles = fetch_second_bars_polygon(symbol, date_str, session, key=key)  # v0.8.1.0.6: pass key
            
            if not candles:  # v0.8.1.0.6
                empty += 1  # v0.8.1.0.6
                print(f"[WARN] no seconds for {symbol}")  # v0.8.1.0.6
                continue  # v0.8.1.0.6: skip writing empty CSV
            
            out_csv = out_dir / f"sample_1s_{date_str}_{symbol}.csv"
            write_second_csv(candles, out_csv)
            wrote += 1  # v0.8.1.0.6
            
            # Rate limit: Polygon free tier allows 5 requests/minute
            # Sleep 12 seconds between requests (5 req/min)
            # Note: minutes fetcher doesn't sleep; adjust if needed  # v0.8.1.0.6
            import time  # v0.8.1.0.6
            if idx < len(symbols):
                time.sleep(12)
        
        except Exception as exc:
            failed += 1  # v0.8.1.0.6
            print(f"[WARN] {symbol} failed: {exc}", file=sys.stderr)  # v0.8.1.0.6: match minutes pattern
    
    print(f"Done. wrote={wrote} empty={empty} failed={failed}")  # v0.8.1.0.6: match minutes output
    print(f"[INFO] v0.8.1.0.6: 1-second ingestion complete for {date_str}")


if __name__ == "__main__":
    main()
