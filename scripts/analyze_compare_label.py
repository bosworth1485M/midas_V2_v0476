#!/usr/bin/env python3
"""
Analyze comparison JSONs for a specific compare label.

- Scans: out/*/_comparisons/comparison_*.json (recursive)
- Filters: only entries where .label == --label and .metrics is present
- Dedupe (default): keep the latest run per day (highest run_id)
- Prints a table and optional CSV with Date, Used, WR%, TP, SL, PnL, RunId

Usage:
  python scripts/analyze_compare_label.py --label B_primary_top4_rvol18_g15 --csv out/compare_B_primary_top4_rvol18_g15.csv
"""

import argparse
import csv
import glob
import json
import os
from collections import defaultdict

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".", help="Project root (default: current dir).")
    p.add_argument(
        "--pattern",
        default=os.path.join("out", "*", "_comparisons", "comparison_*.json"),
        help="Glob pattern to comparison JSONs."
    )
    p.add_argument(
        "--label",
        default="B_primary_top4_rvol18_g15",
        help="Compare label to filter on."
    )
    p.add_argument(
        "--csv",
        default="",
        help="Optional path to write a CSV summary."
    )
    p.add_argument(
        "--no-dedupe",
        action="store_true",
        help="List all matching runs (donΓÇÖt keep only the latest per day)."
    )
    return p.parse_args()

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        # Corrupt/partial file ΓÇö skip quietly
        return None

def fmt_pnl(x):
    try:
        return f"{float(x):+.2f}"
    except Exception:
        return "n/a"

def main():
    args = parse_args()
    pattern = os.path.join(args.root, args.pattern)
    files = glob.glob(pattern, recursive=True)
    if not files:
        print("No comparison files found.")
        return 0

    rows = []
    for path in files:
        j = load_json(path)
        if not j:
            continue
        if j.get("label") != args.label:
            continue
        metrics = j.get("metrics") or {}
        used = metrics.get("used")
        tp = metrics.get("tp")
        sl = metrics.get("sl")
        pnl = metrics.get("pnl")
        date = j.get("date")
        run_id = j.get("run_id")

        # Only keep entries that actually have metrics
        if used is None or tp is None or sl is None or pnl is None or not date:
            continue

        # Compute WR% ourselves for consistency
        try:
            used_i = int(used)
            tp_i = int(tp)
            sl_i = int(sl)
        except Exception:
            # Skip malformed
            continue

        wr_pct = (tp_i / used_i * 100.0) if used_i > 0 else 0.0

        rows.append({
            "date": date,
            "used": used_i,
            "wr_pct": wr_pct,
            "tp": tp_i,
            "sl": sl_i,
            "pnl": float(pnl),
            "run_id": run_id,
            "path": path
        })

    if not rows:
        print(f"No matching runs found for label: {args.label}")
        return 0

    if not args.no_dedupe:
        # Keep the latest run per date (max run_id)
        by_date = defaultdict(list)
        for r in rows:
            by_date[r["date"]].append(r)
        deduped = []
        for d, lst in by_date.items():
            # If run_id is missing on some entries, fallback to file mtime
            if all("run_id" in x and x["run_id"] is not None for x in lst):
                best = max(lst, key=lambda x: x["run_id"])
            else:
                best = max(lst, key=lambda x: os.path.getmtime(x["path"]))
            deduped.append(best)
        rows = deduped

    # Sort by date then run_id
    rows.sort(key=lambda r: (r["date"], r["run_id"] if r["run_id"] is not None else -1))

    # Print table
    header = f"{'Date':10} {'Used':>4} {'WR%':>7} {'TP':>3} {'SL':>3} {'PnL':>10} {'RunId':>12}"
    print(header)
    print("-" * len(header))
    tot_used = tot_tp = tot_sl = 0
    tot_pnl = 0.0

    for r in rows:
        print(f"{r['date']:10} {r['used']:>4d} {r['wr_pct']:7.2f} {r['tp']:>3d} {r['sl']:>3d} {fmt_pnl(r['pnl']):>10} {str(r['run_id']):>12}")
        tot_used += r["used"]
        tot_tp += r["tp"]
        tot_sl += r["sl"]
        tot_pnl += r["pnl"]

    overall_wr = (tot_tp / tot_used * 100.0) if tot_used > 0 else 0.0
    print("-" * len(header))
    print(f"{'TOTAL':10} {tot_used:>4d} {overall_wr:7.2f} {tot_tp:>3d} {tot_sl:>3d} {fmt_pnl(tot_pnl):>10}")

    # Optional CSV
    if args.csv:
        os.makedirs(os.path.dirname(args.csv), exist_ok=True)
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date", "used", "wr_pct", "tp", "sl", "pnl", "run_id"])
            for r in rows:
                w.writerow([r["date"], r["used"], f"{r['wr_pct']:.2f}", r["tp"], r["sl"], f"{r['pnl']:.2f}", r["run_id"]])
            # Append totals row
            w.writerow(["TOTAL", tot_used, f"{overall_wr:.2f}", tot_tp, tot_sl, f"{tot_pnl:.2f}", ""])
        print(f"\nCSV written -> {args.csv}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
