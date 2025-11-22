#!/usr/bin/env python3
"""
Midas_V2 helper: run_day_simple.py (clean rewrite)

- Required: --date, --scenario {A,B,C,D,E}
- Optional: --top N  (trim universe to first N symbols; 0 = keep all)
- Behavior:
  1) Build universe via scripts/topgappers.py (forwards --top if provided)
  2) If universe is empty -> skip day
  3) Fetch minute data via scripts/fetch_minutes_polygon.py
  4) Run backtest via python -m midas_v2.cli backtest
  5) Stream summarize_results.py output to console and also save to summary file
"""

from __future__ import annotations

import os, sys, argparse, subprocess
from subprocess import Popen, PIPE
from pathlib import Path

# --- bootstrap: ensure src on path + load .env from project root ---
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
os.environ["PYTHONPATH"] = str(SRC) + os.pathsep + os.environ.get("PYTHONPATH", "")

try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv(ROOT / ".env")
except Exception as e:
    sys.stderr.write(f"[WARN] dotenv load failed: {e}\n")
# --- end bootstrap ---

SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data" / "samples"
UNIVERSE_PATH = DATA / "universe_sample.txt"
OUT = ROOT / "out"


def run(cmd: list[str]) -> None:
    """Run a subprocess, echoing the command; raise on failure."""
    printable = " ".join(cmd)
    print(f"[CMD] {printable}")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    subprocess.run(cmd, check=True, env=env)


def ensure_out_dir(date_str: str, scenario: str) -> Path:
    d8 = date_str.replace("-", "")
    out_dir = OUT / d8 / scenario
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run a single trading day (clean, safe).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--date", required=True, help="Trading date, e.g., 2025-08-07")
    p.add_argument("--scenario", required=True, choices=["A", "B", "C", "D", "E"])
    p.add_argument("--top", type=int, default=0, help="Trim universe to first N symbols (0 = all)")
    # Hidden/advanced knobs with safe defaults
    p.add_argument("--session", default="rth", help=argparse.SUPPRESS)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    date_str = args.date
    scenario = args.scenario.upper()
    session = args.session

    # 1) Build universe (forward --top if provided)
    top_cmd = [sys.executable, str(SCRIPTS / "topgappers.py"), "--date", date_str]
    if args.top and args.top > 0:
        top_cmd += ["--top", str(args.top)]
    # v0.7.9.6.5: pass scenario through to topgappers so Scenario.params['top'] can override scanner.top_n
    if scenario:
        top_cmd += ["--scenario", scenario]
    run(top_cmd)

    # 1b) Universe sanity
    if UNIVERSE_PATH.exists():
        with UNIVERSE_PATH.open("r", encoding="utf-8", errors="ignore") as f:
            n = sum(1 for _ in f if _.strip())
        print(f"[UNIVERSE] {UNIVERSE_PATH} has {n} symbols")
        if n == 0:
            print(f"[INFO] {date_str}: no symbols met filters (or non-trading day). Skipping.")
            return
    else:
        print(f"[WARN] Universe file not found: {UNIVERSE_PATH}. Skipping.")
        return

    # 2) Fetch minutes
    run([
        sys.executable, str(SCRIPTS / "fetch_minutes_polygon.py"),
        "--date", date_str, "--session", session
    ])

    # 3) Backtest
    out_dir = ensure_out_dir(date_str, scenario)
    run([
        sys.executable, "-m", "midas_v2.cli", "backtest",
        "--date", date_str,
        "--scenario", scenario,
        "--universe", str(UNIVERSE_PATH),
        "--out", str(out_dir),
    ])

    # 4) Stream summarize_results.py and save to file
    summary_path = out_dir / f"summary_{date_str}.txt"
    print("[INFO] Running summarize_results.py and streaming output...")
    with Popen(
        [sys.executable, str(SCRIPTS / "summarize_results.py"), "--date", date_str],
        stdout=PIPE, stderr=PIPE, text=True, env=os.environ.copy()
    ) as proc:
        buf = []
        for line in proc.stdout:
            print(line, end="")
            buf.append(line)
        err = proc.stderr.read()
        rc = proc.wait()
        if rc != 0:
            print(f"[WARN] summarize_results.py failed (exit {rc}). STDERR: {err.strip()}")
        summary_txt = "".join(buf) if buf else "(no summary output)\n"
        summary_path.write_text(summary_txt, encoding="utf-8")
        print(f"[OK] Summary saved -> {summary_path}")

    print("\n[OK] Backtest done.")


if __name__ == "__main__":
    main()
