#!/usr/bin/env python3
import argparse, csv, sys
from pathlib import Path
from datetime import datetime, timedelta

def daterange(start: datetime, end: datetime):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)

def analyze_day(day: datetime, scenario: str, root: Path):
    ymd = day.strftime("%Y%m%d")
    iso = day.strftime("%Y-%m-%d")
    day_csv = root / "out" / ymd / scenario / f"results_{iso}.csv"
    if not day_csv.exists():
        return None
    trades = 0
    wins = 0
    losses = 0
    pnl_sum = 0.0
    try:
        with day_csv.open("r", encoding="utf-8", newline="") as f:
            rdr = csv.DictReader(f)
            for row in rdr:
                trades += 1
                outcome = (row.get("outcome") or "").strip().upper()
                if outcome == "TP":
                    wins += 1
                elif outcome == "SL":
                    losses += 1
                try:
                    pnl_sum += float(row.get("pnl") or 0.0)
                except Exception:
                    pass
    except Exception as e:
        print(f"[WARN] Failed to read {day_csv}: {e}", file=sys.stderr)
        return None
    winrate = (100.0 * wins / (wins + losses)) if (wins + losses) > 0 else 0.0
    return {"date": iso, "scenario": scenario, "trades": trades, "wins": wins, "losses": losses, "winrate_pct": round(winrate, 2), "pnl": round(pnl_sum, 2)}

def main():
    ap = argparse.ArgumentParser(description="Rebuild range summary strictly from per-day results CSVs (one scenario).")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--scenario", required=True, help="Scenario letter, e.g., D or E")
    ap.add_argument("--project-root", default=".", help="Project root (default: current folder)")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end)
    scenario = args.scenario.upper()

    rows = []
    for d in daterange(start, end):
        r = analyze_day(d, scenario, root)
        if r is not None:
            rows.append(r)

    out_dir = root / "out" / "auto"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / f"range_summary_{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}_{scenario}.csv"

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date","scenario","trades","wins","losses","winrate_pct","pnl"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Print a short recap to console
    total_trades = sum(r["trades"] for r in rows)
    total_wins = sum(r["wins"] for r in rows)
    total_losses = sum(r["losses"] for r in rows)
    total_pnl = round(sum(r["pnl"] for r in rows), 2)
    denom = total_wins + total_losses
    overall_wr = round(100.0 * total_wins / denom, 2) if denom > 0 else 0.0
    print(f"[OK] Wrote {out_csv}")
    print(f"Totals -> trades={total_trades}, wins={total_wins}, losses={total_losses}, WR={overall_wr}%, PnL={total_pnl}")

if __name__ == "__main__":
    main()
