#!/usr/bin/env python3
"""
Run the full catalyst flow (steps 1→4) for one day or a date range.

Steps:
  1) topgappers.py               -> data/raw/universe_topgappers_<DATE>.txt
  2) enrich_universe_catalyst.py -> data/catalyst/catalyst_only_<DATE>.txt + catalyst_news_<DATE>.csv
  3) compose_universe_hybrid.py  -> data/catalyst/universe_hybrid_<DATE>.txt
     (NOTE: we pass the FULL RAW file path here)
  4) run_day_catalyst.py         -> out/<YYYYMMDD>/<SCENARIO>_hybrid/...

Usage examples:
  Single day:
    python scripts/run_catalyst_flow.py --date 2025-08-05 --scenario B --news-first --news-min-score 1 --top 12 --enforce-band

  Date range:
    python scripts/run_catalyst_flow.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --news-min-score 1 --top 12 --enforce-band
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
    hybrid_txt = ROOT / f"data/catalyst/universe_hybrid_{ds}.txt"
    out_dir    = ROOT / f"out/{ymd}"
    return ds, ymd, raw_txt, kept_txt, news_csv, hybrid_txt, out_dir


def main():
    ap = argparse.ArgumentParser(description="Run topgappers → enrich → compose → run-day (full RAW path to compose).")
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
    ap.add_argument("--extra-exclude", default=None)
    ap.add_argument("--no-exclude", action="store_true")

    # Rebuild policy for steps 1 & 2
    ap.add_argument("--no-rebuild", action="store_true", help="Skip rebuilding 1 & 2 if files already exist")
    ap.add_argument("--print-news", action="store_true", help="Ask enrich step to print headlines")

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
        ds, ymd, raw_txt, kept_txt, news_csv, hybrid_txt, out_dir = build_paths(d)
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

        # 3) compose (PASS FULL RAW FILE PATH HERE — the path fix)
        sh([
            sys.executable, str(ROOT / "scripts" / "compose_universe_hybrid.py"),
            "--date", ds,
            "--raw", str(raw_txt),                  # <-- full file (fix)
            "--catalyst", str(kept_txt),
            "--top", str(args.top),
            "--out", str(hybrid_txt)
        ], env)

        # 4) run the day
        run_cmd = [
            sys.executable, str(ROOT / "scripts" / "run_day_catalyst.py"),
            "--date", ds,
            "--scenario", args.scenario,
            "--universe", str(hybrid_txt),
            "--catalyst", str(news_csv),
            "--news-min-score", str(args.news_min_score),
        ]
        if args.news_first:   run_cmd.append("--news-first")
        if args.require_news: run_cmd.append("--require-news")
        if args.top and args.top > 0: run_cmd += ["--top", str(args.top)]
        if args.enforce_band: run_cmd.append("--enforce-band")
        if args.extra_exclude: run_cmd += ["--extra-exclude", args.extra_exclude]
        if args.no_exclude:    run_cmd.append("--no-exclude")

        sh(run_cmd, env)


if __name__ == "__main__":
    main()