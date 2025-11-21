#!/usr/bin/env python3
# scripts/topgappers.py — prev-trading-day gappers (price band + min gap)
# - Loads ROOT/.env (override=True) and sanitizes POLYGON_API_KEY
# - Uses Authorization: Bearer <key> (no ?apiKey= in URL)
# - Writes zero bytes when there are 0 symbols (holiday/weekend)
# - Uses prev_trading_day_polygon.py to resolve prior trading day
# - NEW: Loads price/gap limits from JSON (config/scanner.json) with optional per-scenario
#        overrides from config/scenarios.json via Pydantic models.

# --- bootstrap: ensure src on path + load .env from project root ---
import os, sys, json, urllib.request, subprocess
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parents[1]
SRC  = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv(ROOT / ".env", override=True)
except Exception as e:
    sys.stderr.write(f"[WARN] dotenv load failed: {e}\n")
# --- end bootstrap ---

# NEW: import validated config models (does not affect Polygon key handling)
from midas_v2.config_models import ScannerConfig, ScenariosConfig, merge_scanner

DEF_OUT = ROOT / "data" / "samples" / "universe_sample.txt"

def load_key() -> str:
    k = (os.environ.get("POLYGON_API_KEY") or "")
    # strip whitespace and accidental quotes
    k = k.strip().strip('"').strip("'")
    if not k:
        print("[ERR] POLYGON_API_KEY missing (set it in .env)", file=sys.stderr)
        sys.exit(1)
    return k

def http_get_json(url: str, key: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}", "User-Agent": "midas_v2/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def prev_trading_day_for(date_iso: str) -> str:
    # Use helper (header-based); fallback to prior calendar day if it fails
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "prev_trading_day_polygon.py"), "--date", date_iso],
            capture_output=True, text=True, check=True,
        )
        for line in (r.stdout or "").splitlines():
            if "Previous trading day for" in line and " is " in line:
                return line.split(" is ")[-1].strip()
    except Exception:
        pass
    return (datetime.fromisoformat(date_iso).date() - timedelta(days=1)).isoformat()

