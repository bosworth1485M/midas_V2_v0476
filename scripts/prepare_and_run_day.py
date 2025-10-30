#!/usr/bin/env python3
# prepare_and_run_day.py
# One-shot helper to:
# 1) Get top gappers for a date (via scripts/topgappers.py --no-write)
# 2) Fetch minute bars for the first N tickers (via scripts/fetch_minutes_polygon.py)
# 3) Write a universe_<DATE>.txt under data\
# 4) Run scenarios on that universe (default: B), writing to out\auto\<YYYYMMDD>\<SCENARIO>\
# 5) Print a compact summary (trades, wins, losses, winrate, avg win/loss, total PnL)

import argparse, subprocess, sys, re
from pathlib import Path
import csv

def run_cmd(cmd):
    print("[CMD]", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, check=False)

def parse_tickers_from_stdout(text):
    # Extract tickers from lines that look like plain symbols (A-Z and numbers)
    import re as _re
    tickers = []
    for line in text.splitlines():
        t = line.strip().upper()
        if 1 <= len(t) <= 8 and _re.fullmatch(r"[A-Z0-9\.\-]+", t):
            tickers.append(t)
    # Deduplicate preserving order
    seen = set()
    uniq = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq

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
    ap.add_argument("--tickers", type=int, default=3, help="How many top gappers to include (default 3)")
    ap.add_argument("--scenarios", default="B", help="Comma list, e.g. B or B,D or A,B,C,D,E (default B)")
    ap.add_argument("--session", default="rth", choices=["rth","all"])
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    date = args.date
    yyyymmdd = date.replace("-","")
    scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()]
    universe_path = Path("data") / f"universe_{date}.txt"

    # 1) Get top gappers (view-only) and parse tickers
    res = run_cmd([args.python, r".\scripts\topgappers.py", "--date", date, "--no-write"])
    if res.returncode != 0:
        print("[WARN] topgappers.py returned", res.returncode)
        if res.stderr:
            print(res.stderr.strip())
    tickers = parse_tickers_from_stdout(res.stdout)
    if not tickers:
        print("[ERR] No tickers parsed from topgappers output. Aborting.")
        sys.exit(1)
    tickers = tickers[: max(1, args.tickers)]
    print("[INFO] Using tickers:", ", ".join(tickers))

    # 2) Fetch minute bars for each ticker
    for t in tickers:
        print(f"[FETCH] {t} {date} ({args.session})")
        _ = run_cmd([args.python, r".\scripts\fetch_minutes_polygon.py", "--date", date, "--session", args.session, "--symbol", t])

    # 3) Write universe file
    print("[WRITE]", universe_path)
    universe_path.write_text("\n".join(tickers), encoding="ascii")

    # 4) Run scenarios
    outroot = Path("out") / "auto" / yyyymmdd
    outroot.mkdir(parents=True, exist_ok=True)

    rows = []
    for scn in scenarios:
        outdir = outroot / scn
        outdir.mkdir(parents=True, exist_ok=True)
        cmd = [args.python, "-m", "midas_v2.cli", "backtest", "--date", date, "--scenario", scn, "--universe", str(universe_path), "--out", str(outdir)]
        res = run_cmd(cmd)
        if res.returncode != 0 and res.stderr:
            print("[WARN]", res.stderr.strip())
        csv_path = outdir / f"results_{date}.csv"
        st = read_stats(csv_path)
        rows.append((scn, csv_path, st))

    # 5) Print summary
    print("\nScenario  Trades  Wins  Losses  WinRate%  AvgWin  AvgLoss  TotalPnL")
    for scn, csv_path, st in rows:
        print(f"{scn:8} {st['trades']:6d} {st['wins']:5d} {st['losses']:7d} {st['win_rate']:8.2f} {st['avg_win']:7.2f} {st['avg_loss']:8.2f} {st['total_pnl']:9.2f}")
        print(f"   CSV: {csv_path}")

if __name__ == "__main__":
    main()
