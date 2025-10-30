#!/usr/bin/env python3
"""
Standalone smoke test for the 1s micro-confirm gate (NO backtester, NO Polygon).
Usage:
  python scripts\smoke_micro_strategy.py --case pass --minute 09:31 --date 2025-08-05
  python scripts\smoke_micro_strategy.py --case fail --minute 09:31 --date 2025-08-05
"""
from __future__ import annotations
import os, sys, argparse
from datetime import datetime, timedelta, timezone
import pandas as pd

# Make src importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC  = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from midas_v2.micro.micro_confirm import one_sec_continuation_ok

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", choices=["pass","fail"], default="pass")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (exchange ET)")
    ap.add_argument("--minute", default="09:31", help="Decision minute HH:MM (ET)")
    ap.add_argument("--seconds-window", type=int, default=4)
    ap.add_argument("--min-green-count", type=int, default=3)
    ap.add_argument("--min-last-delta-bps", type=int, default=5)
    ap.add_argument("--max-red-body-bps", type=int, default=10)
    ap.add_argument("--min-avg-body-bps", type=int, default=15)
    ap.add_argument("--min-required-rows", type=int, default=3)
    return ap.parse_args()

def et_minute_open_to_utc_ms(date_str: str, minute_hhmm: str) -> int:
    """Convert ET minute open -> epoch-ms UTC (DST-safe on 3.9+ with zoneinfo)."""
    try:
        from zoneinfo import ZoneInfo
        ET = ZoneInfo("America/New_York")
    except Exception:
        ET = timezone(timedelta(hours=-4))  # simple EDT fallback for smoke use
    y,m,d = map(int, date_str.split("-"))
    hh,mm = map(int, minute_hhmm.split(":"))
    dt_et = datetime(y,m,d,hh,mm,0, tzinfo=ET)
    return int(dt_et.astimezone(timezone.utc).timestamp() * 1000)

def build_synthetic_seconds(minute_close_ms: int, seconds_window: int, case: str) -> pd.DataFrame:
    """
    Build exactly the last N seconds of the CURRENT minute (e.g., :56..:59 for 4s).
    Columns: ['t','open','high','low','close','volume'] (epoch-ms UTC)
    """
    rows = []
    start_ms = minute_close_ms - seconds_window*1000
    price = 1.0000
    for k in range(seconds_window):
        t = start_ms + k*1000
        if case == "pass":
            # 3 green secs (0,1,3), one tiny red (2); last delta >= 5 bps; avg body healthy
            if k in (0,1,3):
                o = price; c = price * (1 + 0.0018)  # +18 bps
            else:
                o = price; c = price * (1 - 0.0005)  # -5 bps
        else:
            # FAIL: only 2 greens and small bodies; last delta < 5 bps
            if k in (0,2):
                o = price; c = price * (1 + 0.0006)  # +6 bps
            else:
                o = price; c = price * (1 - 0.0006)  # -6 bps
        h, l, v = max(o,c), min(o,c), 10000 + 100*k
        rows.append(dict(t=t, open=o, high=h, low=l, close=c, volume=v))
        price = c
    return pd.DataFrame(rows)

def main():
    a = parse_args()
    minute_open_ms = et_minute_open_to_utc_ms(a.date, a.minute)
    minute_close_ms = minute_open_ms + 59_999

    df_sec = build_synthetic_seconds(minute_close_ms, a.seconds_window, a.case)

    ok, reason, metrics = one_sec_continuation_ok(
        df_seconds=df_sec,
        minute_close_ms=minute_close_ms,
        seconds_window=a.seconds_window,
        min_green_count=a.min_green_count,
        min_last_close_delta_bps=a.min_last_delta_bps,
        max_red_body_bps=a.max_red_body_bps,
        min_avg_body_bps=a.min_avg_body_bps,
        min_required_rows=a.min_required_rows,
    )

    print(f"[MICRO_SMOKE] case={a.case} -> {ok}")
    print(f"[MICRO_SMOKE] {reason}")
    print(f"[MICRO_SMOKE] {metrics}")

if __name__ == "__main__":
    main()