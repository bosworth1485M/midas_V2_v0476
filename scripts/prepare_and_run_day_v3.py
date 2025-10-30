#!/usr/bin/env python3
# prepare_and_run_day_v3.py
# One-shot daily runner that:
# - Resolves the previous TRADING day via scripts/prev_trading_day_polygon.py
# - Logs Target/PrevTradingDay
# - Parses topgappers table for the target day
# - Fetches minute bars for N tickers (0 = all)
# - Writes data\universe_<DATE>.txt
# - Runs scenarios (default A,B,C,D,E)
# - Prints summary

import argparse, subprocess, sys
from pathlib import Path
import csv

def run_cmd(cmd):
    print("[CMD]", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, check=False)

def get_prev_trading_day(python_exe: str, date: str) -> str:
    res = run_cmd([python_exe, r".\scripts\prev_trading_day_polygon.py", "--date", date, "--quiet"])
    if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()
    return ""

def parse_tickers_from_table(text: str):
    tickers = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("Open-gap") or s.startswith("SYMBOL"):
            continue
        parts = s.split()
        if not parts:
            continue
        sym = parts[0].strip().upper()
        if 1 <= len(sym) <= 10:
            tickers.append(sym)
    seen = set()
    out = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out

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
    ap.add_argument("--tickers", type=int, default=0, help="How many top gappers to include (0 = all)")
    ap.add_argument("--scenarios", default="A,B,C,D,E", help="Comma list")
    ap.add_argument("--session", default="rth", choices=["rth","all"])
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    date = args.date
    yyyymmdd = date.replace("-","")
    scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()]
    universe_path = Path("data") / f"universe_{date}.txt"

    prev = get_prev_trading_day(args.python, date)
    if prev:
        print(f"[INFO] Target={date}  PrevTradingDay={prev}")
    else:
        print(f"[WARN] Could not resolve previous trading day for {date}. Continuing.")

    # Top gappers for the target date
    tg = run_cmd([args.python, r".\scripts\topgappers.py", "--date", date, "--no-write"])
    tickers = parse_tickers_from_table(tg.stdout)
    if not tickers:
        print("[ERR] Could not parse any tickers from topgappers output. Aborting.")
        sys.exit(1)

    if args.tickers and args.tickers > 0:
        tickers = tickers[:args.tickers]
    print("[INFO] Using tickers:", ", ".join(tickers))

    # Fetch minutes
    for t in tickers:
        print(f"[FETCH] {t} {date} ({args.session})")
        _ = run_cmd([args.python, r".\scripts\fetch_minutes_polygon.py", "--date", date, "--session", args.session, "--symbol", t])

    # Write universe
    print("[WRITE]", universe_path)
    universe_path.write_text("\n".join(tickers), encoding="ascii")

    # Run scenarios
    outroot = Path("out") / "auto" / yyyymmdd
    outroot.mkdir(parents=True, exist_ok=True)

    rows = []
    for scn in scenarios:
        outdir = outroot / scn
        outdir.mkdir(parents=True, exist_ok=True)
        cmd = [args.python, "-m", "midas_v2.cli", "backtest", "--date", date, "--scenario", scn, "--universe", str(universe_path), "--out", str(outdir)]
        res = run_cmd(cmd)
        csv_path = outdir / f"results_{date}.csv"
        st = read_stats(csv_path)
        rows.append((scn, csv_path, st))

    print("\nScenario  Trades  Wins  Losses  WinRate%  AvgWin  AvgLoss  TotalPnL")
    for scn, csv_path, st in rows:
        print(f"{scn:8} {st['trades']:6d} {st['wins']:5d} {st['losses']:7d} {st['win_rate']:8.2f} {st['avg_win']:7.2f} {st['avg_loss']:8.2f} {st['total_pnl']:9.2f}")
        print(f"   CSV: {csv_path}")

if __name__ == "__main__":
    main()
