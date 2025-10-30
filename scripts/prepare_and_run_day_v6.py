#!/usr/bin/env python3
# prepare_and_run_day_v6.py
# Like v5, but:
# - Scans the ENTIRE repo for candidate CSVs (not just ./data)
# - Matches multiple date formats: YYYY-MM-DD, YYYYMMDD, YYYY_MM_DD
# - Matches symbol variants: SYM, SYM-WS, SYM_WS, SYMWS (dot/underscore/dash removed)
# - Copies the largest matching CSV to data/samples/sample_<DATE>_<SYMBOL>.csv

import argparse, subprocess, sys, os, shutil, re
from pathlib import Path
import csv

UNIVERSE_ACTIVE = Path("data") / "universe_active.txt"
SAMPLES_DIR = Path("data") / "samples"

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
        if 1 <= len(sym) <= 16:
            tickers.append(sym)
    # dedupe preserving order
    seen = set()
    out = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out

def symbol_variants(sym: str):
    s = sym.upper()
    variants = {s, s.replace(".","-"), s.replace(".","_"), s.replace(".",""), s.replace("_","-"), s.replace("-","_")}
    # also collapse any dashes/underscores entirely
    variants.add(re.sub(r"[\._\-]+", "", s))
    return list(variants)

def date_variants(date: str):
    d1 = date  # YYYY-MM-DD
    d2 = date.replace("-", "") # YYYYMMDD
    d3 = date.replace("-", "_") # YYYY_MM_DD
    return [d1, d2, d3]

def find_candidate_csvs(date: str, symbol: str):
    root = Path(".")
    sym_vars = [v.lower() for v in symbol_variants(symbol)]
    date_vars = [v.lower() for v in date_variants(date)]
    cands = []
    for p in root.rglob("*.csv"):
        name = p.name.lower()
        # quick skip: ignore obvious result files and summaries
        if name.startswith("results_") or name.startswith("sweep_summary_"):
            continue
        # must include a symbol variant and a date variant in the filename
        if any(sv in name for sv in sym_vars) and any(dv in name for dv in date_vars):
            try:
                size = p.stat().st_size
            except Exception:
                size = 0
            cands.append((size, p))
    cands.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in cands]

def normalize_to_stage2(date: str, symbol: str) -> Path | None:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    target = SAMPLES_DIR / f"sample_{date}_{symbol}.csv"
    if target.exists() and target.stat().st_size > 0:
        print(f"[OK] Stage-2 sample exists: {target.name} ({target.stat().st_size} bytes)")
        return target
    cands = find_candidate_csvs(date, symbol)
    if not cands:
        print(f"[WARN] No minute CSV found for {symbol} {date}")
        return None
    src = cands[0]
    try:
        shutil.copy2(src, target)
        print(f"[COPY] {src} -> {target}")
    except Exception as e:
        print(f"[ERR] Copy failed {src} -> {target}: {e}")
        return None
    return target

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
    ap.add_argument("--tickers", type=int, default=0, help="0 = all parsed gappers; otherwise limit")
    ap.add_argument("--scenarios", default="A,B,C,D,E", help="Comma list")
    ap.add_argument("--session", default="rth", choices=["rth","all"])
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    date = args.date
    yyyymmdd = date.replace("-", "")
    scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()]

    prev = get_prev_trading_day(args.python, date)
    if prev:
        print(f"[INFO] Target={date}  PrevTradingDay={prev}")
    else:
        print(f"[WARN] Could not resolve previous trading day for {date}. Continuing.")

    # Top gappers for target date
    tg = run_cmd([args.python, r".\scripts\topgappers.py", "--date", date, "--no-write"])
    tickers = parse_tickers_from_table(tg.stdout)
    if not tickers:
        print("[ERR] Could not parse any tickers from topgappers output. Aborting.")
        sys.exit(1)

    if args.tickers and args.tickers > 0:
        tickers = tickers[: args.tickers]
    print("[INFO] Using tickers:", ", ".join(tickers))

    # Fetch minutes for each ticker
    for t in tickers:
        print(f"[FETCH] {t} {date} ({args.session})")
        _ = run_cmd([args.python, r".\scripts\fetch_minutes_polygon.py", "--date", date, "--session", args.session, "--symbol", t])

    # Normalize fetched files to Stage-2 naming under data/samples
    print("[NORMALIZE] Copying minute CSVs to Stage-2 samples... (scanning repo)")
    have = 0
    for t in tickers:
        if normalize_to_stage2(date, t):
            have += 1
    print(f"[NORMALIZE] Ready samples: {have}/{len(tickers)} in {SAMPLES_DIR}")

    # Write one active universe file (overwrites)
    UNIVERSE_ACTIVE.parent.mkdir(parents=True, exist_ok=True)
    UNIVERSE_ACTIVE.write_text("\n".join(tickers), encoding="ascii")
    print("[WRITE]", UNIVERSE_ACTIVE)

    # Run scenarios
    outroot = Path("out") / "auto" / yyyymmdd
    outroot.mkdir(parents=True, exist_ok=True)

    rows = []
    for scn in scenarios:
        outdir = outroot / scn
        outdir.mkdir(parents=True, exist_ok=True)
        cmd = [args.python, "-m", "midas_v2.cli", "backtest",
               "--date", date, "--scenario", scn,
               "--universe", str(UNIVERSE_ACTIVE), "--out", str(outdir)]
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
