# scripts/sanity_micro_slice.py
"""
Sanity check for Polygon 1s->5s micro window using your loaders.

- Finds project root (.. from scripts/) and adds src/ to PYTHONPATH
- Uses pandas-only micro slicer (get_micro_slice_cached)
- Uses polygon_1s_loader (Authorization: Bearer <POLYGON_API_KEY> from project-root .env)
- Prints counts and a couple of sample rows

Usage (UTC minute; 13:41:00 UTC ≈ 9:41am ET):
  python scripts/sanity_micro_slice.py --symbol STTK --date 2025-08-05 --minute 13:41:00 --seconds 60 --resolution 5s
"""

import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

# 1) Locate project root: <root>/scripts/.. -> <root>
ROOT = Path(__file__).resolve().parents[1]
SRC  = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# 2) Imports: micro slicer + Polygon 1s loader
from midas_v2.data.one_sec_loader import get_micro_slice_cached
from midas_v2.data.polygon_micro_loader import polygon_1s_loader

def parse_args():
    p = argparse.ArgumentParser(
        description="Fetch Polygon 1s bars and build 5s/1s micro windows (verbose)"
    )
    p.add_argument("--symbol", default="STTK", help="Ticker symbol")
    p.add_argument("--date", default="2025-08-05", help="Session date (YYYY-MM-DD, UTC)")
    # Use a REGULAR-SESSION UTC minute; 13:41:00 UTC ≈ 09:41am ET.
    p.add_argument("--minute", default="13:41:00", help="Minute-close time (HH:MM:SS, UTC)")
    p.add_argument("--seconds", type=int, default=60, help="Window length after the minute close")
    p.add_argument("--resolution", default="5s", choices=["1s", "5s"], help="Micro window resolution")
    return p.parse_args()

def main():
    args = parse_args()

    # Build minute-close timestamp in UTC
    try:
        dt_utc = datetime.fromisoformat(f"{args.date}T{args.minute}+00:00")
    except ValueError as e:
        raise SystemExit(f"Invalid --date/--minute: {e}")
    epoch = int(dt_utc.replace(tzinfo=timezone.utc).timestamp())

    print("=== sanity_micro_slice ===")
    print("Project root:", ROOT)
    print("Symbol:", args.symbol)
    print("Minute close (UTC):", dt_utc.isoformat())
    print("Window seconds:", args.seconds)
    print("Resolution:", args.resolution)
    print("POLYGON_API_KEY present:", bool(os.environ.get("POLYGON_API_KEY")))

    # Fetch micro window via pandas-only slicer + Polygon 1s loader
    bars = get_micro_slice_cached(
        symbol=args.symbol,
        minute_close_ts=epoch,   # UTC epoch seconds of the minute close
        seconds=args.seconds,
        resolution=args.resolution,  # "5s" baseline or "1s"
        loader=polygon_1s_loader,    # reads project-root .env; Authorization: Bearer <key>
    )

    print(f"Bars returned ({args.resolution}):", len(bars))
    if bars[:1]:
        print("First bar:", bars[0])
    if len(bars) > 1:
        print("Second bar:", bars[1])

    # Also compare raw 1s if you requested 5s
    if args.resolution == "5s":
        bars_1s = get_micro_slice_cached(
            symbol=args.symbol,
            minute_close_ts=epoch,
            seconds=args.seconds,
            resolution="1s",
            loader=polygon_1s_loader,
        )
        print("Bars returned (1s):", len(bars_1s))
        if bars_1s[:1]:
            print("1s first:", bars_1s[0])

if __name__ == "__main__":
    if not os.environ.get("POLYGON_API_KEY"):
        print("NOTE: POLYGON_API_KEY not found in env. Ensure project-root .env contains it.")
    main()