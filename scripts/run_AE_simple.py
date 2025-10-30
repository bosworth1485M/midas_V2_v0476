# scripts/run_AE_simple.py
# Run scenarios A–E (or any list) and print a summary.
# Usage:
#   python scripts/run_AE_simple.py --date 2025-08-05
#   python scripts/run_AE_simple.py --date 2025-08-05 --scenarios E
#   python scripts/run_AE_simple.py --date 2025-08-05 --scenarios A,B,C,D,E --universe data/samples/universe_sample.txt

import argparse, subprocess, os, csv

def main():
    ap = argparse.ArgumentParser(description="Run scenarios and summarize results.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--universe", default="data/samples/universe_sample.txt")
    ap.add_argument("--scenarios", default="A,B,C,D,E", help="Comma-separated list (default: A,B,C,D,E)")
    ap.add_argument("--out-root", default="out")
    args = ap.parse_args()

    day = args.date
    d8  = day.replace("-", "")
    scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()]

    # Run each scenario
    for s in scenarios:
        out_dir = os.path.join(args.out_root, d8, s)
        cmd = [
            "python", "-m", "midas_v2.cli", "backtest",
            "--date", day, "--scenario", s,
            "--universe", args.universe,
            "--out", out_dir,
        ]
        print("RUN:", " ".join(cmd))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print(f"[ERR] scenario {s} exited with code {r.returncode}")

    # Summarize
    print("\nSummary:")
    for s in scenarios:
        path = os.path.join(args.out_root, d8, s, f"results_{day}.csv")
        if not os.path.exists(path):
            print(f"{s}: (no results)")
            continue
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
        tp  = sum(1 for r in rows if r.get("outcome") == "TP")
        sl  = sum(1 for r in rows if r.get("outcome") == "SL")
        tot = tp + sl
        win = round(100 * tp / tot, 2) if tot > 0 else 0
        print(f"{s}: TP={tp} SL={sl} Win%={win}")

if __name__ == "__main__":
    main()