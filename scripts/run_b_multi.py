#!/usr/bin/env python
"""
Run Scenario B for multiple dates.

Usage:
  python scripts/run_b_multi.py 2025-08-05 2025-08-06 2025-08-07
"""
import sys, subprocess, os

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_b_multi.py YYYY-MM-DD [YYYY-MM-DD ...]")
        sys.exit(1)

    dates = sys.argv[1:]
    for d in dates:
        outdir = os.path.join("out", d.replace("-", ""), "B")
        cmd = [
            sys.executable, "-m", "midas_v2.cli", "backtest",
            "--date", d,
            "--scenario", "B",
            "--universe", "data/samples/universe_sample.txt",
            "--out", outdir,
            "--max-trades-per-symbol", "1",
            "--daily-max-loss", "1000"
        ]
        print("[RUN]", " ".join(cmd))
        ret = subprocess.call(cmd)
        if ret != 0:
            print(f"[WARN] Backtest for {d} exited with code {ret}")

if __name__ == "__main__":
    main()