#!/usr/bin/env python3
# Show the most recent range_summary_*_B.csv as a table.
import argparse, glob, os, csv, sys

DEFAULT_GLOBS = [
    r"out\auto_catalyst\range_summary_*_B.csv",
    r"out/auto_catalyst/range_summary_*_B.csv",
    r"out\auto\range_summary_*_B.csv",
    r"out/auto/range_summary_*_B.csv",
]

def pick_latest(patterns):
    files = []
    for pat in patterns:
        files.extend(glob.glob(pat))
    return max(files, key=os.path.getmtime) if files else None

def print_table(rows, cols):
    widths = [max(len(c), max((len(r.get(c, "")) for r in rows), default=0)) for c in cols]
    header = " | ".join(c.ljust(w) for c, w in zip(cols, widths))
    sep    = "-+-".join("-" * w for w in widths)
    print(header); print(sep)
    for r in rows:
        print(" | ".join((r.get(c, "").ljust(w) for c, w in zip(cols, widths))))

def main():
    ap = argparse.ArgumentParser(description="Show latest range summary CSV.")
    ap.add_argument("--glob", help="Override glob pattern(s), comma-separated", default=None)
    args = ap.parse_args()

    patterns = [p.strip() for p in args.glob.split(",")] if args.glob else DEFAULT_GLOBS
    latest = pick_latest(patterns)
    if not latest:
        print(f"[ERR] No files found matching any of: {patterns}")
        sys.exit(2)

    print(f"[FILE] {latest}")
    with open(latest, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        rows = list(rdr)

    # Preferred columns if present
    want = ["Date", "Scenario", "Used", "WR%", "TP/SL", "PnL"]
    cols = [c for c in want if rows and c in rows[0]]
    if not cols and rows:
        cols = list(rows[0].keys())  # fallback to all columns

    print_table(rows, cols)

if __name__ == "__main__":
    main()