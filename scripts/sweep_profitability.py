#!/usr/bin/env python3
# sweep_profitability.py
# Minimal safe version: no docstrings with backslashes

import argparse
import csv
import subprocess
import sys
from pathlib import Path

def parse_list(s):
    return [float(x.strip()) for x in s.split(",") if x.strip()]

def find_results_csv(out_dir, date):
    cand = out_dir / f"results_{date}.csv"
    if cand.exists():
        return cand
    for p in out_dir.glob("*.csv"):
        return p
    return None

def summarize_results(csv_path):
    wins = losses = 0
    total = 0.0
    if not csv_path or not csv_path.exists():
        return wins, losses, total
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            outcome = (row.get("outcome") or "").strip().lower()
            try:
                pnl = float(row.get("pnl") or 0.0)
            except ValueError:
                pnl = 0.0
            total += pnl
            if outcome == "win":
                wins += 1
            elif outcome == "loss":
                losses += 1
    return wins, losses, total

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--scenario", default="B")
    ap.add_argument("--universe", required=True)
    ap.add_argument("--tp", required=True, help="Comma-separated TP list, e.g. 5,10,15")
    ap.add_argument("--sl", required=True, help="Comma-separated SL list, e.g. 5,6,8")
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    date = args.date
    scn = args.scenario
    tps = parse_list(args.tp)
    sls = parse_list(args.sl)
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    summary_csv = out_root / f"sweep_summary_{date}_{scn}.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as fsum:
        writer = csv.writer(fsum)
        writer.writerow(["tp_pct", "sl_pct", "wins", "losses", "total_pnl", "results_csv"])

        for tp in tps:
            for sl in sls:
                combo_dir = out_root / f"TP{tp:.2f}_SL{sl:.2f}"
                combo_dir.mkdir(parents=True, exist_ok=True)

                cmd = [
                    args.python, "-m", "midas_v2.cli", "backtest",
                    "--date", date,
                    "--scenario", scn,
                    "--universe", args.universe,
                    "--out", str(combo_dir),
                ]
                print(f"[RUN] TP={tp}% SL={sl}%")
                subprocess.run(cmd)

                results_csv = find_results_csv(combo_dir, date)
                wins, losses, total = summarize_results(results_csv)
                writer.writerow([tp, sl, wins, losses, total, str(results_csv or "")])

if __name__ == "__main__":
    main()