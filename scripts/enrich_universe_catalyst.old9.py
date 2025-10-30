#!/usr/bin/env python3
"""
Build a catalyst-qualified universe for a given date by scoring Polygon news.

Inputs (RAW, no catalyst applied yet):
  data/universe_topgappers_YYYY-MM-DD.txt   # one symbol per line (from topgappers.py)

Outputs:
  data/catalyst/universe_YYYY-MM-DD.txt     # kept symbols (score >= min-score, optional top-N cap)
  out/YYYYMMDD/catalyst/catalyst_news_YYYY-MM-DD.csv  # audit: best headline/score/time per symbol
"""

# --- bootstrap: ensure src on path + load .env from project root (override) ---
import os, sys, csv, json, time, argparse, urllib.parse, urllib.request
from pathlib import Path
from datetime import datetime
from urllib.error import HTTPError

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

POLY_BASE = "https://api.polygon.io/v2/reference/news"

# Simple keyword scoring (tune later if needed)
WL = [
    "fda", "phase", "trial", "contract", "upgrade",
    "beats", "beat", "raises guidance", "raised guidance", "guidance raised",
]
BL = [
    "atm", "offering", "dilution", "reverse split",
    "nasdaq deficiency", "deficiency notice", "going concern", "resignation",
]

def parse_args():
    ap = argparse.ArgumentParser(description="Filter a universe by scoring Polygon news for a given date.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--in", dest="inp", required=True, help="Raw top-gappers file (one symbol per line)")
    ap.add_argument("--out", required=True, help="Output catalyst universe file")
    ap.add_argument("--min-score", type=int, default=1, help="Minimum score to keep (default 1)")
    ap.add_argument("--limit", type=int, default=0, help="Optional cap on kept symbols (0 = no cap)")
    ap.add_argument("--rate-sleep", type=float, default=0.3, help="Seconds to sleep between API calls (default 0.3)")
    return ap.parse_args()

def yyyymmdd(d: str) -> str:
    return datetime.strptime(d, "%Y-%m-%d").strftime("%Y%m%d")

def load_key() -> str:
    # Mirror your working scripts: read from ENV after .env override, then sanitize
    k = (os.environ.get("POLYGON_API_KEY") or "").strip().strip('"').strip("'")
    if not k:
        raise SystemExit("[ERR] POLYGON_API_KEY missing (set it in .env or environment)")
    return k

def read_universe(path: Path):
    syms = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip().upper()
        if s and not s.startswith("#"):
            syms.append(s)
    return syms

def score_text(text: str) -> int:
    t = (text or "").lower()
    sc = 0
    for w in WL:
        if w in t: sc += 1
    for b in BL:
        if b in t: sc -= 2
    return sc

def http_get_json(url: str, headers: dict, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def fetch_news_bearer(ticker: str, date: str, key: str) -> list:
    params = {
        "ticker": ticker.upper(),
        "published_utc.gte": f"{date}T00:00:00Z",
        "published_utc.lte": f"{date}T23:59:59Z",
        "order": "asc",
        "limit": "100",
    }
    url = POLY_BASE + "?" + urllib.parse.urlencode(params)
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json", "User-Agent": "midas_v2/news/1.0"}
    return http_get_json(url, headers).get("results", [])

def fetch_news_header_key(ticker: str, date: str, key: str) -> list:
    params = {
        "ticker": ticker.upper(),
        "published_utc.gte": f"{date}T00:00:00Z",
        "published_utc.lte": f"{date}T23:59:59Z",
        "order": "asc",
        "limit": "100",
    }
    url = POLY_BASE + "?" + urllib.parse.urlencode(params)
    headers = {"X-Polygon-API-Key": key, "Accept": "application/json", "User-Agent": "midas_v2/news/1.0"}
    return http_get_json(url, headers).get("results", [])

def best_headline(results):
    best = (0, "", "")
    for item in results:
        title = item.get("title") or ""
        desc  = item.get("description") or ""
        ts    = item.get("published_utc") or ""
        sc    = score_text(title + " " + desc)
        if (sc, ts) > (best[0], best[1]):
            best = (sc, ts, title)
    return best  # (score, ts, title)

def main():
    args = parse_args()
    key  = load_key()

    raw_path = Path(args.inp)
    if not raw_path.exists():
        raise SystemExit(f"Input universe not found: {raw_path}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    candidates = read_universe(raw_path)
    if not candidates:
        raise SystemExit(f"No symbols found in {raw_path}")

    audit_dir = Path("out") / yyyymmdd(args.date) / "catalyst"
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_csv = audit_dir / f"catalyst_news_{args.date}.csv"

    kept, rows = [], []
    print(f"[INFO] {args.date} candidates={len(candidates)}  min_score={args.min_score}  limit={args.limit or 'none'}")

    for sym in candidates:
        # Try Bearer (your normal pattern); on 401/403, fallback to X-Polygon-API-Key header
        try:
            results = fetch_news_bearer(sym, args.date, key)
        except HTTPError as e:
            body = ""
            try: body = e.read().decode("utf-8", "ignore")
            except Exception: pass
            if e.code in (401, 403):
                print(f"[AUTH] {sym}: {e.code} {e.reason}; retrying with X-Polygon-API-Key. Server said: {body[:180]!r}")
                results = fetch_news_header_key(sym, args.date, key)
            else:
                raise

        sc, ts, ttl = best_headline(results)
        rows.append({"ticker": sym, "count": len(results), "best_score": sc, "best_time_utc": ts, "best_headline": ttl})
        if sc >= args.min_score:
            kept.append(sym); print(f"[KEEP] {sym:<6} score={sc} title={ttl[:90]!r}")
        else:
            print(f"[DROP] {sym:<6} score={sc}")

        time.sleep(args.rate_sleeps if hasattr(args, "rate_sleeps") else args.rate_sleep)

    if args.limit and len(kept) > args.limit:
        kept = kept[:args.limit]
        print(f"[CAP ] limited to top {args.limit} kept symbols (preserving input order).")

    if kept:
        out_path.write_text("\n".join(kept) + "\n", encoding="utf-8")
        print(f"[OK ] Wrote {len(kept)} symbols -> {out_path}")
    else:
        print("[WARN] No symbols met the threshold; wrote nothing.")

    with audit_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ticker","count","best_score","best_time_utc","best_headline"])
        w.writeheader(); w.writerows(rows)
    print(f"[AUDIT] {audit_csv}")

if __name__ == "__main__":
    main()