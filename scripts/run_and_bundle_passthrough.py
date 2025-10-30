#!/usr/bin/env python3
"""
run_and_bundle_passthrough.py

One command that:
  1) runs run_catalyst_flow.py with EXACT flags you pass (no defaults),
  2) runs summarize_results.py for the date,
  3) writes a comparison bundle into out/<YYYYMMDD>/_comparisons.

Why:
- You can keep all your experimental flags on run_catalyst_flow.py.
- You don't have to remember to summarize + bundle after each run.

Usage (note the `--` to pass flags verbatim):
  python scripts/run_and_bundle_passthrough.py --date 2025-08-05 --scenario B -- \
      --news-first --news-min-score 2 --top 8 --enforce-band --deny-negative

Optional overrides (if your file names differ):
  --universe data/catalyst/universe_hybrid_2025-08-05.txt
  --catalyst data/catalyst/catalyst_news_2025-08-05.csv
  --label "B_custom_test"

Relies on project conventions:
- Results live under out/YYYYMMDD/SCENARIO/... (per DEV/USER guides).
- Summaries are produced by scripts/summarize_results.py.

"""

import argparse, subprocess, sys, shlex, os, glob
from pathlib import Path

def yyyymmdd(date_str: str) -> str:
    return date_str.replace("-", "")

def find_latest_summary(out_day: Path, date_str: str) -> Path | None:
    # Find the newest summary *txt* anywhere under out/YYYYMMDD/** that includes the date
    patt = f"summary*{date_str}*.txt"
    cands = sorted(out_day.rglob(patt), key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0] if cands else None

def main():
    # Split args at '--' so everything after goes straight to run_catalyst_flow.py
    if "--" in sys.argv:
        idx = sys.argv.index("--")
        ours, passthrough = sys.argv[1:idx], sys.argv[idx+1:]
    else:
        ours, passthrough = sys.argv[1:], []

    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--scenario", default="B")
    ap.add_argument("--label", default=None, help="Label for comparison JSON (defaults to scenario name)")
    ap.add_argument("--universe", default=None, help="Override path to universe txt")
    ap.add_argument("--catalyst", default=None, help="Override path to catalyst csv")
    args = ap.parse_args(ours)

    root = Path(".").resolve()
    day = yyyymmdd(args.date)
    out_day = root / "out" / day

    # 1) Run catalyst flow with EXACT passthrough flags
    flow_cmd = [sys.executable, "scripts/run_catalyst_flow.py", "--date", args.date, "--scenario", args.scenario]
    if passthrough:
        flow_cmd.extend(passthrough)
    print("[FLOW]", " ".join(map(str, flow_cmd)))
    subprocess.check_call(flow_cmd)

    # 2) Summarize results for this date
    sum_cmd = [sys.executable, "scripts/summarize_results.py", "--date", args.date]
    print("[SUMMARY]", " ".join(map(str, sum_cmd)))
    subprocess.check_call(sum_cmd)

    # 3) Determine universe/catalyst paths
    uni = Path(args.universe) if args.universe else (root / "data" / "catalyst" / f"universe_hybrid_{args.date}.txt")
    cat = Path(args.catalyst) if args.catalyst else (root / "data" / "catalyst" / f"catalyst_news_{args.date}.csv")
    if not uni.exists():
        raise SystemExit(f"[ERROR] Universe not found: {uni}")
    if not cat.exists():
        raise SystemExit(f"[ERROR] Catalyst CSV not found: {cat}")

    # 4) Find newest summary TXT under out/YYYYMMDD/**
    summary_txt = find_latest_summary(out_day, args.date)
    if summary_txt is None:
        raise SystemExit(f"[ERROR] No summary txt found under: {out_day}")

    # 5) Build comparison bundle in out/YYYYMMDD/_comparisons
    cmp_dir = out_day / "_comparisons"
    cmp_dir.mkdir(parents=True, exist_ok=True)
    label = args.label or f"{args.scenario}_bundle"

    bundle_cmd = [
        sys.executable, "scripts/write_compare_bundle.py",
        "--date", args.date,
        "--scenario", args.scenario,
        "--summary", str(summary_txt),
        "--universe", str(uni),
        "--catalyst-csv", str(cat),
        "--out-dir", str(cmp_dir),
        "--label", label
    ]
    print("[BUNDLE]", " ".join(map(str, bundle_cmd)))
    subprocess.check_call(bundle_cmd)

    print("\n[DONE] Completed flow + summary + bundle for", args.date)
    print("       Summary:", summary_txt)
    print("       Comparison dir:", cmp_dir)

if __name__ == "__main__":
    main()