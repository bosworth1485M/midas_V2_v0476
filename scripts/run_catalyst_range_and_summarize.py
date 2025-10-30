#!/usr/bin/env python3
# scripts/run_catalyst_range_and_summarize.py
# Range runner for the *catalyst* flow (with provenance passthrough).

import argparse, subprocess, sys, csv, os
from datetime import datetime, timedelta
from pathlib import Path
import glob

ROOT = Path(__file__).resolve().parents[1]

def daterange(start: datetime, end: datetime):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)

def precheck_gappers(date_str: str, timeout_sec: int) -> int:
    cmd = [sys.executable, str(ROOT / "scripts" / "topgappers.py"), "--date", date_str, "--no-write"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec, check=True)
        out = (r.stdout or "").strip()
        if "(none)" in out:
            return 0
        lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
        rows = [ln for ln in lines
                if not ln.startswith("Open-gap")
                and not ln.startswith("SYMBOL")
                and not ln.startswith("Wrote")]
        return max(0, len(rows))
    except Exception:
        return -1

def summarize_csv(csv_path: Path):
    t=w=l=0; pnl=0.0
    if not csv_path.exists(): return t,w,l,pnl
    with csv_path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            t += 1
            try: pnl += float(row.get("pnl", 0.0))
            except Exception: pass
            o = (row.get("outcome") or "").upper()
            if o == "TP": w += 1
            elif o == "SL": l += 1
    return t,w,l,pnl

def write_row(out_csv: Path, date_str: str, label: str, t: int, w: int, l: int, pnl: float):
    wr = (100*w/t) if t else 0.0
    with out_csv.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date","label","trades","wins","losses","winrate_pct","pnl"])
        writer.writerow({"date":date_str,"label":label,"trades":t,"wins":w,
                         "losses":l,"winrate_pct":round(wr,2),"pnl":round(pnl,2)})

def pick_results_csv(date_str: str, scenario: str|None, profile: str|None) -> Path|None:
    ymd = date_str.replace("-", "")
    base = ROOT / "out" / ymd
    candidate_names = []
    if profile: candidate_names.append(f"{profile}_hybrid")
    if scenario: candidate_names.append(f"{scenario}_hybrid")
    for name in candidate_names:
        p = base / name / f"results_{date_str}.csv"
        if p.exists(): return p
    for d in sorted(base.glob("*_hybrid")):
        p = d / f"results_{date_str}.csv"
        if p.exists(): return p
    return None

def build_flow_cmd(date_str: str, args, top_cmd: str) -> list[str]:
    """Forward all supported run_catalyst_flow.py flags so behavior matches the single-day runner."""
    cmd = [sys.executable, str(ROOT / "scripts" / "run_catalyst_flow.py"), "--date", date_str,
           "--upstream-command", top_cmd]
    # scenario/profile handling
    if args.profile:
        cmd += ["--profile", args.profile]
        if args.profile_keep: cmd.append("--profile-keep")
        if args.profile_v1_path: cmd += ["--profile-v1-path", args.profile_v1_path]
        if args.profile_v2_path: cmd += ["--profile-v2-path", args.profile_v2_path]
    else:
        cmd += ["--scenario", args.scenario]
    # catalyst knobs
    if args.news_first: cmd.append("--news-first")
    if args.require_news: cmd.append("--require-news")
    if args.news_min_score is not None: cmd += ["--news-min-score", str(args.news_min_score)]
    if args.top is not None: cmd += ["--top", str(args.top)]
    if args.enforce_band: cmd.append("--enforce-band")
    if args.band_min is not None: cmd += ["--band-min", str(args.band_min)]
    if args.band_max is not None: cmd += ["--band-max", str(args.band_max)]
    if args.min_rvol_open is not None: cmd += ["--min-rvol-open", str(args.min_rvol_open)]
    if args.gate_minutes is not None: cmd += ["--gate-minutes", str(args.gate_minutes)]
    if args.deny_negative: cmd.append("--deny-negative")
    if args.exclude_china: cmd.append("--exclude-china")
    if args.neg_terms_file: cmd += ["--neg-terms-file", args.neg_terms_file]
    if args.china_list_file: cmd += ["--china-list-file", args.china_list_file]
    if args.no_rebuild: cmd.append("--no-rebuild")
    if args.print_news: cmd.append("--print-news")
    if args.compare:
        cmd.append("--compare")
        if args.compare_label: cmd += ["--compare-label", args.compare_label]
    return cmd

