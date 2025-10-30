#!/usr/bin/env python3
# scripts/analyze_all_ranges.py
import argparse, sys, glob
from pathlib import Path
import pandas as pd

from analyze_range import analyze, format_report  # assumes both scripts sit in same folder

def main():
    ap = argparse.ArgumentParser(description="Find latest range_summary CSV and analyze it.")
    ap.add_argument("--root", default="out/auto", help="Folder where range_summary CSVs live")
    ap.add_argument("--scenario", default="B", help="Scenario to filter by (default B)")
    ap.add_argument("--report", default=None, help="Optional Markdown report path")
    args = ap.parse_args()

    pattern = str(Path(args.root) / f"range_summary_*_{args.scenario}.csv")
    files = glob.glob(pattern)
    if not files:
        print(f"[ERR] No files found: {pattern}", file=sys.stderr)
        sys.exit(1)

    latest = max(files, key=lambda p: Path(p).stat().st_mtime)
    print(f"[INFO] Latest CSV: {latest}")
    df = pd.read_csv(latest)
    stats = analyze(df)

    # Console summary
    print(f"Rows: {len(df)}")
    print(f"Total Trades: {stats['total_trades']}")
    print(f"Wins / Losses: {stats['total_wins']} / {stats['total_losses']}")
    print(f"Overall Win Rate: {stats['overall_winrate_pct']}%")
    print(f"Total PnL: {stats['total_pnl']}")

    if args.report:
        md = format_report(Path(latest), df, stats)
        Path(args.report).write_text(md, encoding='utf-8')
        print(f"[OK] Report saved -> {args.report}")

if __name__ == "__main__":
    main()
