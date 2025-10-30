#!/usr/bin/env python3
# scripts/topgappers.py (prev-trading-day FIX ONLY)
import sys, os, json, subprocess, urllib.request
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime, timedelta

DEF_OUT = Path("data/samples/universe_sample.txt")

def load_key():
    k = os.environ.get("POLYGON_API_KEY", "").strip()
    if not k:
        envp = Path(".env")
        if envp.exists():
            for line in envp.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.strip().startswith("POLYGON_API_KEY="):
                    k = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not k:
        print("[ERR] POLYGON_API_KEY missing (set env var or .env)", file=sys.stderr)
        sys.exit(1)
    return "".join(k.split())

def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "midas_v2/1.0"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))

def prev_trading_day_for(date_iso: str) -> str:
    try:
        r = subprocess.run([sys.executable, "scripts/prev_trading_day_polygon.py", "--date", date_iso],
                           capture_output=True, text=True, check=True)
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if "Previous trading day for" in line and " is " in line:
                return line.split(" is ")[-1].strip()
    except Exception:
        d = datetime.fromisoformat(date_iso).date()
        return (d - timedelta(days=1)).isoformat()
    d = datetime.fromisoformat(date_iso).date()
    return (d - timedelta(days=1)).isoformat()

def write_universe(symbols, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(symbols), encoding="ascii")
    print(f"Wrote {len(symbols)} symbols -> {out_path}")

def main():
    ap = ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--min-price", type=float, default=1.0)
    ap.add_argument("--max-price", type=float, default=20.0)
    ap.add_argument("--min-gap",   type=float, default=5.0)
    ap.add_argument("--top",       type=int,   default=50)
    ap.add_argument("--out",       default=str(DEF_OUT))
    ap.add_argument("--no-write",  action="store_true")
    args = ap.parse_args()

    key = load_key()
    today_iso = args.date
    prev_iso  = prev_trading_day_for(today_iso)

    url_prev  = f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{prev_iso}?adjusted=true&apiKey={key}"
    url_today = f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{today_iso}?adjusted=true&apiKey={key}"
    prev = http_get_json(url_prev)
    today = http_get_json(url_today)

    prev_close = {}
    for r in (prev.get("results") or []):
        t = r.get("T"); c = r.get("c")
        if t and c is not None:
            try:
                prev_close[t] = float(c)
            except Exception:
                pass

    rows = []
    for r in (today.get("results") or []):
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
        if args.min_price <= o <= args.max_price and gap_pct >= args.min_gap:
            rows.append((t, round(gap_pct, 2), round(o, 4)))

    rows.sort(key=lambda x: x[1], reverse=True)

    print(f"Open-gap gappers (open vs prev close)  price=[{args.min_price}..{args.max_price}]  min_gap={args.min_gap}%")
    if not rows:
        print("(none)")
    else:
        print(f"{'SYMBOL':<8} {'GAP%':>7} {'PRICE':>8}")
        for t, g, p in rows[:args.top]:
            print(f"{t:<8} {g:>7.2f} {p:>8.4f}")

    if not args.no_write:
        symbols_all = [t for (t, _, _) in rows]
        write_universe(symbols_all, Path(args.out))

if __name__ == "__main__":
    main()
