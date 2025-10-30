# scripts/enrich_universe_catalyst.py
#!/usr/bin/env python3
"""
Build a catalyst-qualified universe for a given date by scoring Polygon news.
Mirrors OLD key handling:
 - load .env from repo root with override=True
 - read POLYGON_API_KEY from env (or --polygon-key)
 - fetch with Bearer first; on 401/403 retry with X-Polygon-API-Key
Outputs:
 - Kept list (TXT) at --out
 - Audit CSV at out/YYYYMMDD/catalyst/catalyst_news_YYYY-MM-DD.csv
 - Canonical CSV at data/catalyst/catalyst_news_YYYY-MM-DD.csv  (symbol,score,headline)
"""

import argparse, os, re, time, csv, json, sys, urllib.parse, urllib.request, urllib.error
from pathlib import Path

# ---------- bootstrap: dotenv exactly like OLD ----------
ROOT = Path(__file__).resolve().parent.parent  # repo root (…/midas_V2)
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv(ROOT / ".env", override=True)
except Exception as e:
    sys.stderr.write(f"[WARN] dotenv load failed: {e}\n")

POLY_BASE = "https://api.polygon.io/v2/reference/news"

# ---------- scoring keywords (simple + transparent) ----------
KEYWORDS = [
    (r"\b(FDA|approval|approv|clearance|phase\s*(II|III)|pivotal|endpoint|trial|NDA|BLA)\b", 2),
    (r"\b(earnings|EPS|revenue|guidance|beat|raises?|surprise)\b", 2),
    (r"\b(acquisition|merger|buyout|takeover)\b", 2),
    (r"\b(contract|award|partnership|collaborat|licens(e|ing))\b", 1),
    (r"\b(upgrade|initiates? coverage|price target)\b", 1),
    (r"\b(spin[- ]?off|divest|asset sale)\b", 1),
]

JUNK_5TH = {"W","U","R","P"}  # NASDAQ 5th-letter classes (warrant/unit/rights/preferred)

def is_junky(sym: str) -> bool:
    s = sym.upper().strip()
    if len(s) == 5 and s[-1] in JUNK_5TH: return True
    if "." in s:
        tail = s.split(".")[-1]
        if tail.isalpha() and len(tail) == 1: return True
    if "-" in s:
        tail = s.split("-")[-1]
        if tail.isalpha() and len(tail) == 1: return True
    if len(s) >= 2 and s[-2] == "P" and s[-1].isalpha(): return True
    return False

def parse_args():
    ap = argparse.ArgumentParser(description="Filter a universe by scoring Polygon news for a given date.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--in", dest="inp", required=True, help="Raw top-gappers file (one symbol per line)")
    ap.add_argument("--out", dest="out_path", required=True, help="Where to write kept catalyst-only TXT")
    ap.add_argument("--min-score", type=float, default=1.0, help="Minimum score to KEEP a symbol (default 1)")
    ap.add_argument("--limit", type=int, default=100, help="Max news items per symbol (default 100)")
    ap.add_argument("--rate-sleep", type=float, default=0.25, help="Sleep seconds between symbols (default 0.25)")
    ap.add_argument("--polygon-key", dest="polygon_key", help="Polygon API key override (optional)")
    ap.add_argument("--print-news", action="store_true", help="Print any headlines found per symbol")
    ap.add_argument("--max-print", type=int, default=3, help="Max headlines to print per symbol (default 3)")
    return ap.parse_args()

def load_key(cli_override: str | None) -> str:
    # Mirror OLD: read from env (after dotenv), sanitize quotes; allow CLI override
    k = (cli_override or os.environ.get("POLYGON_API_KEY") or "").strip().strip('"').strip("'")
    if not k:
        raise SystemExit("[ERR] POLYGON_API_KEY missing (set it in .env or environment, or pass --polygon-key)")
    return k

def http_get_json(url: str, headers: dict) -> dict:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = resp.read()
    try:
        return json.loads(data.decode("utf-8", "replace") or "{}")
    except Exception:
        return {}

def fetch_news_bearer(ticker: str, day: str, key: str, limit: int) -> list[dict]:
    params = {
        "ticker": ticker.upper(),
        "published_utc.gte": f"{day}T00:00:00Z",
        "published_utc.lte": f"{day}T23:59:59Z",
        "order": "desc",
        "limit": max(1, min(limit, 1000)),
    }
    url = POLY_BASE + "?" + urllib.parse.urlencode(params)
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json", "User-Agent": "midas_v2/news/1.0"}
    return http_get_json(url, headers).get("results", [])

def fetch_news_header_key(ticker: str, day: str, key: str, limit: int) -> list[dict]:
    params = {
        "ticker": ticker.upper(),
        "published_utc.gte": f"{day}T00:00:00Z",
        "published_utc.lte": f"{day}T23:59:59Z",
        "order": "desc",
        "limit": max(1, min(limit, 1000)),
    }
    url = POLY_BASE + "?" + urllib.parse.urlencode(params)
    headers = {"X-Polygon-API-Key": key, "Accept": "application/json", "User-Agent": "midas_v2/news/1.0"}
    return http_get_json(url, headers).get("results", [])

