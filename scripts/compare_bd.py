#!/usr/bin/env python3
# compare_bd.py - run backtests for given scenarios and print stats (pure Python, no PowerShell)

import argparse, csv, os, subprocess, sys
from pathlib import Path

def read_stats(csv_path: Path):
    wins = losses = 0
    total = 0.0
    win_sum = 0.0
    loss_sum = 0.0
    if not csv_path.exists():
        return {"trades": 0, "wins": 0, "losses": 0, "win_rate": 0.0, "avg_win": 0.0, "avg_loss": 0.0, "total_pnl": 0.0}
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
    return {"trades": trades, "wins": wins, "losses": losses, "win_rate": win_rate, "avg_win": avg_win, "avg_loss": avg_loss, "total_pnl": total}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--scenarios", default="B,D", help="Comma list, e.g. B,D")
    ap.add_argument("--universe", default="data/samples/universe_sample.txt")
    ap.add_argument("--outroot", default="out/cmp")
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    date = args.date
    scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()]
    outroot = Path(args.outroot)
    outroot.mkdir(parents=True, exist_ok=True)

    print(f"=== Compare scenarios on {date} ===")
    rows = []
    for scn in scenarios:
        outdir = outroot / f"{scn}_{date.replace('-','')}"
        outdir.mkdir(parents=True, exist_ok=True)

        cmd = [args.python, "-m", "midas_v2.cli", "backtest", "--date", date, "--scenario", scn, "--universe", args.universe, "--out", str(outdir)]
        print(f"[RUN] {scn}: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[WARN] Scenario {scn} returned {res.returncode}")
            if res.stderr:
                print(res.stderr.strip())

        csv_path = outdir / f"results_{date}.csv"
        st = read_stats(csv_path)
        rows.append((scn, csv_path, st))

    # Print summary
    print("\nScenario  Trades  Wins  Losses  WinRate%  AvgWin  AvgLoss  TotalPnL")
    for scn, csv_path, st in rows:
        print(f"{scn:8} {st['trades']:6d} {st['wins']:5d} {st['losses']:7d} {st['win_rate']:8.2f} {st['avg_win']:7.2f} {st['avg_loss']:8.2f} {st['total_pnl']:9.2f}")
        print(f"   CSV: {csv_path}")

if __name__ == '__main__':
    main()
