# scripts/summarize_pnl.py
import argparse, csv, pathlib

def summarize(csv_path: pathlib.Path):
    trades = wins = losses = 0
    total_pnl = 0.0
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trades += 1
            total_pnl += float(row["pnl"])
            if row["outcome"] == "TP":
                wins += 1
            elif row["outcome"] == "SL":
                losses += 1
    winrate = (wins / trades * 100) if trades else 0.0
    return trades, wins, losses, winrate, total_pnl

def main():
    ap = argparse.ArgumentParser(description="Summarize PnL from scenario CSV(s)")
    ap.add_argument("--date", required=True, help="Date, e.g. 2025-08-06")
    ap.add_argument("--scenarios", default="B,E", help="Comma-separated scenarios to check")
    ap.add_argument("--out-root", default="out/auto", help="Results root folder")
    args = ap.parse_args()

    for scen in [s.strip().upper() for s in args.scenarios.split(",")]:
        csv_path = pathlib.Path(args.out_root) / args.date.replace("-", "") / scen / f"results_{args.date}.csv"
        if not csv_path.exists():
            print(f"[WARN] CSV not found for {scen}: {csv_path}")
            continue
        trades, wins, losses, winrate, total_pnl = summarize(csv_path)
        print(f"Scenario {scen}: trades={trades}, wins={wins}, losses={losses}, "
              f"winrate={winrate:.2f}%, totalPnL={total_pnl:.2f}")

if __name__ == "__main__":
    main()