# scripts/list_base_files.py
# Lists which canonical result files exist (ignores out/auto)
# Usage:
#   python scripts/list_base_files.py --scenario E --start 2025-08-05 --end 2025-08-31

import argparse
from pathlib import Path
from datetime import date, datetime, timedelta

def parse_args():
    ap = argparse.ArgumentParser(description="List existing/missing base result files for a scenario/date range.")
    ap.add_argument("--scenario", required=True, help="Scenario letter, e.g. D or E")
    ap.add_argument("--start", required=True, help="Start YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="End YYYY-MM-DD")
    return ap.parse_args()

def main():
    a = parse_args()
    scen = a.scenario.upper()
    start = datetime.strptime(a.start, "%Y-%m-%d").date()
    end = datetime.strptime(a.end, "%Y-%m-%d").date()

    have, missing = [], []
    d = start
    while d <= end:
        ymd = d.strftime("%Y%m%d")
        iso = d.isoformat()
        p = Path(f"out/{ymd}/{scen}/results_{iso}.csv")
        (have if p.exists() else missing).append(iso)
        d += timedelta(days=1)

    print(f"Scenario {scen}  {a.start}→{a.end}")
    print("HAVE   :", ", ".join(have) if have else "(none)")
    print("MISSING:", ", ".join(missing) if missing else "(none)")

if __name__ == "__main__":
    main()