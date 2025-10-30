# scripts/topgappers.py
# Open-gap (today_open vs yesterday_close) top gappers.
# Prints list and overwrites data/samples/universe_sample.txt each run unless --no-write.

import os, sys, json, urllib.request, urllib.error
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime, timedelta

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

def get_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "midas_v2/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"[ERR] HTTP {e.code} for {url}\n{body[:200]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERR] {e}", file=sys.stderr)
        sys.exit(1)

def grouped(date, key):
    url = f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{date}?adjusted=true&apiKey={key}"
    return get_json(url)

def main():
    ap = ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--min-price", type=float, default=1.0)
    ap.add_argument("--max-price", type=float, default=20.0)
    ap.add_argument("--min-gap",   type=float, default=5.0)   # percent
    ap.add_argument("--top",       type=int,   default=50)    # rows to print
    ap.add_argument("--no-write",  action="store_true", help="Do not overwrite universe_sample.txt")
    args = ap.parse_args()

    key = load_key()
    d  = datetime.fromisoformat(args.date).date()
    dy = (d - timedelta(days=1)).isoformat()

    prev = grouped(dy, key)
    today = grouped(args.date, key)

    prev_close = {}
    for r in prev.get("results") or []:
        t = r.get("T"); c = r.get("c")
        if t and c is not None:
            try:
                prev_close[t] = float(c)
            except:
                pass

    rows = []
    for r in today.get("results") or []:
        t = r.get("T"); o = r.get("o")
        if not t or o is None:
            continue
        pc = prev_close.get(t)
        if not pc or pc <= 0:
            continue
        o = float(o)
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
        outp = Path("data/samples/universe_sample.txt")
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text("\n".join([t for t, _, _ in rows]), encoding="ascii")
        print(f"Wrote {len(rows)} symbols -> {outp}")

if __name__ == "__main__":
    main()