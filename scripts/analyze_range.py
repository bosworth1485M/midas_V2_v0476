#!/usr/bin/env python3
# scripts/analyze_range.py
import argparse, sys
from pathlib import Path
import pandas as pd

def analyze(df: pd.DataFrame):
    # Normalize columns
    cols = {c.lower(): c for c in df.columns}
    req = ["date","scenario","trades","wins","losses","winrate_pct","pnl"]
    missing = [c for c in req if c not in [x.lower() for x in df.columns]]
    if missing:
        raise ValueError(f"Missing required columns: {missing} in CSV (found: {list(df.columns)})")

    total_trades = int(df["trades"].fillna(0).sum())
    total_wins = int(df["wins"].fillna(0).sum())
    total_losses = int(df["losses"].fillna(0).sum())
    denom = total_wins + total_losses
    overall_wr = (100.0 * total_wins / denom) if denom > 0 else 0.0
    total_pnl = float(df["pnl"].fillna(0).sum())

    nonzero_days = (df["trades"] > 0).sum()
    zero_days = (df["trades"] == 0).sum()

    # Best/Worst day by pnl
    best = df.sort_values("pnl", ascending=False).head(1)
    worst = df.sort_values("pnl", ascending=True).head(1)

    result = {
        "total_trades": total_trades,
        "total_wins": total_wins,
        "total_losses": total_losses,
        "overall_winrate_pct": round(overall_wr, 2),
        "total_pnl": round(total_pnl, 2),
        "days_with_trades": int(nonzero_days),
        "days_without_trades": int(zero_days),
        "best_day": (best["date"].iloc[0], float(best["pnl"].iloc[0])) if not best.empty else (None, None),
        "worst_day": (worst["date"].iloc[0], float(worst["pnl"].iloc[0])) if not worst.empty else (None, None),
    }
    return result

def format_report(csv_path: Path, df: pd.DataFrame, stats: dict):
    lines = []
    lines.append(f"# Range Analysis — {csv_path.name}")
    lines.append("")
    lines.append(f"- **Rows:** {len(df)}")
    lines.append(f"- **Total Trades:** {stats['total_trades']}")
    lines.append(f"- **Wins / Losses:** {stats['total_wins']} / {stats['total_losses']}")
    lines.append(f"- **Overall Win Rate:** {stats['overall_winrate_pct']}%")
    lines.append(f"- **Total PnL:** {stats['total_pnl']}")
    lines.append(f"- **Days with trades:** {stats['days_with_trades']}")
    lines.append(f"- **Days without trades:** {stats['days_without_trades']}")
    if stats['best_day'][0] is not None:
        lines.append(f"- **Best day:** {stats['best_day'][0]} (PnL {stats['best_day'][1]:+.2f})")
    if stats['worst_day'][0] is not None:
        lines.append(f"- **Worst day:** {stats['worst_day'][0]} (PnL {stats['worst_day'][1]:+.2f})")
    lines.append("")
    lines.append("## Daily Breakdown")
    lines.append("date,scenario,trades,wins,losses,winrate_pct,pnl")
    for _, r in df.iterrows():
        lines.append(f"{r['date']},{r['scenario']},{int(r['trades'])},{int(r['wins'])},{int(r['losses'])},{float(r['winrate_pct'])},{float(r['pnl'])}")
    lines.append("")
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser(description="Analyze a range_summary CSV and print totals.")
    ap.add_argument("--csv", required=True, help="Path to range_summary_*.csv")
    ap.add_argument("--report", default=None, help="Optional path to save a Markdown report")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"[ERR] CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(csv_path)
    stats = analyze(df)

    # Print clean console summary
    print(f"=== Analysis: {csv_path.name} ===")
    print(f"Rows: {len(df)}")
    print(f"Total Trades: {stats['total_trades']}")
    print(f"Wins / Losses: {stats['total_wins']} / {stats['total_losses']}")
    print(f"Overall Win Rate: {stats['overall_winrate_pct']}%")
    print(f"Total PnL: {stats['total_pnl']}")
    print(f"Days with trades: {stats['days_with_trades']}")
    print(f"Days without trades: {stats['days_without_trades']}")
    if stats['best_day'][0] is not None:
        print(f"Best day: {stats['best_day'][0]} (PnL {stats['best_day'][1]:+.2f})")
    if stats['worst_day'][0] is not None:
        print(f"Worst day: {stats['worst_day'][0]} (PnL {stats['worst_day'][1]:+.2f})")

    if args.report:
        md = format_report(csv_path, df, stats)
        Path(args.report).write_text(md, encoding="utf-8")
        print(f"[OK] Report saved -> {args.report}")

if __name__ == "__main__":
    main()
