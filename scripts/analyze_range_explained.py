#!/usr/bin/env python3
# analyze_range_explained.py
# Print explanatory analysis for a range_summary CSV

import argparse, sys
from pathlib import Path
import pandas as pd

def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default

def analyze(df: pd.DataFrame):
    # Required columns
    req = ["date","scenario","trades","wins","losses","winrate_pct","pnl"]
    missing = [c for c in req if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Coerce numeric
    for c in ["trades","wins","losses","winrate_pct","pnl"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    total_trades = int(df["trades"].sum())
    total_wins = int(df["wins"].sum())
    total_losses = int(df["losses"].sum())
    denom = total_wins + total_losses
    overall_wr = (100.0 * total_wins / denom) if denom > 0 else 0.0
    total_pnl = float(df["pnl"].sum())

    # Active vs zero days
    nonzero_df = df[df["trades"] > 0].copy()
    zero_df = df[df["trades"] == 0].copy()
    days_with_trades = int(len(nonzero_df))
    days_without_trades = int(len(zero_df))

    # Average daily WR on days that had trades
    avg_daily_wr = float(nonzero_df["winrate_pct"].mean()) if not nonzero_df.empty else 0.0
    # Median daily WR
    med_daily_wr = float(nonzero_df["winrate_pct"].median()) if not nonzero_df.empty else 0.0

    # Best/Worst by pnl
    best_day = None
    worst_day = None
    if not nonzero_df.empty:
        best_row = nonzero_df.sort_values("pnl", ascending=False).iloc[0]
        worst_row = nonzero_df.sort_values("pnl", ascending=True).iloc[0]
        best_day = (best_row["date"], float(best_row["pnl"]), int(best_row["trades"]), float(best_row["winrate_pct"]))
        worst_day = (worst_row["date"], float(worst_row["pnl"]), int(worst_row["trades"]), float(worst_row["winrate_pct"]))

    out = {
        "total_trades": total_trades,
        "total_wins": total_wins,
        "total_losses": total_losses,
        "overall_wr": round(overall_wr, 2),
        "total_pnl": round(total_pnl, 2),
        "days_with_trades": days_with_trades,
        "days_without_trades": days_without_trades,
        "avg_daily_wr": round(avg_daily_wr, 2),
        "med_daily_wr": round(med_daily_wr, 2),
        "best_day": best_day,
        "worst_day": worst_day,
    }
    return out

def print_explained(csv_path: Path, df: pd.DataFrame, stats: dict):
    sep = "-" * 72
    print(sep)
    print(f"Range Analysis — {csv_path.name}")
    print(sep)
    print("Overview")
    print(f"  Rows                      : {len(df)} (days in range)")
    print(f"  Days with trades          : {stats['days_with_trades']}")
    print(f"  Days with zero trades     : {stats['days_without_trades']}")
    print("Totals")
    print(f"  Total Trades              : {stats['total_trades']}")
    print(f"  Wins / Losses             : {stats['total_wins']} / {stats['total_losses']}")
    print(f"  Overall Win Rate          : {stats['overall_wr']}%   (wins / (wins+losses))")
    print(f"  Total PnL                 : {stats['total_pnl']}     (sum of daily PnL)")
    if stats['days_with_trades'] > 0:
        print("Daily Quality (on trade days)")
        print(f"  Avg Daily Win Rate        : {stats['avg_daily_wr']}%")
        print(f"  Median Daily Win Rate     : {stats['med_daily_wr']}%")
    if stats['best_day']:
        d, pnl, t, wr = stats['best_day']
        print(f"Best Day                    : {d}  PnL {pnl:+.2f}  Trades {t}  WR {wr:.2f}%")
    if stats['worst_day']:
        d, pnl, t, wr = stats['worst_day']
        print(f"Worst Day                   : {d}  PnL {pnl:+.2f}  Trades {t}  WR {wr:.2f}%")
    print(sep)
    # Brief interpretation
    print("Interpretation")
    if stats['overall_wr'] >= 55.0:
        print("  ✔ Baseline WR is in the target zone (≥55%). Continue expanding the sample.")
    elif stats['overall_wr'] >= 50.0:
        print("  ~ WR is near 50–55%. Consider small guard adjustments or adding a variant (D_strict / E_dip).")
    else:
        print("  ✖ WR < 50%. Prioritize guard tuning before expanding sample size.")
    if stats['days_without_trades'] > stats['days_with_trades']:
        print("  Note: Many zero‑trade days — consider broadening the universe or easing filters later (after baseline).")
    print(sep)
    print("Next Actions")
    print("  1) Run another range to increase sample size (same scenario).")
    print("  2) If WR <55%, compare with Scenario D_strict (tighter early guard) or E_dip (reclaim entries).")
    print("  3) Only after baseline is validated, consider 1‑sec entries or multiple trades per ticker.")
    print(sep)

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Explanatory analysis for range_summary CSV")
    ap.add_argument("--csv", required=True, help="Path to range_summary_*.csv")
    args = ap.parse_args()

    p = Path(args.csv)
    if not p.exists():
        print(f"[ERR] CSV not found: {p}", file=sys.stderr); sys.exit(1)

    df = pd.read_csv(p)
    stats = analyze(df)
    print_explained(p, df, stats)

if __name__ == "__main__":
    main()