def write_universe(symbols, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # zero bytes when empty; newline-terminated when non-empty
    text = ("\n".join(symbols) + "\n") if symbols else ""
    out_path.write_text(text, encoding="ascii")
    print(f"Wrote {len(symbols)} symbols -> {out_path}")

# --- NEW: write a gap-map sidecar (symbol -> gap_pct) for downstream summaries ---
def write_gap_map(rows, date_iso: str):
    """
    rows: iterable of tuples (symbol, gap_pct, open_price)
    Writes: out/<YYYYMMDD>/scanner/gap_map_<YYYY-MM-DD>.json
    """
    ymd = date_iso.replace("-", "")
    out_dir = ROOT / f"out/{ymd}/scanner"
    out_dir.mkdir(parents=True, exist_ok=True)
    gap_map = {sym.upper(): float(gap) for (sym, gap, _price) in rows}
    out_path = out_dir / f"gap_map_{date_iso}.json"
    out_path.write_text(json.dumps(gap_map, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[SCAN] gap_map saved -> {out_path}")

def main():
    ap = ArgumentParser(description="Build universe from open-gap vs previous trading day")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    # CLI price/gap args retained for backward compat but now ignored; JSON is source of truth
    ap.add_argument("--min-price", type=float, default=1.0)
    ap.add_argument("--max-price", type=float, default=20.0)
    ap.add_argument("--min-gap", type=float, default=10.0,
                    help="Minimum open gap percent (default 10)")
    ap.add_argument("--top", type=int, default=50,
                    help="Trim universe to top N gappers (default 50; set 0 to disable)")
    ap.add_argument("--out", default=str(DEF_OUT))
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--session", default=None, help="(ignored; compatibility)")
    # NEW: allow scenario to pick per-scenario scanner overrides from scenarios.json
    ap.add_argument("--scenario", default=None, help="Scenario name for overrides (e.g., B)")
    args, _ = ap.parse_known_args()

    # === Load validated scanner config (JSON is source of truth) ===
    scanner_global = ScannerConfig.model_validate_json(
        (ROOT / "config" / "scanner.json").read_text(encoding="utf-8")
    )
    scenario_obj = None
    scn_path = ROOT / "config" / "scenarios.json"
    if scn_path.exists():
        scenarios_map = ScenariosConfig.model_validate_json(
            scn_path.read_text(encoding="utf-8")
        ).root
        if args.scenario:
            scenario_obj = scenarios_map.get(args.scenario)
    scanner = merge_scanner(scanner_global, scenario_obj)
    price_min = scanner.price_min
    price_max = scanner.price_max
    min_gap_pct = scanner.min_gap_pct
    # max_gap_pct is available if you choose to use it later:
    # max_gap_pct = scanner.max_gap_pct
    # === End config load ===

    key = load_key()
    today_iso = args.date
    prev_iso  = prev_trading_day_for(today_iso)

    u_prev  = f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{prev_iso}?adjusted=true"
    u_today = f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{today_iso}?adjusted=true"

    prev = http_get_json(u_prev, key)
    today = http_get_json(u_today, key)

    # Holiday/weekend: Polygon returns 200 with empty results/resultsCount=0
    today_results = today.get("results") or []
    today_count = today.get("resultsCount", len(today_results))
    if today_count == 0:
        print(f"[INFO] No grouped results for {today_iso} (likely non-trading day).")
        # still emit an empty gap map so downstream tools don't break
        write_gap_map([], today_iso)
        if not args.no_write:
            write_universe([], Path(args.out))
        return

    prev_close = {}
    for r in (prev.get("results") or []):
        t = r.get("T"); c = r.get("c")
        if t and c is not None:
            try:
                prev_close[t] = float(c)
            except Exception:
                pass

    rows = []
    for r in today_results:
        t = r.get("T"); o = r.get("o")
        if not t or o is None:
            continue
        pc = prev_close.get(t)
        if not pc or pc <= 0:
            continue
        try:
            o = float(o)
        except Exception:
            continue
        gap_pct = (o - pc) / pc * 100.0
        # Use validated JSON values (not CLI) for banding and min-gap
        if price_min <= o <= price_max and gap_pct >= min_gap_pct:
            rows.append((t, round(gap_pct, 2), round(o, 4)))

    rows.sort(key=lambda x: x[1], reverse=True)

    print(f"Open-gap gappers (open vs prev close)  price=[{price_min}..{price_max}]  min_gap={min_gap_pct}%")
    if rows:
        print(f"{'SYMBOL':<8} {'GAP%':>7} {'PRICE':>8}")
        # Respect preview to Top-N for the on-screen list as well
        preview_n = args.top if isinstance(args.top, int) and args.top > 0 else len(rows)
        for t, g, p in rows[:preview_n]:
            print(f"{t:<8} {g:>7.2f} {p:>8.4f}")
    else:
        print("(none)")

    # --- NEW: always write the gap-map sidecar (independent of --no-write) ---
    write_gap_map(rows, today_iso)

    if not args.no_write:
        # Determine final list to write
        if isinstance(args.top, int) and args.top > 0:
            symbols_trimmed = [t for (t, _, _) in rows[:args.top]]
            # Clear & truthful logging
            if len(rows) > args.top:
                print(f"[UNIVERSE] Trimmed to Top-{args.top} symbols (from {len(rows)})")
            else:
                print(f"[UNIVERSE] Using all {len(symbols_trimmed)} symbols (list shorter than Top-{args.top})")
        else:
            symbols_trimmed = [t for (t, _, _) in rows]
            print(f"[UNIVERSE] Using full list (no trim). Count={len(symbols_trimmed)}")

        write_universe(symbols_trimmed, Path(args.out))

if __name__ == "__main__":
    main()