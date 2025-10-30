#!/usr/bin/env python3
"""
check_comparison_metrics.py

Scans _comparisons/comparison_*.json files for specific days
and prints out their metrics (used, wr%, tp, sl, pnl).
"""

import json, os, glob

def check_days(days=("20250805","20250806","20250807")):
    bad = []
    for day in days:
        folder = os.path.join("out", day, "_comparisons")
        for fp in glob.glob(os.path.join(folder, "comparison_*.json")):
            with open(fp, encoding="utf-8") as f:
                d = json.load(f)
            m = d.get("metrics") or {}
            used, wr, tp, sl, pnl = (m.get("used"), m.get("wr_pct"),
                                     m.get("tp"), m.get("sl"), m.get("pnl"))
            ok = all(v is not None for v in (used, wr, tp, sl, pnl))
            print(f"{day} -> {os.path.basename(fp)} | "
                  f"used={used} wr%={wr} tp={tp} sl={sl} pnl={pnl} "
                  f"| {'OK' if ok else 'MISSING'}")
            if not ok:
                bad.append(fp)
    if not bad:
        print("\nALL GOOD ✅")
    else:
        print("\nIssues found ❌:")
        for fp in bad:
            print(" -", fp)

if __name__ == "__main__":
    check_days()