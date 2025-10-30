#!/usr/bin/env python3
"""
view_results.py — tiny, dependency‑free viewer for Midas_V2 results

Usage examples (run from your project root):
  python scripts/view_results.py --date 2025-08-05                # overview for all scenarios with results
  python scripts/view_results.py --date 2025-08-05 --scenario D    # detailed view for scenario D
  python scripts/view_results.py --date 2025-08-05 --scenario D --preview 20 --top 5  # show first 20 trades + top/bottom 5

What it does:
- Finds results at out/YYYYMMDD/<SCENARIO>/results_YYYY-MM-DD.csv
- Prints an overview table across all scenarios (trades, wins, win%, total PnL)
- For a single scenario: prints per-trade preview, outcome breakdown, and top winners/losers
- No external libraries required (pure Python)
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Dict, List, Tuple

SCENARIO_GUESS = ["A","B","C","D","E","E2","E_cfg","E_cfg2","E_vwapoff","E_debug"]

def yyyymmdd(date_str: str) -> str:
    return date_str.replace("-", "")

def results_path(date_str: str, scenario: str) -> Path:
    base = Path("out") / yyyymmdd(date_str) / scenario.upper()
    return base / f"results_{date_str}.csv"

def load_rows(path: Path) -> List[Dict[str,str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="ignore") as f:
        return list(csv.DictReader(f))

def summarize(rows: List[Dict[str,str]]) -> Tuple[int,int,float,float,Dict[str,int]]:
    """Return (n_trades, n_wins_TP, win_pct_TP, total_pnl, outcome_counts)."""
    n = len(rows)
    outcome_counts: Dict[str,int] = {}
    total_pnl = 0.0
    wins = 0
    for r in rows:
        oc = (r.get("outcome") or "").strip()
        if oc:
            outcome_counts[oc] = outcome_counts.get(oc, 0) + 1
        try:
            total_pnl += float(r.get("pnl") or 0.0)
        except Exception:
            pass
        if oc == "TP":
            wins += 1
    win_pct = (100.0*wins/n) if n else 0.0
    return n, wins, win_pct, total_pnl, outcome_counts

def print_overview(date_str: str) -> None:
    out_root = Path("out") / yyyymmdd(date_str)
    if not out_root.exists():
        print(f"[ERR] No results folder: {out_root}")
        return
    # discover scenarios present
    scenarios = [p.name for p in out_root.iterdir() if p.is_dir()]
    # keep a friendly order
    scenarios = sorted(scenarios, key=lambda s: (SCENARIO_GUESS.index(s) if s in SCENARIO_GUESS else 999, s))

    print(f"\n== Overview {date_str} ==\nScenario   Trades   Wins   Win%    TotalPnL")
    print("---------  ------   ----   -----   --------")
    for sc in scenarios:
        rp = results_path(date_str, sc)
        rows = load_rows(rp)
        n, wins, win_pct, total_pnl, _ = summarize(rows)
        if n == 0:
            continue
        print(f"{sc:<9}  {n:>6}   {wins:>4}   {win_pct:>5.2f}   {total_pnl:>8.2f}")
    print()

def print_detail(date_str: str, scenario: str, preview: int = 0, top: int = 5) -> None:
    sc = scenario.upper()
    rp = results_path(date_str, sc)
    rows = load_rows(rp)
    if not rows:
        print(f"[ERR] No rows found for {sc} at {rp}")
        return
    n, wins, win_pct, total_pnl, outcome_counts = summarize(rows)
    print(f"\n== {sc} detail for {date_str} ==")
    print(f"File: {rp}")
    print(f"Trades: {n}  Wins (TP): {wins}  Win% (TP): {win_pct:.2f}  TotalPnL: {total_pnl:.2f}")
    print(f"By outcome: {outcome_counts}\n")

    if preview > 0:
        print(f"-- First {preview} trades --")
        head = rows[:preview]
        # print common columns if present
        common_cols = [c for c in ["symbol","outcome","pnl","entry_time","exit_time","entry","exit"] if c in rows[0]]
        if not common_cols:
            common_cols = list(rows[0].keys())[:6]
        print(", ".join(common_cols))
        for r in head:
            print(", ".join(str(r.get(c,"")) for c in common_cols))
        print()

    # Winners and losers
    try:
        pnl_pairs = [(r.get("symbol",""), float(r.get("pnl") or 0.0)) for r in rows]
    except Exception:
        pnl_pairs = [(r.get("symbol",""), 0.0) for r in rows]

    pnl_pairs_sorted = sorted(pnl_pairs, key=lambda x: x[1])
    losers = pnl_pairs_sorted[:top]
    winners = list(reversed(pnl_pairs_sorted))[:top]

    print(f"-- Top {top} winners --")
    for sym, pnl in winners:
        print(f"{sym:<10} {pnl:>8.2f}")
    print(f"\n-- Top {top} losers --")
    for sym, pnl in losers:
        print(f"{sym:<10} {pnl:>8.2f}")
    print()

def main():
    ap = argparse.ArgumentParser(description="Simple viewer for Midas_V2 backtest results (pure Python).")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--scenario", default="ALL", help="Scenario code (A,B,C,D,E,...) or ALL")
    ap.add_argument("--preview", type=int, default=0, help="For single-scenario view: show first N trades")
    ap.add_argument("--top", type=int, default=5, help="Show top/bottom N by PnL (single-scenario)")
    args = ap.parse_args()

    if args.scenario.upper() == "ALL":
        print_overview(args.date)
        # optionally also show D detail if present
        rp = results_path(args.date, "D")
        if rp.exists():
            print_detail(args.date, "D", preview=min(args.preview, 20) if args.preview else 0, top=args.top)
    else:
        print_detail(args.date, args.scenario, preview=args.preview, top=args.top)

if __name__ == "__main__":
    main()
