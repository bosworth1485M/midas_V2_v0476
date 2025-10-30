#!/usr/bin/env python3
"""
scan_runs_simple.py — human-first scanner (with provenance/flag view).
Adds:
  • robust fallback to summary text if JSON metrics missing
  • prints main flags (Top, band, RVOL, gate, score, newsOnly/newsFirst)
  • prefers the latest bundle WITH trades, falling back to latest if none
"""

import argparse, json, glob, os, csv, time, re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT  = ROOT / "out"

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end",   required=True, help="YYYY-MM-DD")
    ap.add_argument("--scenarios", default="B", help="Comma-separated scenarios (default B)")
    ap.add_argument("--label-substr", default=None, help="Only include bundles whose label contains this substring")
    ap.add_argument("--write", action="store_true", help="Also write CSV/MD to out/")
    return ap.parse_args()

def to_date(s): return datetime.strptime(s, "%Y-%m-%d").date()

def fmt(x):
    if x is None: return "?"
    try:
        xf = float(x)
        return str(int(xf)) if xf.is_integer() else f"{xf:.2f}"
    except: return str(x)

def profile_string(p):
    """Short summary of key flags."""
    parts = []
    parts.append("newsOnly" if p.get("news_only") else ("newsFirst" if p.get("news_first") else "mixed"))
    if p.get("top"): parts.append(f"Top-{int(p['top'])}")
    bmin, bmax = p.get("band_min"), p.get("band_max")
    if bmin is not None or bmax is not None: parts.append(f"band {fmt(bmin)}-{fmt(bmax)}")
    if p.get("min_rvol_open") is not None:   parts.append(f"RVOL {fmt(p['min_rvol_open'])}")
    if p.get("gate_minutes")   is not None:  parts.append(f"gate {int(p['gate_minutes'])}m")
    if p.get("news_min_score") not in (None, 1, 1.0): parts.append(f"score ≥ {fmt(p['news_min_score'])}")
    return " + ".join(parts)

def parse_summary_txt(summary_path):
    """Fallback parser for RUN SUMMARY one-liner in TXT."""
    try:
        txt = Path(summary_path).read_text(encoding="utf-8")
    except Exception:
        return None
    m = re.search(r"\bTP\s*=\s*(\d+)\s+SL\s*=\s*(\d+)\s+Win%=\s*([\d.]+)\s+PnL=\s*([-+]?\d+(?:\.\d+)?)", txt)
    if not m: return None
    tp, sl, wr, pnl = m.groups()
    return {"tp": int(tp), "sl": int(sl), "wr": float(wr), "pnl": float(pnl), "used": int(tp)+int(sl)}

def collect_bundles(start, end, scenarios, label_substr):
    files = glob.glob(str(OUT / "*" / "_comparisons" / "comparison_*.json"))
    rows = []
    for fp in files:
        try:
            d = json.loads(Path(fp).read_text(encoding="utf-8"))
        except Exception:
            continue
        date = d.get("date"); scen = d.get("scenario"); lab = (d.get("label") or "")
        if not date or not scen: continue
        dd = to_date(date)
        if not (start <= dd <= end): continue
        if scen not in scenarios: continue
        if label_substr and (label_substr.lower() not in lab.lower()): continue

        m  = d.get("metrics") or {}
        p  = d.get("params")  or {}
        tp = m.get("tp") or 0
        sl = m.get("sl") or 0
        used = m.get("used") or (int(tp)+int(sl))
        wr  = m.get("wr_pct")
        pnl = m.get("pnl")

        # Fallback if any metric missing/zero-ish
        needs_fallback = (used is None or used == 0 or wr is None or pnl is None)
        if needs_fallback:
            # Infer the paired summary path from the comparison name
            # comparison_<runid>.json  ->  summary_<runid>.txt
            stem = Path(fp).stem  # e.g., comparison_1759771953
            run_id = stem.split("_", 1)[1] if "_" in stem else None
            if run_id:
                txt_guess = Path(fp).with_name(f"summary_{run_id}.txt")
                fall = parse_summary_txt(txt_guess) if txt_guess.exists() else None
                if fall:
                    tp, sl, wr, pnl, used = fall["tp"], fall["sl"], fall["wr"], fall["pnl"], fall["used"]

        rows.append({
            "date": date, "scenario": scen, "label": lab, "file": fp,
            "tp": int(tp), "sl": int(sl), "used": int(used or 0),
            "wr": float(wr or 0.0), "pnl": float(pnl or 0.0),
            "params": p, "mtime": os.path.getmtime(fp)
        })
    return rows

