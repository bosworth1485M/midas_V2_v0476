# scripts/analyze_base_only.py
# Reads ONLY canonical results files:
#   out/YYYYMMDD/SCENARIO/results_YYYY-MM-DD.csv
# (Intentionally ignores out/auto artifacts.)
#
# Usage examples:
#   python scripts/analyze_base_only.py --scenario E --start 2025-08-05 --end 2025-08-31
#   python scripts/analyze_base_only.py --scenario D --date 2025-08-05

import argparse, csv
from pathlib import Path
from datetime import datetime, timedelta

def parse_args():
    ap = argparse.ArgumentParser(description="Analyze base-only results (ignoring out/auto).")
    ap.add_argument("--scenario", required=True, help="Scenario letter, e.g. D or E")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--date", help="Single day YYYY-MM-DD")
    g.add_argument("--start", help="Start YYYY-MM-DD")
    ap.add_argument("--end", help="End YYYY-MM-DD (required if --start)", default=None)
    return ap.parse_args()

def daterange(start_dt, end_dt):
    d = start_dt
    while d <= end_dt:
        yield d
        d += timedelta(days=1)

def canonical_path(day: datetime, scenario: str) -> Path:
    ymd = day.strftime("%Y%m%d")
    iso = day.strftime("%Y-%m-%d")
    return Path(f"out/{ymd}/{scenario}/results_{iso}.csv")

def analyze_files(paths):
    total_rows = wins = 0
    total_pnl = 0.0
    per_day = []
    for p in paths:
        if not p.exists():
            continue
        rows = list(csv.DictReader(p.open(newline="", encoding="utf-8")))
        n = len(rows)
        w = sum(1 for r in rows if (r.get("outcome") or "").upper() == "TP")
        try:
            pnl = sum(float(r.get("pnl", 0) or 0) for r in rows)
        except ValueError:
            pnl = 0.0
        total_rows += n
        wins += w
        total_pnl += pnl
        per_day.append((p, n, w, pnl))
    return total_rows, wins, total_pnl, per_day

def main():
    args = parse_args()
    scen = args.scenario.upper()

    if args.date:
        day = datetime.strptime(args.date, "%Y-%m-%d")
        paths = [canonical_path(day, scen)]
        label = f"{args.date} {scen}"
    else:
        if not args.end:
            raise SystemExit("--end is required when using --start")
        start_dt = datetime.strptime(args.start, "%Y-%m-%d")
        end_dt = datetime.strptime(args.end, "%Y-%m-%d")
        paths = [canonical_path(d, scen) for d in daterange(start_dt, end_dt)]
        label = f"{args.start}→{args.end} {scen}"

    n, w, pnl, per_day = analyze_files(paths)
    wr = (w / n) if n else 0.0

    print("----------------------------------------------------")
    print(f"Base-only Analysis — {label}")
    print("  Files read        :", sum(1 for p in paths if p.exists()), "/", len(paths))
    print("  Total trades (N)  :", n)
    print("  Wins              :", w)
    print("  Win rate          :", f"{wr:.2%}")
    print("  Total PnL         :", f"{pnl:.2f}")
    print("----------------------------------------------------")
    if per_day:
        print("Sample days (first 5 with data):")
        for p, dn, dw, dp in per_day[:5]:
            print(" ", p, f"N={dn}  WR={(dw/dn):.2%}  PnL={dp:.2f}")

if __name__ == "__main__":
    main()