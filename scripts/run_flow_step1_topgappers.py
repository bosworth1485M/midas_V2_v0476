#!/usr/bin/env python3
"""
Step 1 only: build RAW gappers for a day, and auto-create the RAW CSV from the TXT table.

Writes:
  data/raw/universe_topgappers_<DATE>.txt
  data/raw/universe_topgappers_<DATE>.csv  (auto-created from TXT)

Usage:
  python scripts/run_flow_step1_topgappers.py --date 2025-08-05 --scenario B
"""

import argparse, os, re, csv, subprocess, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

# Parse the TXT table printed by topgappers (SYMBOL, GAP%, PRICE)
HEADER_RX = re.compile(r"^\s*SYMBOL\s+GAP%\s+PRICE", re.IGNORECASE)
ROW_RX    = re.compile(r"^\s*([A-Za-z0-9.\-pP]{1,10})\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)")

def sh(cmd, env=None, check=True):
    print("[CMD]", " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, check=check, env=env)

def ensure_raw_csv_from_txt(raw_txt: Path, raw_csv: Path) -> int:
    """
    Create data/raw/universe_topgappers_<DATE>.csv from the TXT table if missing.
    Returns number of rows written (0 if nothing created).
    """
    if raw_csv.exists():
        print(f"[STEP1] RAW_CSV exists: {raw_csv}")
        return sum(1 for _ in open(raw_csv, encoding="utf-8")) - 1  # minus header
    if not raw_txt.exists():
        print(f"[STEP1] RAW_TXT missing: {raw_txt}")
        return 0

    lines = raw_txt.read_text(encoding="utf-8", errors="ignore").splitlines()
    started = False
    rows = []
    for line in lines:
        if not started:
            if HEADER_RX.match(line):
                started = True
            continue
        m = ROW_RX.match(line)
        if m:
            sym = m.group(1).upper()
            gap = float(m.group(2))
            price = float(m.group(3))
            rows.append((sym, gap, price))

    if not rows:
        print(f"[STEP1] RAW_TXT parsed 0 rows (unexpected).")
        return 0

    raw_csv.parent.mkdir(parents=True, exist_ok=True)
    with raw_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "gap_pct", "price"])
        for s, g, p in rows:
            w.writerow([s, f"{g:.2f}", f"{p:.4f}"])
    print(f"[STEP1] RAW_CSV created from TXT: {raw_csv} rows={len(rows)}")
    return len(rows)

def write_stamp(date_str: str):
    """Optional provenance stamp (keeps audits consistent as we add steps)."""
    import hashlib, json
    out_dir = ROOT / f"out/{date_str.replace('-','')}"
    def file_sha(p: Path):
        try:
            h = hashlib.sha256()
            with p.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            return h.hexdigest()
        except FileNotFoundError:
            return None
    stamp = {
        "date": date_str,
        "built_at": datetime.now().isoformat(timespec="seconds"),
        "scanner_json_sha": file_sha(ROOT/"config"/"scanner.json"),
        "scenarios_json_sha": file_sha(ROOT/"config"/"scenarios.json"),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"build_stamp_{date_str}.json").write_text(
        json.dumps(stamp, indent=2), encoding="utf-8"
    )
    print(f"[STEP1] Wrote stamp -> {out_dir / f'build_stamp_{date_str}.json'}")

def main():
    ap = argparse.ArgumentParser(description="Step 1: build RAW gappers + RAW CSV for a day")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--scenario", default="B", help="Scenario name (default B)")
    ap.add_argument("--rebuild", action="store_true", help="Force re-run even if RAW exists")
    args = ap.parse_args()

    ds = args.date
    raw_txt = ROOT / f"data/raw/universe_topgappers_{ds}.txt"
    raw_csv = ROOT / f"data/raw/universe_topgappers_{ds}.csv"

    # Step 1 — run topgappers to write RAW TXT (Top=0 = full list)
    if args.rebuild or not raw_txt.exists():
        raw_txt.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy(); env["PYTHONPATH"] = "src"
        sh([
            sys.executable, str(ROOT / "scripts" / "topgappers.py"),
            "--date", ds, "--scenario", args.scenario,
            "--out", str(raw_txt), "--top", "0"
        ], env=env, check=True)
    else:
        print(f"[STEP1] RAW_TXT exists (skip run): {raw_txt}")

    # Auto-create RAW CSV from TXT (so later steps can deterministically use CSV)
    nrows = ensure_raw_csv_from_txt(raw_txt, raw_csv)

    # Provenance (optional but handy)
    write_stamp(ds)

    # Final audit summary for step 1
    print("\n[STEP1 SUMMARY]")
    print(f"RAW_TXT: {raw_txt}  exists={raw_txt.exists()}")
    print(f"RAW_CSV: {raw_csv}  exists={raw_csv.exists()}  rows={(nrows if nrows else 'unknown')}")
    print("\nNext: when you're happy with Step 1, we'll add Step 2 (enrich_universe_catalyst).")

if __name__ == "__main__":
    main()