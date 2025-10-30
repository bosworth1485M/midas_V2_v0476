#!/usr/bin/env python3
# stats_only.py - compute stats from an existing results CSV (no backtest run)

import argparse, csv
from pathlib import Path

def read_stats(csv_path: Path):
    wins = losses = 0
    total = 0.0
    win_sum = 0.0
    loss_sum = 0.0
    with csv_path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                pnl = float(row.get("pnl", 0) or 0)
            except:
                pnl = 0.0
            outcome = (row.get("outcome") or "").strip().lower()
            total += pnl
            if outcome in ("tp","win"):
                wins += 1
                win_sum += pnl
            elif outcome in ("sl","loss"):
                losses += 1
                loss_sum += pnl
    trades = wins + losses
    win_rate = (wins / trades * 100.0) if trades else 0.0
    avg_win = (win_sum / wins) if wins else 0.0
    avg_loss = (loss_sum / losses) if losses else 0.0
    return trades, wins, losses, win_rate, avg_win, avg_loss, total

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to results_YYYY-MM-DD.csv")
    args = ap.parse_args()
    p = Path(args.csv)
    if not p.exists():
        print(f"[ERR] Not found: {p}")
        return
    trades, wins, losses, win_rate, avg_win, avg_loss, total = read_stats(p)
    print("Trades Wins Losses WinRate% AvgWin AvgLoss TotalPnL")
    print(f"{trades:6d} {wins:4d} {losses:6d} {win_rate:8.2f} {avg_win:6.2f} {avg_loss:7.2f} {total:8.2f}")

if __name__ == '__main__':
    main()