def titles_from_results(results: list[dict]) -> list[str]:
    out = []
    for it in results or []:
        t = (it.get("title") or it.get("headline") or "").strip()
        if t:
            out.append(t)
    return out

def score_headlines(headlines: list[str]) -> tuple[int, str]:
    best, best_score = "", 0
    for title in headlines:
        if not title:
            continue
        s = 0
        lt = title.lower()
        for rx, pts in KEYWORDS:
            if re.search(rx, lt, flags=re.IGNORECASE):
                s = max(s, pts)
        if s > best_score:
            best_score, best = s, title
    return best_score, best

def read_txt_symbols(path: Path) -> list[str]:
    if not path.exists():
        raise SystemExit(f"[ERROR] input file not found: {path}")
    raw = [line.strip().upper() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    seen, out = set(), []
    for s in raw:
        if s not in seen:
            seen.add(s); out.append(s)
    return out

def main():
    args = parse_args()
    day = args.date
    ymd = day.replace("-", "")
    raw_path  = Path(args.inp)
    kept_path = Path(args.out_path).resolve()

    audit_dir = Path(f"out/{ymd}/catalyst"); audit_dir.mkdir(parents=True, exist_ok=True)
    audit_csv = audit_dir / f"catalyst_news_{day}.csv"
    dump_txt  = audit_dir / f"news_found_{day}.txt"

    data_dir  = Path("data/catalyst"); data_dir.mkdir(parents=True, exist_ok=True)
    canon_csv = data_dir / f"catalyst_news_{day}.csv"

    syms = read_txt_symbols(raw_path)
    print(f"[INFO] {day} candidates={len(syms)}  min_score={args.min_score}  limit={args.limit}")

    key = load_key(args.polygon_key)
    print("[AUTH] polygon_key=OK (from .env/env/CLI)")

    kept = []
    rows = []
    dump_lines = []

    for i, sym in enumerate(syms, 1):
        # Uncomment to drop junk-class tickers here:
        # if is_junky(sym): print(f"[DROP] {sym:<6} junk-class"); continue

        results = []
        # Try Bearer first, like OLD
        try:
            results = fetch_news_bearer(sym, day, key, args.limit)
        except urllib.error.HTTPError as e:
            # On 401/403, retry with header key (exact OLD behavior)
            try:
                body = e.read().decode("utf-8", "replace")
            except Exception:
                body = ""
            if e.code in (401, 403):
                print(f"[AUTH] {sym}: {e.code} {e.reason}; retrying with X-Polygon-API-Key. Server said: {body[:120]!r}")
                results = fetch_news_header_key(sym, day, key, args.limit)
            else:
                # Non-auth errors: still try header-key once
                results = fetch_news_header_key(sym, day, key, args.limit)
        except Exception:
            # Network or other — try header-key once
            results = fetch_news_header_key(sym, day, key, args.limit)

        titles = titles_from_results(results)

        if args.print_news:
            if titles:
                print(f"[NEWS] {sym}:")
                dump_lines.append(f"[NEWS] {sym}:")
                for t in titles[:max(1, args.max_print)]:
                    print(f"  - {t}")
                    dump_lines.append(f"  - {t}")
            else:
                print(f"[NEWS] {sym}: (none)")
                dump_lines.append(f"[NEWS] {sym}: (none)")

        score, best = score_headlines(titles)
        if score >= args.min_score:
            print(f"[KEEP] {sym:<6} score={int(score)} title='{(best or '')[:80]}'")
            kept.append(sym)
        else:
            print(f"[DROP] {sym:<6} score={int(score)}")

        rows.append({"symbol": sym, "score": int(score), "headline": best})

        if args.rate_sleep > 0 and i < len(syms):
            time.sleep(args.rate_sleep)

    # Write kept TXT
    kept_path.parent.mkdir(parents=True, exist_ok=True)
    kept_path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    print(f"[OK ] Wrote {len(kept)} symbols -> {kept_path}")

    # Optional dump of news lines
    if args.print_news:
        dump_txt.write_text("\n".join(dump_lines) + ("\n" if dump_lines else ""), encoding="utf-8")
        print(f"[DUMP] {dump_txt}")

    # Write audit CSV
    with audit_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["symbol","score","headline"])
        w.writeheader()
        for r in rows:
            w.writerow({"symbol": r["symbol"], "score": r["score"], "headline": r.get("headline","")})
    print(f"[AUDIT] {audit_csv}")

    # Write canonical CSV (strict schema)
    with canon_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["symbol","score","headline"])
        w.writeheader()
        for r in rows:
            w.writerow({"symbol": r["symbol"], "score": r["score"], "headline": r.get("headline","")})
    print(f"[CANONICAL] {canon_csv}")

    head = ", ".join((kept or [])[:12])
    print(f"[SUMMARY] kept={len(kept)}  head: {head}")

if __name__ == "__main__":
    main()