# scripts/run_day_simple.py  (v1.1: auto-sanitize universe from samples)
import argparse, subprocess, sys, os, glob, re

def run(cmd: list[str]) -> None:
    print("[CMD]", " ".join(cmd))
    subprocess.run(cmd, check=True)

def rm_samples_for(date_str: str) -> int:
    pat = os.path.join("data", "samples", f"sample_{date_str}_*.csv")
    n = 0
    for p in glob.glob(pat):
        try:
            os.remove(p); n += 1
        except Exception as e:
            print(f"[WARN] Could not remove {p}: {e}")
    return n

def build_universe_from_samples(date_str: str, out_path: str) -> int:
    pat = os.path.join("data", "samples", f"sample_{date_str}_*.csv")
    keep, seen = [], set()
    rx = re.compile(r"^[A-Z][A-Z0-9\.]*$")  # allow dots (e.g., OPFI.WS)
    for p in glob.glob(pat):
        base = os.path.basename(p)
        sym = base[len(f"sample_{date_str}_"):-4].strip()  # strip prefix/suffix
        if sym and sym not in seen and rx.fullmatch(sym):
            seen.add(sym); keep.append(sym)
    keep.sort()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="") as f:
        f.write("\n".join(keep))
    print(f"[UNIVERSE] Wrote {len(keep)} symbols -> {out_path}")
    return len(keep)

def main():
    ap = argparse.ArgumentParser(
        description="One-shot: topgappers → fetch → sanitize-universe → backtest (uses data/samples/)."
    )
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--scenarios", default="B", help="Comma-separated list, e.g. B,E")
    ap.add_argument("--session", default="rth", choices=["rth","all"], help="Minute data session")
    ap.add_argument("--refresh-samples", action="store_true",
                    help="Delete data/samples/sample_<DATE>_*.csv before fetching")
    ap.add_argument("--out-root", default="out/auto", help="Root out folder (default: out/auto)")
    args = ap.parse_args()

    date_str = args.date
    scenarios = [s.strip().upper() for s in args.scenarios.split(",") if s.strip()]
    out_root = args.out_root.replace("\\", "/")

    # 0) Optional: clear old samples cache for this date
    if args.refresh_samples:
        removed = rm_samples_for(date_str)
        print(f"[CLEAN] Removed {removed} old sample files for {date_str} from data/samples/")

    # 1) Build universe candidates (topgappers)
    run([sys.executable, "scripts/topgappers.py", "--date", date_str])

    # 2) Fetch minute bars into data/samples/
    run([sys.executable, "scripts/fetch_minutes_polygon.py", "--date", date_str, "--session", args.session])

    # 3) Rebuild a CLEAN universe (symbols only) from samples just fetched
    sanitized_universe = os.path.join("data", f"universe_topgappers_{date_str}.txt")
    n_syms = build_universe_from_samples(date_str, sanitized_universe)
    if n_syms == 0:
        print("[ERR] No samples found after fetch; cannot backtest.")
        sys.exit(2)

    # 4) Backtest each scenario using the sanitized universe
    for scen in scenarios:
        out_dir = os.path.join(out_root, date_str.replace("-", ""), scen)
        os.makedirs(out_dir, exist_ok=True)
        cmd = [
            sys.executable, "-m", "midas_v2.cli", "backtest",
            "--date", date_str,
            "--scenario", scen,
            "--universe", sanitized_universe,
            "--out", out_dir
        ]
        run(cmd)
        csv = os.path.join(out_dir, f"results_{date_str}.csv")
        print(f"[OK] Scenario {scen} CSV -> {csv}")

    print("[DONE] All scenarios complete.")

if __name__ == "__main__":
    main()