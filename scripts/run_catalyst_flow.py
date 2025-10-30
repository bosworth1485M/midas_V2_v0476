#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
run_catalyst_flow.py — one-day catalyst flow

Steps:
  1) Build raw top gappers list
  2) Enrich catalysts (kept list + news CSV)
  3) Optionally filter catalysts (deny-negative / exclude-china) -> *filtered* CSV
  4) Build FILTERED ticker list from the CSV actually used by the day run (score >= --news-min-score)
  5) Compose hybrid universe using that FILTERED list (fallback to kept list if empty/missing)
  6) Run day backtest
  7) Optionally write compare bundle
"""

from __future__ import annotations

import argparse
import csv
import subprocess as s
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]  # repo root
PY = "python"


def run(cmd: List[str], check: bool = True) -> int:
    print("[CMD]", " ".join(cmd))
    return s.run(cmd, check=check).returncode


def build_filtered_symbol_txt(news_csv_path: Path, date_str: str, min_score: float) -> Optional[Path]:
    """
    Make data/catalyst/catalyst_news_{date}.FILTERED.txt from the CSV that will be used by day-runner.
    Returns FILTERED file path if any symbols meet min_score; else None.
    """
    out_txt = ROOT / f"data/catalyst/catalyst_news_{date_str}.FILTERED.txt"
    try:
        rows = list(csv.DictReader(open(news_csv_path, encoding="utf-8")))
    except FileNotFoundError:
        print(f"[COMPOSE] No CSV at {news_csv_path}; falling back to kept list.")
        return None

    syms = sorted({
        (r.get("symbol", "") or "").strip()
        for r in rows
        if float(r.get("score", 0) or 0) >= float(min_score)
    })
    if syms:
        out_txt.write_text("\n".join([x for x in syms if x]), encoding="utf-8")
        print(f"[COMPOSE] Using filtered catalyst list -> {out_txt} (>= {min_score}) | count={len(syms)}")
        return out_txt

    print("[COMPOSE] 0 symbols met score threshold; will use kept list for compose.")
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--scenario", required=True)

    # Selection knobs
    ap.add_argument("--news-first", action="store_true")
    ap.add_argument("--require-news", action="store_true")
    ap.add_argument("--news-min-score", type=float, default=3.0)
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--enforce-band", action="store_true")
    ap.add_argument("--band-min", type=float, default=10.0)
    ap.add_argument("--band-max", type=float, default=40.0)
    ap.add_argument("--min-rvol-open", type=float, default=2.0)
    ap.add_argument("--gate-minutes", type=int, default=15)

    # Optional filtering flags (for catalyst_filter.py ONLY)
    ap.add_argument("--deny-negative", action="store_true")
    ap.add_argument("--exclude-china", action="store_true")
    ap.add_argument("--neg-terms-file", default="data/catalyst/neg_terms.txt")
    ap.add_argument("--china-list-file", default="data/deny/china_tickers.txt")

    # Optional compare bundle flags
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--compare-label", default=None)

    # Range-runner metadata (accepted & ignored)
    ap.add_argument("--upstream-command", nargs="+", default=None, help="ignored upstream metadata")

    args = ap.parse_args()
    ds = args.date

    out_dir = ROOT / f"out/{ds.replace('-', '')}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[CATALYST-DAY] date={ds} scenario={args.scenario}")

    # 1) RAW top gappers
    raw_txt = ROOT / f"data/raw/universe_topgappers_{ds}.txt"
    run([
        PY, str(ROOT / "scripts/topgappers.py"),
        "--date", ds,
        "--scenario", args.scenario,
        "--out", str(raw_txt),
        "--top", "0"  # keep full list; Top-N is applied in compose/day
    ])

    # 2) Enrich catalysts
    kept_txt = ROOT / f"data/catalyst/catalyst_only_{ds}.txt"
    news_csv = ROOT / f"data/catalyst/catalyst_news_{ds}.csv"
    run([
        PY, str(ROOT / "scripts/enrich_universe_catalyst.py"),
        "--date", ds,
        "--in", str(raw_txt),
        "--out", str(kept_txt),
    ])

    # 2b) Optional filter (deny-negative / exclude-china)
    news_csv_filtered = ROOT / f"data/catalyst/catalyst_news_{ds}_filtered.csv"
    filter_cmd = [
        PY, str(ROOT / "scripts/catalyst_filter.py"),
        "--in", str(news_csv),
        "--out", str(news_csv_filtered),
    ]
    if args.deny_negative:
        filter_cmd.append("--deny-negative")
    if args.exclude_china:
        filter_cmd.append("--exclude-china")
    if args.neg_terms_file:
        filter_cmd += ["--neg-terms-file", str(ROOT / args.neg_terms_file)]
    if args.china_list_file:
        filter_cmd += ["--china-list-file", str(ROOT / args.china_list_file)]
    run(filter_cmd)

    # CSV that the day runner will use (filtered if present)
    news_for_run = news_csv_filtered if news_csv_filtered.exists() else news_csv

    # 3) Build FILTERED list aligned with day-run CSV, then compose hybrid universe
    filtered_txt = build_filtered_symbol_txt(
        news_csv_path=news_for_run,
        date_str=ds,
        min_score=float(args.news_min_score or 1.0)
    )
    use_catalyst_list = filtered_txt if filtered_txt is not None else kept_txt

    uni_txt = ROOT / f"data/catalyst/universe_hybrid_{ds}.txt"
    run([
        PY, str(ROOT / "scripts/compose_universe_hybrid.py"),
        "--date", ds,
        "--raw", str(raw_txt),
        "--catalyst", str(use_catalyst_list),
        "--top", str(args.top),
        "--out", str(uni_txt),
    ])

    # 4) Run the day backtest (NO deny-negative/exclude-china here)
    out_day = ROOT / f"out/{ds.replace('-', '')}/{args.scenario}_hybrid"
    out_day.mkdir(parents=True, exist_ok=True)

    cmd_day = [
        PY, str(ROOT / "scripts/run_day_catalyst.py"),
        "--date", ds,
        "--scenario", args.scenario,
        "--universe", str(uni_txt),
        "--catalyst", str(news_for_run),
    ]
    if args.news_first:
        cmd_day.append("--news-first")
    if args.require_news:
        cmd_day.append("--require-news")
    cmd_day += [
        "--news-min-score", str(args.news_min_score),
        "--top", str(args.top),
    ]
    if args.enforce_band:
        cmd_day.append("--enforce-band")
    cmd_day += [
        "--band-min", str(args.band_min),
        "--band-max", str(args.band_max),
        "--min-rvol-open", str(args.min_rvol_open),
        "--gate-minutes", str(args.gate_minutes),
    ]
    run(cmd_day)

    # 5) Optional compare bundle
    if args.compare:
        bundle_dir = ROOT / f"out/{ds.replace('-', '')}/_comparisons"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        summary_txt = out_day / f"summary_hybrid_{ds}.txt"
        run([
            PY, str(ROOT / "scripts/write_compare_bundle.py"),
            "--date", ds,
            "--scenario", args.scenario,
            "--summary", str(summary_txt),
            "--universe", str(uni_txt),
            "--catalyst-csv", str(news_for_run),
            "--out-dir", str(bundle_dir),
            "--label", str(args.compare_label or "run"),
        ])

    print("[OK] Day flow complete.")


if __name__ == "__main__":
    main()