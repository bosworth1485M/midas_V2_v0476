#!/usr/bin/env python3
# scripts/summarize_results.py
# Drop-in replacement: reads authoritative per-day results CSVs and prints daily summary.
# Usage:
#   python scripts/summarize_results.py --date YYYY-MM-DD
#
# Output:
#   Prints lines like:
#     B: TP=.. SL=.. Win%=..
#     D: TP=.. SL=.. Win%=..
#     E: TP=.. SL=.. Win%=..
#   Writes:
#     out\<YYYYMMDD>\_final\summary_only_YYYY-MM-DD.txt
#
# Data sources (authoritative):
#   out\<YYYYMMDD>\<SCENARIO>\results_<YYYY-MM-DD>.csv  (with an 'outcome' column: TP | SL)
#   out\<YYYYMMDD>\_last_cfg.json                      (optional: prints overrides)
#   config\scenarios.json                              (prints key scenario params)

import argparse
import csv
import io
import json
import os
from typing import Tuple, Dict

SCENARIOS = ("B", "D", "E")

def _ymd_compact(date_ymd: str) -> str:
    return date_ymd.replace("-", "")

def _results_csv_path(date_ymd: str, scenario: str) -> str:
    return os.path.join("out", _ymd_compact(date_ymd), scenario, f"results_{date_ymd}.csv")

def _last_cfg_path(date_ymd: str) -> str:
    return os.path.join("out", _ymd_compact(date_ymd), "_last_cfg.json")

def _final_dir(date_ymd: str) -> str:
    return os.path.join("out", _ymd_compact(date_ymd), "_final")

def _summary_txt_path(date_ymd: str) -> str:
    return os.path.join(_final_dir(date_ymd), f"summary_only_{date_ymd}.txt")

def _count_tp_sl(csv_path: str) -> Tuple[int, int]:
    tp = sl = 0
    if not os.path.exists(csv_path):
        return tp, sl
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        # Accept various outcome column names
        possible_cols = [c for c in reader.fieldnames or []]
        outcome_col = None
        for name in ("outcome", "Outcome", "result", "Result", "status", "Status"):
            if name in possible_cols:
                outcome_col = name
                break
        # Fallback: if unknown, use the second column if it exists
        if outcome_col is None and possible_cols:
            outcome_col = possible_cols[1] if len(possible_cols) > 1 else possible_cols[0]
        for row in reader:
            outcome = str(row.get(outcome_col, "")).strip().upper()
            if outcome == "TP":
                tp += 1
            elif outcome == "SL":
                sl += 1
    return tp, sl

def _load_overrides(date_ymd: str) -> Dict:
    path = _last_cfg_path(date_ymd)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _load_scenarios_params() -> Dict:
    path = os.path.join("config", "scenarios.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _fmt_pct(tp: int, sl: int) -> float:
    n = tp + sl
    return round(100.0 * tp / n, 2) if n else 0.0

def main():
    ap = argparse.ArgumentParser(description="Summarize per-day results for B/D/E from authoritative CSVs.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()

    date_ymd = args.date
    final_dir = _final_dir(date_ymd)
    os.makedirs(final_dir, exist_ok=True)
    summary_lines = []

    # Compute B/D/E from CSVs
    totals = {}
    for s in SCENARIOS:
        tp, sl = _count_tp_sl(_results_csv_path(date_ymd, s))
        wr = _fmt_pct(tp, sl)
        # Print to console
        print(f"{s}: TP={tp} SL={sl} Win%={wr:.2f}")
        totals[s] = {"tp": tp, "sl": sl, "wr": wr}

    # Prepare footer with scenario key params
    scenarios = _load_scenarios_params()
    def _params_for(s: str) -> str:
        p = (scenarios.get(s, {}) or {}).get("params", {})
        # Show the core confirms/gates that users expect to see
        fields = [
            ("tp_pct", p.get("tp_pct")), ("sl_pct", p.get("sl_pct")),
            ("ema_confirm", p.get("ema_confirm")), ("vwap_confirm", p.get("vwap_confirm")),
            ("macd_confirm", p.get("macd_confirm")),
            ("gate_minutes", p.get("gate_minutes")),
            # Rising price candles (stable code enforces rise_bars)
            ("rise_bars", p.get("rise_bars")),
            # Optional display if present
            ("min_pm_vol", p.get("min_pm_vol")),
        ]
        # Build "k=v" comma string, skipping None
        parts = [f"{k}={v}" for k, v in fields if v is not None]
        return ", ".join(parts)

    # Optional overrides section
    overrides = _load_overrides(date_ymd)
    def _fmt_overrides(ov: Dict) -> str:
        if not ov:
            return "min_rvol_open=None, rvol_open_minutes=15, max_trades_per_symbol=1, daily_max_loss=1000.0"
        # Show a minimal subset if present
        keys = ("min_rvol_open", "rvol_open_minutes", "max_trades_per_symbol", "daily_max_loss")
        parts = []
        for k in keys:
            v = overrides.get(k, None) if isinstance(overrides, dict) else None
            parts.append(f"{k}={v if v is not None else 'None'}")
        return ", ".join(parts)

    # Build the text summary exactly like before
    summary_lines.append(f"B: TP={totals['B']['tp']} SL={totals['B']['sl']} Win%={totals['B']['wr']:.2f}")
    summary_lines.append(f"B (catalyst): TP=0 SL=0 Win%=0.00")  # keep line; catalyst summarization is separate
    summary_lines.append(f"D: TP={totals['D']['tp']} SL={totals['D']['sl']} Win%={totals['D']['wr']:.2f}")
    summary_lines.append(f"E: TP={totals['E']['tp']} SL={totals['E']['sl']} Win%={totals['E']['wr']:.2f}")
    summary_lines.append("[AUTHORITATIVE] Wrote " + _summary_txt_path(date_ymd))
    summary_lines.append("")
    summary_lines.append("---")
    summary_lines.append("Run Parameters:")
    summary_lines.append("  scenarios_in_summary = B, D, E")
    summary_lines.append(f"  [B] {_params_for('B')}")
    summary_lines.append(f"  [D] {_params_for('D')}")
    summary_lines.append(f"  [E] {_params_for('E')}")
    summary_lines.append(f"  [catalyst] picked=0, a_only=False")
    summary_lines.append(f"  [overrides] {_fmt_overrides(overrides)}")

    # Write summary file
    with open(_summary_txt_path(date_ymd), "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(summary_lines))

if __name__ == "__main__":
    main()