def main():
    ap = argparse.ArgumentParser(description="Run a *catalyst* date range and summarize (with provenance passthrough).")
    ap.add_argument("--start", required=True); ap.add_argument("--end", required=True)
    ap.add_argument("--scenario", default="B")
    ap.add_argument("--profile", choices=["B_profit_v1","B_profit_v2"])
    ap.add_argument("--profile-keep", action="store_true")
    ap.add_argument("--profile-v1-path", default=str(ROOT / "scenarios_B_profit_v1.json"))
    ap.add_argument("--profile-v2-path", default=str(ROOT / "scenarios_B_profit_v2.json"))
    ap.add_argument("--news-first", action="store_true")
    ap.add_argument("--require-news", action="store_true")
    ap.add_argument("--news-min-score", type=float, default=None)
    ap.add_argument("--top", type=int, default=None)
    ap.add_argument("--enforce-band", action="store_true")
    ap.add_argument("--band-min", type=float, default=None)
    ap.add_argument("--band-max", type=float, default=None)
    ap.add_argument("--min-rvol-open", type=float, default=None)
    ap.add_argument("--gate-minutes", type=int, default=None)
    ap.add_argument("--deny-negative", action="store_true")
    ap.add_argument("--exclude-china", action="store_true")
    ap.add_argument("--neg-terms-file", default="data/catalyst/neg_terms.txt")
    ap.add_argument("--china-list-file", default="data/deny/china_tickers.txt")
    ap.add_argument("--no-rebuild", action="store_true")
    ap.add_argument("--print-news", action="store_true")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--compare-label")
    ap.add_argument("--include-weekends", action="store_true")
    ap.add_argument("--include-empty", action="store_true")
    ap.add_argument("--precheck-timeout", type=int, default=60)
    ap.add_argument("--timeout-sec", type=int, default=600)
    ap.add_argument("--append", action="store_true")
    ap.add_argument("--save-csv", default=None)
    ap.add_argument("--skip-missing", action="store_true")
    ap.add_argument("--log-skipped", action="store_true")
    args = ap.parse_args()

    # capture the top-level command line (provenance)
    top_cmd = " ".join([sys.executable] + sys.argv)

    start_dt = datetime.strptime(args.start, "%Y-%m-%d")
    end_dt   = datetime.strptime(args.end, "%Y-%m-%d")
    label_for_totals = (args.profile or args.scenario).upper()
    out_root = ROOT / "out" / "auto_catalyst"
    tag = f"{args.start.replace('-','')}_{args.end.replace('-','')}_{label_for_totals}"
    out_csv = Path(args.save_csv) if args.save_csv else out_root / f"range_summary_{tag}.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    if not args.append:
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["date","label","trades","wins","losses","winrate_pct","pnl"])
            writer.writeheader()

    totals = {"t":0,"w":0,"l":0,"pnl":0.0}
    print(f"\n=== Running *catalyst* range: {args.start} -> {args.end} | Label: {label_for_totals} ===\n")
    for d in daterange(start_dt, end_dt):
        date_str = d.strftime("%Y-%m-%d")
        if (not args.include_weekends) and d.weekday() >= 5:
            print(f"[SKIP] {date_str} (weekend)")
            if args.log_skipped: write_row(out_csv, date_str, label_for_totals, 0,0,0,0.0)
            continue
        pre_ct = precheck_gappers(date_str, args.precheck_timeout)
        if (not args.include_empty) and pre_ct == 0:
            print(f"[SKIP] {date_str} (no gappers; likely holiday/empty)")
            if args.log_skipped: write_row(out_csv, date_str, label_for_totals, 0,0,0,0.0)
            continue

        cmd = build_flow_cmd(date_str, args, top_cmd)
        print("[RUN]", " ".join(cmd))
        try:
            subprocess.run(cmd, check=True, timeout=args.timeout_sec, env=os.environ.copy())
        except subprocess.TimeoutExpired:
            print(f"[WARN] {date_str}: flow timeout after {args.timeout_sec}s; continuing.")
        except subprocess.CalledProcessError as e:
            print(f"[WARN] {date_str}: flow failed (rc={e.returncode}); continuing.")

        res_csv = pick_results_csv(date_str, None if args.profile else args.scenario.upper(), args.profile)
        if not res_csv or not res_csv.exists():
            msg = "(missing results CSV)"
            print(f"{date_str} [{label_for_totals}] -> trades=0, wins=0, losses=0, winrate=0.00%, pnl=+0.00 {msg}")
            if not args.skip_missing: write_row(out_csv, date_str, label_for_totals, 0,0,0,0.0)
            continue

        t,w,l,pnl = summarize_csv(res_csv)
        totals["t"]+=t; totals["w"]+=w; totals["l"]+=l; totals["pnl"]+=pnl
        wr = (100*w/t) if t else 0.0
        print(f"{date_str} [{label_for_totals}] -> trades={t}, wins={w}, losses={l}, winrate={wr:.2f}%, pnl={pnl:+.2f}")
        write_row(out_csv, date_str, label_for_totals, t,w,l,pnl)

    T,W,L,P = totals["t"], totals["w"], totals["l"], totals["pnl"]
    WR = (100*W/T) if T else 0.0
    print("\n=== TOTALS ===")
    print(f"[{label_for_totals}] trades={T}, wins={W}, losses={L}, winrate={WR:.2f}%, totalPnL={P:+.2f}")
    print(f"\n[OK] Catalyst range summary CSV -> {out_csv}")

if __name__ == "__main__":
    main()