#!/usr/bin/env python3
# run_range_safe.py (filtered)
# Runs the standard range runner, FILTERS out the old "=== TOTALS ===" block,
# then REBUILDS the range summary from per-day CSVs so your summary is always correct.
#
# Usage:
#   python scripts/run_range_safe.py --start YYYY-MM-DD --end YYYY-MM-DD --scenario D
#
# What you will see:
# - Normal per-day run lines from the range runner
# - NO confusing "=== TOTALS ===" printout
# - A final "[OK] Fresh summary -> ..." line pointing to the rebuilt CSV

import argparse, subprocess, sys, re
from pathlib import Path
from datetime import datetime

TOTALS_START = re.compile(r'^\s*=== TOTALS ===\s*$')
TRADES_LINE  = re.compile(r'^\s*\[[A-Z]\]\s+trades=\d+.*$')

def stream_and_filter(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    suppress = False
    for line in proc.stdout:
        # Start suppressing at the old totals header
        if TOTALS_START.match(line):
            suppress = True
            continue
        # While suppressing, skip lines that look like the old totals
        if suppress:
            # Stop suppressing once we see the range summary CSV line or a blank line after totals
            if line.strip().startswith("[OK] Range summary CSV") or line.strip() == "":
                suppress = False
            # Do not print any of the totals block
            continue
        # Filter any stray "[X] trades=..." lines as a backup
        if TRADES_LINE.match(line):
            continue
        # Normal output
        print(line, end="")
    proc.wait()
    return proc.returncode

def main():
    ap = argparse.ArgumentParser(description="Run range then rebuild the summary from day CSVs (no staleness).")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--scenario", required=True, help="Scenario letter, e.g., D or E")
    ap.add_argument("--project-root", default=".", help="Project root (default: current folder)")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    py = sys.executable

    # 1) Run the range (executes per-day runs), but filter out old totals noise
    cmd_range = [py, str(root / "scripts" / "run_range_and_summarize.py"),
                 "--start", args.start, "--end", args.end, "--scenario", args.scenario]
    print("[RUN]", " ".join(cmd_range))
    rc = stream_and_filter(cmd_range)
    if rc != 0:
        sys.exit(rc)

    # 2) Rebuild summary strictly from per-day CSVs
    cmd_rebuild = [py, str(root / "scripts" / "rebuild_range_summary.py"),
                   "--start", args.start, "--end", args.end, "--scenario", args.scenario]
    print("[REBUILD]", " ".join(cmd_rebuild))
    r2 = subprocess.run(cmd_rebuild)
    if r2.returncode != 0:
        sys.exit(r2.returncode)

    # 3) Show where the file lives
    start_tag = datetime.fromisoformat(args.start).strftime("%Y%m%d")
    end_tag = datetime.fromisoformat(args.end).strftime("%Y%m%d")
    out_csv = root / "out" / "auto" / f"range_summary_{start_tag}_{end_tag}_{args.scenario.upper()}.csv"
    print(f"[OK] Fresh summary -> {out_csv}")

if __name__ == "__main__":
    main()
