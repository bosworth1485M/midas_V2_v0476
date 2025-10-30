#!/usr/bin/env python3
"""
Run the full catalyst flow (steps 1→5) for one day or a date range.

Steps:
  1) topgappers.py               -> data/raw/universe_topgappers_<DATE>.txt
  2) enrich_universe_catalyst.py -> data/catalyst/catalyst_only_<DATE>.txt + catalyst_news_<DATE>.csv
  2.5) catalyst_filter.py (optional) -> catalyst_news_<DATE>_filtered.csv
  3) compose_universe_hybrid.py  -> data/catalyst/universe_hybrid_<DATE>.txt
  4) run_day_catalyst.py         -> out/<YYYYMMDD>/<SCENARIO>_hybrid/...
  5) write_compare_bundle.py     -> out/<YYYYMMDD>/_comparisons/summary_*.txt + comparison_*.json

Examples:
  Single day (news-first, score≥1, Top-12, band 10–40, RVOL≥1.5):
    python scripts/run_catalyst_flow.py --date 2025-08-06 --scenario B --news-first --require-news \
      --news-min-score 1 --top 12 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 1.5 \
      --deny-negative --exclude-china --compare --compare-label B_newsOnly_s1_top12_bandRVOL

  Range:
    python scripts/run_catalyst_flow.py --start 2025-08-05 --end 2025-08-07 --scenario D --news-first --top 12
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parents[1]


def sh(cmd, env=None):
    print("[CMD]", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True, env=env)


def parse_date(s: str):
    return datetime.strptime(s, "%Y-%m-%d").date()


def date_iter(single=None, start=None, end=None):
    if single:
        yield single
        return
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def ensure_env():
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    return env


def build_paths(d):
    ds = d.isoformat()
    ymd = ds.replace("-", "")
    raw_txt    = ROOT / f"data/raw/universe_topgappers_{ds}.txt"
    kept_txt   = ROOT / f"data/catalyst/catalyst_only_{ds}.txt"
    news_csv   = ROOT / f"data/catalyst/catalyst_news_{ds}.csv"
    news_csv_f = ROOT / f"data/catalyst/catalyst_news_{ds}_filtered.csv"
    hybrid_txt = ROOT / f"data/catalyst/universe_hybrid_{ds}.txt"
    out_dir    = ROOT / f"out/{ymd}"
    return ds, ymd, raw_txt, kept_txt, news_csv, news_csv_f, hybrid_txt, out_dir


def main():
    ap = argparse.ArgumentParser(description="Run topgappers → enrich → (optional filter) → compose → run-day (+compare).")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--date", help="YYYY-MM-DD (single day)")
    grp.add_argument("--start", help="YYYY-MM-DD (range start)")
    ap.add_argument("--end", help="YYYY-MM-DD (range end; required with --start)")

    ap.add_argument("--scenario", default="B", help="Scenario (default: B)")

    # Runner knobs
    ap.add_argument("--news-first", action="store_true")
    ap.add_argument("--require-news", action="store_true")
    ap.add_argument("--news-min-score", type=float, default=1.0)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--enforce-band", action="store_true")
    ap.add_argument("--extra-exclude", default=None, help="Comma-separated tickers to exclude in the day runner.")
    ap.add_argument("--no-exclude", action="store_true", help="Disable built-in excludes.")

    # NEW: pass-through numeric knobs to the day runner (kept default None to avoid behavior changes)
    ap.add_argument("--band-min", type=float, default=None, help="Minimum allowed gap%% band (e.g., 10).")
    ap.add_argument("--band-max", type=float, default=None, help="Maximum allowed gap%% band (e.g., 40).")
    ap.add_argument("--min-rvol-open", type=float, default=None, help="Opening RVOL gate (e.g., 1.5 for ≥150%).")

    # Optional filter knobs (call catalyst_filter.py)
    ap.add_argument("--deny-negative", action="store_true", help="Filter out negative headlines via catalyst_filter.py")
    ap.add_argument("--exclude-china", action="store_true", help="Exclude China tickers via catalyst_filter.py")
    ap.add_argument("--neg-terms-file", type=str, default="data/catalyst/neg_terms.txt")
    ap.add_argument("--china-list-file", type=str, default="data/deny/china_tickers.txt")

    # Rebuild policy for steps 1 & 2
    ap.add_argument("--no-rebuild", action="store_true", help="Skip rebuilding 1 & 2 if files already exist")
    ap.add_argument("--print-news", action="store_true", help="Ask enrich step to print headlines")

    # comparison bundle options (calls helper script after the run)
    ap.add_argument("--compare", action="store_true",
                    help="Write TXT+JSON comparison bundle under out/YYYMMDD/_comparisons via helper")
    ap.add_argument("--compare-label", type=str, default=None,
                    help="Optional human label recorded inside the bundle")

    args = ap.parse_args()
    env = ensure_env()

    # Resolve dates
    if args.date:
        rng = date_iter(single=parse_date(args.date))
    else:
        if not args.end:
            ap.error("--end is required when using --start")
        start = parse_date(args.start)
        end = parse_date(args.end)
        if end < start:
            ap.error("--end must be >= --start")
        rng = date_iter(start=start, end=end)

    do_rebuild = not args.no_rebuild

    for d in rng:
        ds, ymd, raw_txt, kept_txt, news_csv, news_csv_f, hybrid_txt, out_dir = build_paths(d)
        print(f"\n==== {ds} | scenario={args.scenario} | rebuild={'YES' if do_rebuild else 'no'} ====")

        # 1) topgappers (writes RAW TXT)
        if do_rebuild or not raw_txt.exists():
            raw_txt.parent.mkdir(parents=True, exist_ok=True)
            sh([
                sys.executable, str(ROOT / "scripts" / "topgappers.py"),
                "--date", ds,
                "--scenario", args.scenario,
                "--out", str(raw_txt),
                "--top", "0"  # full list
            ], env)
        else:
            print(f"[SKIP] topgappers: {raw_txt}")

        # 2) enrich (writes kept + canonical news CSV)
        if do_rebuild or not news_csv.exists():
            kept_txt.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                sys.executable, str(ROOT / "scripts" / "enrich_universe_catalyst.py"),
                "--date", ds,
                "--in", str(raw_txt),
                "--out", str(kept_txt),
            ]
            if args.print_news:
                cmd.append("--print-news")
            sh(cmd, env)
        else:
            print(f"[SKIP] enrich: {news_csv}")

        # 2.5) optional filter (produce *_filtered.csv)
        news_for_run = news_csv
        if news_csv.exists() and (args.deny_negative or args.exclude_china):
            cmd = [
                sys.executable, str(ROOT / "scripts" / "catalyst_filter.py"),
                "--in", str(news_csv),
                "--out", str(news_csv_f),
            ]
            if args.deny_negative:  cmd.append("--deny-negative")
            if args.exclude_china:  cmd.append("--exclude-china")
            if args.neg_terms_file: cmd += ["--neg-terms-file", args.neg_terms_file]
            if args.china_list_file: cmd += ["--china-list-file", args.china_list_file]
            sh(cmd, env)
            news_for_run = news_csv_f
        else:
            print("[FILTER] Skipped (no filters active or news CSV missing).")

        # 3) compose (NO --news flag here; universe is a hybrid of raw + kept, trimmed to Top-N)
        sh([
            sys.executable, str(ROOT / "scripts" / "compose_universe_hybrid.py"),
            "--date", ds,
            "--raw", str(raw_txt),
            "--catalyst", str(kept_txt),
            "--top", str(args.top),
            "--out", str(hybrid_txt)
        ], env)

        # 4) run the day (pass filtered news + knobs to the runner)
        run_cmd = [
            sys.executable, str(ROOT / "scripts" / "run_day_catalyst.py"),
            "--date", ds,
            "--scenario", args.scenario,
            "--universe", str(hybrid_txt),
            "--catalyst", str(news_for_run),
            "--news-min-score", str(args.news_min_score),
        ]
        if args.news_first:    run_cmd.append("--news-first")
        if args.require_news:  run_cmd.append("--require-news")
        if args.top and args.top > 0: run_cmd += ["--top", str(args.top)]
        if args.enforce_band:  run_cmd.append("--enforce-band")
        if args.extra_exclude: run_cmd += ["--extra-exclude", args.extra_exclude]
        if args.no_exclude:    run_cmd.append("--no-exclude")

        # NEW: forward numeric knobs only if provided (avoid changing default behavior)
        if args.band_min is not None:      run_cmd += ["--band-min", str(args.band_min)]
        if args.band_max is not None:      run_cmd += ["--band-max", str(args.band_max)]
        if args.min_rvol_open is not None: run_cmd += ["--min-rvol-open", str(args.min_rvol_open)]

        sh(run_cmd, env)

        # 5) (Optional) write comparison bundle via helper
        if args.compare:
            summary_src = ROOT / f"out/{ymd}/{args.scenario}_hybrid/summary_hybrid_{ds}.txt"
            cmp_dir     = ROOT / f"out/{ymd}/_comparisons"
            cmd_cmp = [
                sys.executable, str(ROOT / "scripts" / "write_compare_bundle.py"),
                "--date", ds,
                "--scenario", args.scenario,
                "--summary", str(summary_src),
                "--universe", str(hybrid_txt),
                "--catalyst-csv", str(news_for_run),
                "--out-dir", str(cmp_dir)
            ]
            if args.compare_label:
                cmd_cmp += ["--label", args.compare_label]

            # Pass through active knobs so JSON shows real values (no nulls)
            if args.band_min is not None:       cmd_cmp += ["--band-min", str(args.band_min)]
            if args.band_max is not None:       cmd_cmp += ["--band-max", str(args.band_max)]
            if args.min_rvol_open is not None:  cmd_cmp += ["--min-rvol-open", str(args.min_rvol_open)]
            if args.news_first:                 cmd_cmp.append("--news-first")
            if args.require_news:               cmd_cmp.append("--require-news")
            if args.enforce_band:               cmd_cmp.append("--enforce-band")
            if args.top is not None:            cmd_cmp += ["--top", str(args.top)]
            if args.news_min_score is not None: cmd_cmp += ["--news-min-score", str(args.news_min_score)]
            if args.deny_negative:              cmd_cmp.append("--deny-negative")
            if args.exclude_china:              cmd_cmp.append("--exclude-china")

            sh(cmd_cmp, env)


if __name__ == "__main__":
    main()