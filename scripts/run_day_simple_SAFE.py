#!/usr/bin/env python3
"""
Simple one-command day runner (SAFE)

Pipeline:
1) Top gappers -> data/samples/universe_sample.txt
2) Fetch minutes for the day
3) Backtest Scenario to out/<YYYYMMDD>/<SCENARIO>
4) Summarize (writes _final/ authoritative one-pager)

Also: forwards RVOL flags (--min-rvol-open, --rvol-open-minutes) to CLI,
and writes out/<YYYYMMDD>/_last_cfg.json so the summarizer footer shows run knobs.
"""

import os, sys, argparse, pathlib, subprocess, json

def sh(args, env=None):
    print("[CMD]", " ".join(args))
    return subprocess.run(args, check=False, env=env)

def ensure_dir(p: pathlib.Path):
    p.mkdir(parents=True, exist_ok=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--scenario", required=True, help="Scenario (A, B, C, D, E)")
    # Optional RVOL gate passthrough
    ap.add_argument("--min-rvol-open", type=float, default=None,
                    help="Opening RVOL gate (e.g., 1.5 = 50% > prior day first N minutes).")
    ap.add_argument("--rvol-open-minutes", type=int, default=15,
                    help="Minutes window used by RVOL comparison (default 15).")
    # Optional guardrails – keep aligned with CLI defaults (printed by CLI banner)
    ap.add_argument("--max-trades-per-symbol", type=int, default=1)
    ap.add_argument("--daily-max-loss", type=float, default=1000.0)
    args = ap.parse_args()

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    src_dir = str(repo_root / "src")
    env = os.environ.copy()
    env["PYTHONPATH"] = src_dir + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    date = args.date
    ymd = date.replace("-", "")
    out_day_dir = repo_root / "out" / ymd
    ensure_dir(out_day_dir)

    # 1) top gappers
    sh([sys.executable, "scripts/topgappers.py", "--date", date], env=env)
    universe = repo_root / "data" / "samples" / "universe_sample.txt"

    # 2) minutes
    sh([sys.executable, "scripts/fetch_minutes_polygon.py", "--date", date, "--session", "rth"], env=env)

    # 3) write params snapshot (for summarizer footer)
    snapshot = {
        "date": date,
        "scenario": args.scenario,
        "min_rvol_open": args.min_rvol_open,
        "rvol_open_minutes": args.rvol_open_minutes,
        "max_trades_per_symbol": args.max_trades_per_symbol,
        "daily_max_loss": args.daily_max_loss,
    }
    (out_day_dir / "_last_cfg.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    # 4) backtest
    out_dir = out_day_dir / args.scenario
    ensure_dir(out_dir)
    cmd = [sys.executable, "-m", "midas_v2.cli", "backtest",
           "--date", date, "--scenario", args.scenario,
           "--universe", str(universe), "--out", str(out_dir),
           "--max-trades-per-symbol", str(args.max_trades_per_symbol),
           "--daily-max-loss", str(args.daily_max_loss)]
    if args.min_rvol_open is not None:
        cmd += ["--min-rvol-open", str(args.min_rvol_open),
                "--rvol-open-minutes", str(args.rvol_open_minutes)]
    sh(cmd, env=env)

    # 5) summarize (prints + authoritative one-pager)
    sh([sys.executable, "scripts/summarize_results.py", "--date", date], env=env)

if __name__ == "__main__":
    main()