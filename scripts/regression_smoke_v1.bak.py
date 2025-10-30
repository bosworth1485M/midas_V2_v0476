#!/usr/bin/env python3
"""
regression_smoke_v1.py — basic post-change regression for Midas_V2

What it does (uses ONLY your existing scripts/commands):
1) Non-trading day handling (holiday + weekend): runs run_day_simple.py on known dates and
   checks that it prints INFO and SKIPS cleanly (no failures).
2) Single-day sanity (default: 2025-08-05, Scenario D): runs the day, then summarize_results.py
   and view_results.py so you can eyeball trades.
3) Small range (default: 10 days starting 2025-08-05, Scenario D): runs run_range_and_summarize.py,
   then show_latest_range.py and analyze_range_explained.py.

CLI (all optional):
  --scenario D            Scenario to test (default D)
  --range-start YYYY-MM-DD  Range start (default 2025-08-05)
  --range-days 10         Small range length (default 10)
  --include-e             Also test Scenario E for single day and range
  --skip-single           Skip the single day sanity check
  --skip-range            Skip the range check
  --quiet                 Less output (still shows commands and key results)

Run from repo root:
  python scripts\regression_smoke_v1.py
"""

from __future__ import annotations
import argparse, os, sys, subprocess
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
OUT = ROOT / "out"

def run(cmd:list[str], quiet:bool=False, check:bool=False) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH","")
    printable = " ".join(cmd)
    if not quiet:
        print(f"\n$ {printable}")
    r = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    if not quiet:
        if r.stdout:
            print(r.stdout.rstrip())
        if r.returncode != 0 and r.stderr:
            print(r.stderr.rstrip())
    if check and r.returncode != 0:
        raise SystemExit(r.returncode)
    return r

def test_nontrading(dates:list[str], scenario:str, quiet:bool=False) -> None:
    print("\n== Non-trading day handling ==")
    for d in dates:
        r = run([sys.executable, str(SCRIPTS/"run_day_simple.py"), "--date", d, "--scenario", scenario], quiet=quiet)
        ok = ("Skipping minutes fetch and backtest" in (r.stdout or "")) or ("No grouped results" in (r.stdout or ""))
        print(f"[{'OK' if ok else 'WARN'}] {d}: {'skipped cleanly' if ok else 'expected skip not detected'}")

def single_day(date_str:str, scenario:str, include_e:bool, quiet:bool=False) -> None:
    print("\n== Single-day sanity ==")
    for sc in ([scenario] + (["E"] if include_e and scenario != "E" else [])):
        run([sys.executable, str(SCRIPTS/"run_day_simple.py"), "--date", date_str, "--scenario", sc], quiet=quiet)
        run([sys.executable, str(SCRIPTS/"summarize_results.py"), "--date", date_str], quiet=quiet)
        # quick detail view for the scenario we just ran
        run([sys.executable, str(SCRIPTS/"view_results.py"), "--date", date_str, "--scenario", sc, "--preview", "20", "--top", "5"], quiet=quiet)

def small_range(start:str, days:int, scenario:str, include_e:bool, quiet:bool=False) -> None:
    print("\n== Small range regression ==")
    start_dt = datetime.fromisoformat(start).date()
    end_dt = start_dt + timedelta(days=max(1, days)-1)
    start_s, end_s = start_dt.isoformat(), end_dt.isoformat()
    for sc in ([scenario] + (["E"] if include_e and scenario != "E" else [])):
        run([sys.executable, str(SCRIPTS/"run_range_and_summarize.py"),
             "--start", start_s, "--end", end_s, "--scenario", sc], quiet=quiet, check=False)
        # Show path + first lines
        r = run([sys.executable, str(SCRIPTS/"show_latest_range.py"), "--root", str(OUT/"auto"), "--scenario", sc], quiet=quiet)
        # Analyze
        lines = (r.stdout or "").splitlines()
        csv_path = None
        for ln in lines:
            if ln.strip().endswith(f"_{sc}.csv"):
                csv_path = ln.strip()
                break
        if csv_path:
            run([sys.executable, str(SCRIPTS/"analyze_range_explained.py"), "--csv", csv_path], quiet=quiet)
        else:
            print(f"[WARN] Could not detect summary CSV path for scenario {sc}.")

def main():
    ap = argparse.ArgumentParser(description="Basic regression smoke-test using existing scripts only.")
    ap.add_argument("--scenario", default="D", help="Scenario to test (default: D)")
    ap.add_argument("--range-start", default="2025-08-05", help="Range start (YYYY-MM-DD)")
    ap.add_argument("--range-days", type=int, default=10, help="Number of days in small range (default: 10)")
    ap.add_argument("--include-e", action="store_true", help="Also test scenario E for single-day and range")
    ap.add_argument("--skip-single", action="store_true", help="Skip single-day sanity")
    ap.add_argument("--skip-range", action="store_true", help="Skip small-range regression")
    ap.add_argument("--quiet", action="store_true", help="Less output")
    args = ap.parse_args()

    # 1) Non-trading day handling (holiday + weekend)
    nontrading_dates = ["2025-09-01", "2025-09-06", "2025-09-07"]
    test_nontrading(nontrading_dates, args.scenario.upper(), quiet=args.quiet)

    # 2) Single-day sanity (known working day)
    if not args.skip_single:
        single_day("2025-08-05", args.scenario.upper(), include_e=args.include_e, quiet=args.quiet)

    # 3) Small range (e.g., 10 days)
    if not args.skip_range:
        small_range(args.range_start, args.range_days, args.scenario.upper(), include_e=args.include_e, quiet=args.quiet)

    print("\n[OK] Regression smoke-test complete. Review outputs above for any WARN/ERR lines.")

if __name__ == "__main__":
    main()
