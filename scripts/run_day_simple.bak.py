#!/usr/bin/env python3
"""
Midas_V2 helper: run_day_simple.py

Minimal runner: only --date and --scenario are required.
Now also auto-saves a summary into the scenario folder.
"""

from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data" / "samples"
UNIVERSE_PATH = DATA / "universe_sample.txt"
OUT = ROOT / "out"


def run(cmd: list[str]) -> None:
    """Run a subprocess, echoing the command. Raises on failure."""
    printable = " ".join(cmd)
    print(f"[CMD] {printable}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERR] Command failed (exit {e.returncode}): {printable}")
        sys.exit(e.returncode or 1)


def ensure_dirs(date_str: str, scenario: str) -> Path:
    d8 = date_str.replace("-", "")
    out_dir = OUT / d8 / scenario
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run a single trading day with minimal flags",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--date", required=True, help="Trading date, e.g., 2025-08-07")
    p.add_argument(
        "--scenario",
        required=True,
        choices=["A", "B", "C", "D", "E"],
        help="Backtest scenario",
    )
    # Hidden/advanced knobs with safe defaults
    p.add_argument("--session", default="rth", help=argparse.SUPPRESS)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    date_str = args.date
    scenario = args.scenario.upper()
    session = args.session

    # 0) Sanity check
    for rel in ("scripts/topgappers.py", "scripts/fetch_minutes_polygon.py"):
        f = ROOT / rel
        if not f.exists():
            print(f"[WARN] Expected helper not found: {rel}")

    # 1) Build universe
    run([
        sys.executable,
        str(SCRIPTS / "topgappers.py"),
        "--date", date_str,
        "",
    ])

    if UNIVERSE_PATH.exists():
        n = sum(1 for _ in UNIVERSE_PATH.open("r", encoding="utf-8", errors="ignore"))
        print(f"[UNIVERSE] {UNIVERSE_PATH} has {n} symbols")
    else:
        print(f"[WARN] Universe file not found: {UNIVERSE_PATH}")

    # 2) Fetch minute data
    run([
        sys.executable,
        str(SCRIPTS / "fetch_minutes_polygon.py"),
        "--date", date_str,
        "--session", session,
    ])

    # 3) Backtest via CLI
    out_dir = ensure_dirs(date_str, scenario)
    run([
        sys.executable,
        "-m", "midas_v2.cli",
        "backtest",
        "--date", date_str,
        "--scenario", scenario,
        "--universe", str(UNIVERSE_PATH),
        "--out", str(out_dir),
    ])

    # 4) Auto-summarize and save into scenario folder
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "summarize_results.py"), "--date", date_str],
            check=True,
            capture_output=True,
            text=True,
        )
        summary_txt = result.stdout if result.stdout else "(no summary output)\n"
        summary_path = out_dir / f"summary_{date_str}.txt"
        summary_path.write_text(summary_txt, encoding="utf-8")
        print(f"[OK] Summary saved -> {summary_path}")
    except subprocess.CalledProcessError as e:
        print(f"[WARN] summarize_results.py failed (exit {e.returncode}). Skipping save.")

    print("\n[OK] Backtest done.")


if __name__ == "__main__":
    main()