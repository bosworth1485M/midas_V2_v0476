#!/usr/bin/env python3
"""
regression_smoke_v1.py — basic post-change regression for Midas_V2 (streams live output)

What it checks using ONLY your existing scripts:
1) Non-trading days (holiday + weekend) — ensures they SKIP cleanly.
2) Single-day sanity (default: 2025-08-05, Scenario D) — runs day + summaries.
3) Small range (default: 10 days from 2025-08-05, Scenario D) — runs range + analyzer.

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

def run(cmd:list[str], *, quiet:bool=False, check:bool=False, capture:bool=False) -> subprocess.CompletedProcess:
    """Run a command under repo root.
       - capture=False (default): stream child output live to console (like normal tests)
       - capture=True : capture stdout/stderr, but still echo stdout for visibility
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH","")
    printable = " ".join(cmd)
    if not quiet:
        print(f"\n$ {printable}")
    if capture:
        proc = subprocess.run(cmd, cwd=str(ROOT), env=env, text=True, capture_output=True)
        # echo captured output so user still sees it
        if proc.stdout:
            print(proc.stdout.rstrip())
        if proc.returncode != 0 and proc.stderr:
            print(proc.stderr.rstrip(), file=sys.stderr)
    else:
        proc = subprocess.run(cmd, cwd=str(ROOT), env=env)  # streams live
    if check and proc.returncode != 0:
        raise SystemExit(proc.returncode)
    return proc

def test_nontrading(dates:list[str], scenario:str, quiet:bool=False) -> None:
    print("\n== Non-trading day handling ==")
    for d in dates:
        # capture so we can auto-check, but still echo output
        r = run([sys.executable, str(SCRIPTS/"run_day_simple.py"), "--date", d, "--scenario", scenario],
                quiet=quiet, capture=True)
        out = (r.stdout or "")
        ok = ("Skipping minutes fetch and backtest" in out) or ("No grouped results" in out)
        print(f"[{'OK' if ok else 'WARN'}] {d}: {'skipped cleanly' if ok else 'expected skip not detected'}")

def single_day(date_str:str, scenario:str, include_e:bool, quiet:bool=False) -> None:
    print("\n== Single-day sanity ==")
    for sc in ([scenario] + (["E"] if include_e and scenario != "E" else [])):
        run([sys.executable, str(SCRIPTS/"run_day_simple.py"), "--date", date_str, "--scenario", sc], quiet=quiet)
        run([sys.executable, str(SCRIPTS/"summarize_results.py"), "--date", date_str], quiet=quiet)
        run([sys.executable, str(SCRIPTS/"view_results.py"), "--date", date_str, "--scenario", sc, "--preview", "20", "--top", "5"], quiet=quiet)

def small_range(start:str, days:int, scenario:str, include_e:bool, quiet:bool=False) -> None:
    print("\n== Small range regression ==")
    start_dt = datetime.fromisoformat(start).date()
    end_dt = start_dt + timedelta(days=max(1, days)-1)
    start_s, end_s = start_dt.isoformat(), end_dt.isoformat()
    for sc in ([scenario] + (["E"] if include_e and scenario != "E" else [])):
        run([sys.executable, str(SCRIPTS/"run_range_and_summarize.py"),
             "--start", start_s, "--end", end_s, "--scenario", sc], quiet=quiet)
        # capture show_latest_range so we can detect the CSV path (but still echo it)
        r = run([sys.executable, str(SCRIPTS/"show_latest_range.py"), "--root", str(OUT/"auto"), "--scenario", sc],
                quiet=quiet, capture=True)
        csv_path = None
        for ln in (r.stdout or "").splitlines():
            if ln.strip().endswith(f"_{sc}.csv"):
                csv_path = ln.strip()
                break
        if csv_path:
            run([sys.executable, str(SCRIPTS/"analyze_range_explained.py"), "--csv", csv_path], quiet=quiet)
        else:
            print(f"[WARN] Could not detect summary CSV path for scenario {sc}.")

def main():
    ap = argparse.ArgumentParser(description="Basic regression smoke-test (streams output).")
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