def dedupe_by_day(rows):
    """Keep the latest bundle per (date,scenario), preferring one with trades."""
    bykey = {}
    for r in rows:
        k = (r["date"], r["scenario"])
        score = (1 if r["used"] > 0 else 0, r["mtime"])  # prefer has-trades, then newest
        best = bykey.get(k)
        if (best is None) or (score > best[0]):
            bykey[k] = (score, r)
    chosen = [v[1] for v in bykey.values()]
    return sorted(chosen, key=lambda r: (r["date"], r["scenario"]))

def print_table(rows):
    print("\nPer-day results (with flags)")
    print("---------------------------------------------")
    print(f"{'Date':10} {'Scen':5} {'TP/SL':>6} {'Trades':>6} {'WR%':>7} {'PnL':>9}  Profile")
    for r in rows:
        tpsl = f"{r['tp']}/{r['sl']}"
        print(f"{r['date']:10} {r['scenario']:5} {tpsl:>6} {r['used']:>6} {r['wr']:>7.2f} {r['pnl']:>9.2f}  {profile_string(r['params'])}")
    tp = sum(r["tp"] for r in rows)
    sl = sum(r["sl"] for r in rows)
    used = tp + sl
    pnl  = sum(r["pnl"] for r in rows)
    wr   = (tp/used*100.0) if used else 0.0
    print("\nTotals")
    print("------")
    print(f"Days={len(rows)}  Trades={used}  TP/SL={tp}/{sl}  WR={wr:.2f}%  PnL={pnl:.2f}")

def write_outputs(rows, start, end):
    ts = int(time.time())
    csv_path = OUT / f"scan_simple_{start}_{end}_{ts}.csv"
    md_path  = OUT / f"scan_simple_{start}_{end}_{ts}.md"
    # CSV
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date","scenario","tp","sl","trades","wr_pct","pnl","profile","label","file"])
        for r in rows:
            w.writerow([r["date"], r["scenario"], r["tp"], r["sl"], r["used"], f"{r['wr']:.2f}", f"{r['pnl']:.2f}",
                        profile_string(r["params"]), r["label"], r["file"]])
    # MD
    lines = []
    lines.append(f"# Scan {start} → {end}\n")
    lines.append("| Date | Scen | TP/SL | Trades | WR% | PnL | Profile |")
    lines.append("|---|---|---:|---:|---:|---:|---|")
    for r in rows:
        lines.append(f"| {r['date']} | {r['scenario']} | {r['tp']}/{r['sl']} | {r['used']} | {r['wr']:.2f} | {r['pnl']:.2f} | {profile_string(r['params'])} |")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[WROTE] {csv_path.name}, {md_path.name}")

def main():
    args = parse_args()
    start = to_date(args.start); end = to_date(args.end)
    scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()]
    rows = collect_bundles(start, end, scenarios, args.label_substr)
    if not rows:
        print("No bundles found. Make sure you ran with --compare and the dates/scenarios match.")
        return
    rows = dedupe_by_day(rows)                 # prefer non-zero-trade bundles
    rows = [r for r in rows if r["used"] >= 1] # drop zero-trade artifacts
    if not rows:
        print("No rows with trades.")
        return
    print_table(rows)
    if args.write:
        s = args.start.replace("-",""); e = args.end.replace("-","")
        write_outputs(rows, s, e)

if __name__ == "__main__":
    main()