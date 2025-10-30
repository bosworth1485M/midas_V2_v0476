# scripts/run_range_and_summarize.py  (v1.4)
# Fresh-run defaults:
# - Re-fetch samples (fresh) by default (use --no-refresh to disable)
# - Skip weekends by default (use --include-weekends to override)
# - Skip empty/non-trading days by default via topgappers --no-write (use --include-empty to override)
# - No resume by default (use --resume to reuse existing results)
# - Overwrite the summary CSV by default (use --append to append)

import argparse, subprocess, sys, csv
from datetime import datetime, timedelta
from pathlib import Path

def daterange(start: datetime, end: datetime):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)

def precheck_gappers(date_str: str, timeout_sec: int) -> int:
    """Return count of gappers from topgappers --no-write (fast pre-check)."""
    cmd = [sys.executable, "scripts/topgappers.py", "--date", date_str, "--no-write"]
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
        # Unknown (transient). Return -1 so we don't accidentally skip a real day.
        return -1

def run_one_day(date_str: str, scenarios: list[str], args) -> bool:
    cmd = [sys.executable, "scripts/run_day_simple.py", "--date", date_str,
           "--scenario", ",".join(scenarios), "--session", args.session]

    if args.refresh_samples: cmd.append("--refresh-samples")
    if args.no_filter:       cmd.append("--no-filter")
    if args.include_dot:     cmd.append("--include-dot")
    if args.min_gap is not None:   cmd += ["--min-gap", str(args.min_gap)]
    if args.max_price is not None: cmd += ["--max-price", str(args.max_price)]
    if args.limit is not None:     cmd += ["--limit", str(args.limit)]
    if args.out_root:              cmd += ["--out-root", args.out_root]

    print("[RUN]", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True, timeout=args.timeout_sec)
        return True
    except subprocess.TimeoutExpired:
        print(f"[WARN] {date_str}: runner timeout after {args.timeout_sec}s; skipping.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"[WARN] {date_str}: runner failed (rc={e.returncode}); skipping.")
        return False

def summarize_csv(csv_path: Path):
    t=w=l=0; pnl=0.0
    if not csv_path.exists(): return t,w,l,pnl
    with csv_path.open(newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            t += 1
            try: pnl += float(row.get("pnl", 0.0))
            except: pass
            o = (row.get("outcome") or "").upper()
            if o == "TP": w += 1
            elif o == "SL": l += 1
    return t,w,l,pnl

def write_row(out_csv: Path, date_str: str, sc: str, t: int, w: int, l: int, pnl: float):
    wr = (100*w/t) if t else 0.0
    with out_csv.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date","scenario","trades","wins","losses","winrate_pct","pnl"])
        writer.writerow({"date":date_str,"scenario":sc,"trades":t,"wins":w,
                         "losses":l,"winrate_pct":round(wr,2),"pnl":round(pnl,2)})

def main():
    ap = argparse.ArgumentParser(description="Run a date range and summarize (fresh defaults).")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end",   required=True, help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--scenario", default="B", help="Comma-separated scenario keys (e.g., B or B,D)")
    ap.add_argument("--session", default="rth", choices=["rth","all"])
    # Fresh run defaults:
    ap.add_argument("--no-refresh", dest="refresh_samples", action="store_false",
                    help="Do NOT re-fetch samples (default is fresh re-fetch)")
    ap.set_defaults(refresh_samples=True)
    ap.add_argument("--resume", action="store_true", help="Reuse existing per-day results (default: re-run days)")
    ap.add_argument("--append", action="store_true", help="Append to existing range CSV (default: overwrite)")
    # Filters & output
    ap.add_argument("--min-gap", type=float, default=None)
    ap.add_argument("--max-price", type=float, default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--include-dot", action="store_true")
    ap.add_argument("--no-filter", action="store_true")
    ap.add_argument("--out-root", default="out/auto")
    ap.add_argument("--save-csv", default=None)
    ap.add_argument("--timeout-sec", type=int, default=180, help="Per-day runner timeout (sec)")
    # Skips (defaults: skip weekends & empty)
    ap.add_argument("--include-weekends", action="store_true", help="Run weekends (default: skip)")
    ap.add_argument("--include-empty", action="store_true", help="Run even if precheck finds no gappers (default: skip)")
    ap.add_argument("--precheck-timeout", type=int, default=60, help="Seconds to wait for precheck")
    ap.add_argument("--log-skipped", action="store_true", help="Write zero rows for skipped days")
    args = ap.parse_args()
    scenarios = [s.strip().upper() for s in getattr(args, "scenarios", getattr(args, "scenario", "B")).split(",") if s.strip()]
    start_dt = datetime.strptime(args.start, "%Y-%m-%d")
    end_dt   = datetime.strptime(args.end,   "%Y-%m-%d")

    # Output CSV path
    if args.save_csv:
        out_csv = Path(args.save_csv)
    else:
        tag = f"{args.start.replace('-','')}_{args.end.replace('-','')}_{'-'.join(scenarios)}"
        out_csv = Path(args.out_root) / f"range_summary_{tag}.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    # Range CSV: overwrite by default, append only if --append
    mode_msg = "APPEND" if args.append else "OVERWRITE"
    if not args.append:
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["date","scenario","trades","wins","losses","winrate_pct","pnl"])
            writer.writeheader()

    totals = {sc: {"t":0,"w":0,"l":0,"pnl":0.0} for sc in scenarios}

    print(f"\n=== Running range: {args.start} → {args.end} | Scenarios: {scenarios} | Mode: {mode_msg} ===\n")
    for d in daterange(start_dt, end_dt):
        date_str = d.strftime("%Y-%m-%d")

        # Skip weekends by default
        if (not args.include_weekends) and d.weekday() >= 5:
            print(f"[SKIP] {date_str} (weekend)")
            if args.log_skipped:
                for sc in scenarios: write_row(out_csv, date_str, sc, 0, 0, 0, 0.0)
            continue

        # Pre-check for empty/non-trading day via topgappers --no-write
        pre_ct = precheck_gappers(date_str, args.precheck_timeout)
        if (not args.include_empty) and pre_ct == 0:
            print(f"[SKIP] {date_str} (no gappers; likely holiday/empty)")
            if args.log_skipped:
                for sc in scenarios: write_row(out_csv, date_str, sc, 0, 0, 0, 0.0)
            continue

        # Resume: ONLY if requested; otherwise always re-run the day
        if args.resume:
            all_exist = True
            for sc in scenarios:
                p = Path(args.out_root) / d.strftime("%Y%m%d") / sc / f"results_{date_str}.csv"
                if not p.exists():
                    all_exist = False; break
            if all_exist:
                print(f"[RESUME] {date_str} already has results; using them.")
                # Fall through to summarization without running

        # Run the one-shot day runner (unless resuming with all CSVs present)
        if not args.resume or not all_exist:
            run_one_day(date_str, scenarios, args)

        # Summarize per scenario
        for sc in scenarios:
            p = Path(args.out_root) / d.strftime("%Y%m%d") / sc / f"results_{date_str}.csv"
            t,w,l,pnl = summarize_csv(p)
            totals[sc]["t"] += t; totals[sc]["w"] += w; totals[sc]["l"] += l; totals[sc]["pnl"] += pnl
            write_row(out_csv, date_str, sc, t, w, l, pnl)
            wr = (100*w/t) if t else 0.0
            print(f"{date_str} [{sc}] -> trades={t}, wins={w}, losses={l}, winrate={wr:.2f}%, pnl={pnl:+.2f}")

    print("\n=== TOTALS ===")
    for sc in scenarios:
        T,W,L,P = totals[sc]["t"], totals[sc]["w"], totals[sc]["l"], totals[sc]["pnl"]
        WR = (100*W/T) if T else 0.0
        print(f"[{sc}] trades={T}, wins={W}, losses={L}, winrate={WR:.2f}%, totalPnL={P:+.2f}")
    print(f"\n[OK] Range summary CSV -> {out_csv}")

if __name__ == "__main__":
    main()
