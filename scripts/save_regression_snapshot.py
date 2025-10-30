# scripts/save_regression_snapshot.py
# Write a regression snapshot CSV for a given date into Docs/.
# Usage:
#   python scripts/save_regression_snapshot.py --date 2025-08-05 --label polygon
# Produces: Docs/REGRESSION_<YYYYMMDD>_AE_<label>.csv

import os, csv, glob, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--label", default="polygon", help="suffix label for file name (default: polygon)")
    ap.add_argument("--outdir", default="Docs", help="output directory (default: Docs)")
    args = ap.parse_args()

    d = args.date
    d8 = d.replace("-", "")
    outdir = args.outdir
    os.makedirs(outdir, exist_ok=True)

    rows = [("Scenario","Trades","TP","SL","WinPct","Path")]
    pattern = os.path.join("out", d8, "*", f"results_{d}.csv")
    for path in sorted(glob.glob(pattern)):
        scenario = os.path.basename(os.path.dirname(path))
        with open(path, newline="") as f:
            data = list(csv.DictReader(f))
        tp = sum(1 for r in data if r.get("outcome") == "TP")
        sl = sum(1 for r in data if r.get("outcome") == "SL")
        tot = tp + sl
        win = round(100*tp/tot, 2) if tot > 0 else 0.0
        rows.append((scenario, str(len(data)), str(tp), str(sl), f"{win}", path))

    out_path = os.path.join(outdir, f"REGRESSION_{d8}_AE_{args.label}.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerows(rows)
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()