# scripts/run_catalyst.py
# v0.3.12 — Catalyst workflow runner
# Uses a safe "universe swap" so existing scripts (fetch_minutes_polygon.py, run_day_simple.py)
# work unchanged. No --universe/--out flags needed on your runners.

import argparse, sys, subprocess, os, shutil
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(".").resolve()
DEFAULT_UNIVERSE = Path("data/samples/universe_sample.txt")  # what your runners expect
CATALYST_DIR = Path("data/catalyst")

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def parse_args():
    ap = argparse.ArgumentParser(description="Run catalyst backtests without touching normal universe permanently.")
    ap.add_argument("--date", required=True, help="Trading date (YYYY-MM-DD)")
    ap.add_argument("--scenario", required=True, choices=["A","B","C","D","E"], help="Scenario (A–E)")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--symbols", help="Comma-separated symbols, e.g., STTK,LPSN")
    grp.add_argument("--file", help="Path to a text file with one symbol per line")
    ap.add_argument("--session", default="rth", choices=["all","rth"], help="Minutes session for fetch")
    ap.add_argument("--fetch-minutes", action="store_true", help="Fetch minute data before backtest")
    ap.add_argument("--python", default=sys.executable, help="Python interpreter to use")
    return ap.parse_args()

def load_symbols(args) -> list[str]:
    if args.symbols:
        syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    else:
        p = Path(args.file)
        if not p.exists():
            raise SystemExit(f"Catalyst file not found: {p}")
        syms = []
        for line in p.read_text(encoding="utf-8").splitlines():
            s = line.strip().upper()
            if s and not s.startswith("#"):
                syms.append(s)
    if not syms:
        raise SystemExit("No symbols provided.")
    return sorted(set(syms))

def yyyymmdd(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise SystemExit("Invalid --date. Use YYYY-MM-DD.")
    return dt.strftime("%Y%m%d")

def repo_env():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env

def write_catalyst_universe(date_str: str, symbols: list[str]) -> Path:
    ensure_dir(CATALYST_DIR)
    uni_path = CATALYST_DIR / f"universe_{date_str}.txt"
    uni_path.write_text("\n".join(symbols) + "\n", encoding="utf-8")
    return uni_path

def swap_in_universe(temp_universe: Path) -> Path | None:
    """Replace DEFAULT_UNIVERSE with temp_universe content, backing up original if present.
       Returns path to backup if created."""
    ensure_dir(DEFAULT_UNIVERSE.parent)
    backup = None
    if DEFAULT_UNIVERSE.exists():
        backup = DEFAULT_UNIVERSE.with_suffix(".bak")
        shutil.copy2(DEFAULT_UNIVERSE, backup)
    shutil.copy2(temp_universe, DEFAULT_UNIVERSE)
    return backup

def restore_universe(backup: Path | None):
    if backup and backup.exists():
        shutil.copy2(backup, DEFAULT_UNIVERSE)
        try:
            backup.unlink()
        except Exception:
            pass

def run_fetch_minutes(py: str, date_str: str, session: str):
    fetch_script = Path("scripts") / "fetch_minutes_polygon.py"
    if not fetch_script.exists():
        print("[WARN] scripts/fetch_minutes_polygon.py not found — skipping minutes fetch.")
        return
    args = [py, str(fetch_script), "--date", date_str, "--session", session]
    print(f"[CMD] {' '.join(args)}")
    cp = subprocess.run(args, capture_output=True, text=True, env=repo_env())
    print(cp.stdout)
    if cp.returncode != 0:
        print(cp.stderr)
        raise SystemExit(f"Minute fetch failed with exit code {cp.returncode}")

def run_backtest(py: str, date_str: str, scenario: str):
    """Prefer package CLI; if not importable, use scripts/run_day_simple.py."""
    # Try package
    args_pkg = [py, "-m", "midas_v2.cli", "backtest", "--date", date_str, "--scenario", scenario]
    print(f"[CMD] {' '.join(args_pkg)}")
    cp = subprocess.run(args_pkg, capture_output=True, text=True, env=repo_env())
    print(cp.stdout)
    if cp.returncode == 0:
        return
    print(cp.stderr)
    print("[INFO] Package CLI not available — using scripts/run_day_simple.py")

    # Fallback
    fallback = Path("scripts") / "run_day_simple.py"
    if not fallback.exists():
        raise SystemExit("Fallback runner scripts/run_day_simple.py not found.")
    args_fb = [py, str(fallback), "--date", date_str, "--scenario", scenario]
    print(f"[CMD] {' '.join(args_fb)}")
    cp2 = subprocess.run(args_fb, capture_output=True, text=True, env=repo_env())
    print(cp2.stdout)
    if cp2.returncode != 0:
        print(cp2.stderr)
        raise SystemExit(f"Backtest failed (fallback) with exit code {cp2.returncode}")

def main():
    args = parse_args()
    syms = load_symbols(args)
    print(f"[CATALYST] Date={args.date}  Scenario={args.scenario}  Symbols={syms}")

    # Write a dedicated catalyst universe file (for record-keeping)
    cat_uni = write_catalyst_universe(args.date, syms)
    print(f"[UNIVERSE] Catalyst universe -> {cat_uni}")

    # Swap catalyst universe into the default path used by your existing scripts
    backup = swap_in_universe(cat_uni)
    print(f"[SWAP] Default universe replaced for this run. Backup={backup if backup else 'none'}")

    try:
        if args.fetch_minutes:
            run_fetch_minutes(args.python, args.date, args.session)
        run_backtest(args.python, args.date, args.scenario)
        print("[ OK ] Catalyst run complete.")
    finally:
        # Always restore original universe so normal flows remain untouched
        restore_universe(backup)
        print("[RESTORE] Default universe restored.")

if __name__ == "__main__":
    main()