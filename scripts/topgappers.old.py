#!/usr/bin/env python3
# scripts/topgappers.py — prev-trading-day gappers (price band + min gap)

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
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=True)
except Exception as e:
    sys.stderr.write(f"[WARN] dotenv load failed: {e}\n")
# --- end bootstrap ---

DEF_OUT = ROOT / "data" / "samples" / "universe_sample.txt"

def load_key() -> str:
    k = (os.environ.get("POLYGON_API_KEY") or "").strip().strip('"').strip("'")
    if not k:
        print("[ERR] POLYGON_API_KEY missing (set it in .env)", file=sys.stderr)
        sys.exit(1)
    return k

def http_get_json(url: str, key: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}", "User-Agent": "midas_v2/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def prev_trading_day_for(date_iso: str) -> str:
    # Use helper (now header-based); fallback to prior calendar day if it fails
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
    out_path.write_text("\n".join(symbols) + "\n", encoding="ascii")
    print(f"Wrote {len(symbols)} symbols -> {out_path}")

def main():
    ap = ArgumentParser(description="Build universe from open-gap vs previous trading day")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--min-price", type=float, default=1.0)
    ap.add_argument("--max-price", type=float, default=20.0)
    ap.add_argument("--min-gap",   type=float, default=5.0)
    ap.add_argument("--top",       type=int,   default=50)  # print top N; file includes all matches
    ap.add_argument("--out",       default=str(DEF_OUT))
    ap.add_argument("--no-write",  action="store_true")
    ap.add_argument("--session",   default=None, help="(ignored; compatibility)")
    args, _ = ap.parse_known_args()

    key = load_key()
    today_iso = args.date
    prev_iso  = prev_trading_day_for(today_iso)

    u_prev  = f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{prev_iso}?adjusted=true"
    u_today = f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{today_iso}?adjusted=true"

    prev = http_get_json(u_prev, key)
    today = http_get_json(u_today, key)

    prev_close = {}
    for r in (prev.get("results") or []):
        t = r.get("T"); c = r.get("c")
        if t and c is not None:
            try: prev_close[t] = float(c)
            except: pass

    rows = []
    for r in (today.get("results") or []):
        t = r.get("T"); o = r.get("o")
        if not t or o is None: continue
        pc = prev_close.get(t)
        if not pc or pc <= 0:  continue
        try: o = float(o)
        except: continue
        gap_pct = (o - pc) / pc * 100.0
        if args.min_price <= o <= args.max_price and gap_pct >= args.min_gap:
            rows.append((t, round(gap_pct, 2), round(o, 4)))

    rows.sort(key=lambda x: x[1], reverse=True)

    print(f"Open-gap gappers (open vs prev close)  price=[{args.min_price}..{args.max_price}]  min_gap={args.min_gap}%")
    if rows:
        print(f"{'SYMBOL':<8} {'GAP%':>7} {'PRICE':>8}")
        for t, g, p in rows[:args.top]:
            print(f"{t:<8} {g:>7.2f} {p:>8.4f}")
    else:
        print("(none)")

    if not args.no_write:
        symbols_all = [t for (t, _, _) in rows]
        write_universe(symbols_all, Path(args.out))

if __name__ == "__main__":
    main()