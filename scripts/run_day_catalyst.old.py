#!/usr/bin/env python3
# Run a single day using a supplied universe file (no enrichment step).
# Usage:
#   python scripts/run_day_catalyst.py --date 2025-08-05 --scenario D --universe data\universe_active.txt
#   python scripts/run_day_catalyst.py --date 2025-08-05 --scenario D --universe data\universe_active.txt --fetch-minutes

import argparse, os, shutil, subprocess, sys
from pathlib import Path
from datetime import datetime

REPO = Path(__file__).resolve().parents[1]
SRC  = REPO / "src"        # ensure package import
DEFAULT_UNIVERSE = REPO / "data" / "samples" / "universe_sample.txt"

def parse_args():
    ap = argparse.ArgumentParser(description="Run backtest for a given day using a supplied universe file.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--scenario", required=True, help="Scenario (e.g., D or E)")
    ap.add_argument("--universe", required=True, help="Path to a text file with one symbol per line")
    ap.add_argument("--fetch-minutes", action="store_true", help="Fetch minutes for the supplied universe before backtest")
    ap.add_argument("--session", default="rth", choices=["rth", "all"], help="Session for minute fetch (default rth)")
    return ap.parse_args()

def yyyymmdd(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y%m%d")

def repo_env():
    env = os.environ.copy()
    # Make sure the package is importable: src/ must be on PYTHONPATH
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    return env

def fetch_minutes(date_str: str, session: str, universe_path: Path):
    # Temporarily swap the universe so fetch_minutes_polygon.py pulls the right symbols
    backup = None
    if DEFAULT_UNIVERSE.exists():
        backup = DEFAULT_UNIVERSE.with_suffix(".bak")
        shutil.copy2(DEFAULT_UNIVERSE, backup)
    shutil.copy2(universe_path, DEFAULT_UNIVERSE)
    try:
        cmd = [sys.executable, str(REPO / "scripts" / "fetch_minutes_polygon.py"),
               "--date", date_str, "--session", session]
        print("[CMD]", " ".join(cmd))
        cp = subprocess.run(cmd, text=True, capture_output=True, env=repo_env())
        print(cp.stdout)
        if cp.returncode != 0:
            print(cp.stderr)
            raise SystemExit(f"Minute fetch failed (exit {cp.returncode})")
    finally:
        if backup and backup.exists():
            shutil.copy2(backup, DEFAULT_UNIVERSE)
            try: backup.unlink()
            except: pass

def run_backtest(date_str: str, scenario: str, universe_path: Path):
    out_dir = REPO / "out" / yyyymmdd(date_str) / scenario
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, "-m", "midas_v2.cli", "backtest",
        "--date", date_str,
        "--scenario", scenario,
        "--universe", str(universe_path),
        "--out", str(out_dir),
    ]
    print("[CMD]", " ".join(cmd))
    cp = subprocess.run(cmd, text=True, capture_output=True, env=repo_env())
    print(cp.stdout)
    if cp.returncode != 0:
        print(cp.stderr)
        raise SystemExit(f"Backtest failed (exit {cp.returncode})")
    results = out_dir / f"results_{date_str}.csv"
    if results.exists():
        print("[OK] Backtest complete ->", results)
    else:
        print("[INFO] No results file found in", out_dir)

def auto_summarize(date_str: str, scenario: str):
    """
    Calls summarize_results.py for the given date and writes:
      - summary_YYYY-MM-DD.txt            (full per-date summary)
      - summary_only_YYYY-MM-DD.txt       (just this scenario's line, if present)
    so the user always sees fresh, trustworthy results.
    """
    # Run the summarizer
    cmd = [sys.executable, str(REPO / "scripts" / "summarize_results.py"), "--date", date_str]
    try:
        out_txt = subprocess.check_output(cmd, text=True, env=repo_env())
    except subprocess.CalledProcessError as e:
        out_txt = f"[ERROR] summarize_results failed for {date_str}: {e}\n"
        print(out_txt, file=sys.stderr)

    # Write per-scenario directory files
    ymd = yyyymmdd(date_str)
    scen_dir = REPO / "out" / ymd / scenario
    scen_dir.mkdir(parents=True, exist_ok=True)

    full_summary_path = scen_dir / f"summary_{date_str}.txt"
    full_summary_path.write_text(out_txt, encoding="utf-8")

    # Extract only this scenario's line (e.g., "D: TP=... SL=... Win%=...")
    scen_line = ""
    for line in out_txt.splitlines():
        if line.strip().startswith(f"{scenario}:"):
            scen_line = line.strip()
            break
    only_summary_path = scen_dir / f"summary_only_{date_str}.txt"
    only_summary_path.write_text((scen_line + "\n") if scen_line else out_txt, encoding="utf-8")

    print(f"[SUMMARY] Wrote fresh summaries -> {full_summary_path.name}, {only_summary_path.name}")

def main():
    args = parse_args()
    universe_path = Path(args.universe).resolve()
    if not universe_path.exists():
        raise SystemExit(f"Universe not found: {universe_path}")

    print(f"[CATALYST-DAY] date={args.date} scenario={args.scenario} universe={universe_path.name}")

    if args.fetch_minutes:
        fetch_minutes(args.date, args.session, universe_path)

    run_backtest(args.date, args.scenario, universe_path)
    # Auto-summarize so the viewed summary is always current
    auto_summarize(args.date, args.scenario)
    print("[DONE] Day run finished.")

if __name__ == "__main__":
    main()
