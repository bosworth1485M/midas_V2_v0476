# scripts/enrich_universe_catalyst.py
import argparse, os, re, time, csv
from pathlib import Path

try:
    import requests  # used if POLYGON_API_KEY present; otherwise headlines may be empty
except Exception:
    requests = None

KEYWORDS = [
    (r"\b(FDA|approval|approv|clearance|phase\s*(II|III)|pivotal|endpoint|trial|NDA|BLA)\b", 2),
    (r"\b(earnings|EPS|revenue|guidance|beat|raises?|surprise)\b", 2),
    (r"\b(acquisition|merger|buyout|takeover)\b", 2),
    (r"\b(contract|award|partnership|collaborat|licens(e|ing))\b", 1),
    (r"\b(upgrade|initiates? coverage|price target)\b", 1),
    (r"\b(spin[- ]?off|divest|asset sale)\b", 1),
]

JUNK_CLASS_5TH = {"W","U","R","P"}

def is_junky(sym: str) -> bool:
    s = sym.upper().strip()
    if len(s) == 5 and s[-1] in JUNK_CLASS_5TH: return True
    if "." in s:
        tail = s.split(".")[-1]
        if tail.isalpha() and len(tail) == 1: return True
    if "-" in s:
        tail = s.split("-")[-1]
        if tail.isalpha() and len(tail) == 1: return True
    if len(s) >= 2 and s[-2] == "P" and s[-1].isalpha(): return True
    return False

def score_headlines(headlines):
    best, best_score = "", 0
    for title in headlines:
        if not title: continue
        s = 0
        lt = title.lower()
        for rx, pts in KEYWORDS:
            if re.search(rx, lt, flags=re.IGNORECASE):
                s = max(s, pts)
        if s > best_score:
            best_score, best = s, title
    return best_score, best

def polygon_fetch_titles(ticker: str, day: str, api_key: str, limit: int = 100) -> list:
    if not requests or not api_key:
        return []
    base = "https://api.polygon.io/v2/reference/news"
    start = f"{day}T00:00:00Z"
    end   = f"{day}T23:59:59Z"
    params = {
        "ticker": ticker.upper(),
        "published_utc.gte": start,
        "published_utc.lte": end,
        "order": "desc",
        "limit": max(1, min(limit, 1000)),
        "apiKey": api_key,
    }
    try:
        r = requests.get(base, params=params, timeout=12)
        if r.status_code != 200:
            return []
        data = r.json()
        res = data.get("results") or []
        titles = []
        for it in res:
            title = (it.get("title") or it.get("headline") or "").strip()
            if title:
                titles.append(title)
        return titles
    except Exception:
        return []

def read_txt_symbols(path: Path) -> list:
    if not path.exists():
        raise SystemExit(f"[ERROR] input file not found: {path}")
    syms = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip().upper()
        if s: syms.append(s)
    seen, out = set(), []
    for s in syms:
        if s not in seen: seen.add(s); out.append(s)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--in", dest="inp", required=True, help="Path to raw gappers TXT")
    ap.add_argument("--out", dest="out_path", required=True, help="Path to write kept catalyst-only TXT")
    ap.add_argument("--min-score", type=float, default=1.0, help="Minimum score to KEEP a symbol (default 1)")
    ap.add_argument("--limit", type=int, default=100, help="Max news items to scan per symbol (default 100)")
    ap.add_argument("--rate-sleep", type=float, default=0.25, help="Seconds to sleep between symbols (default 0.25)")
    ap.add_argument("--print-news", action="store_true", help="Print any headlines found per symbol")
    ap.add_argument("--max-print", type=int, default=3, help="Max headlines to print per symbol (default 3)")
    args = ap.parse_args()

    day = args.date
    ymd = day.replace("-", "")

    inp = Path(args.inp)
    out_kept = Path(args.out_path).resolve()

    # Output locations
    audit_dir = Path(f"out/{ymd}/catalyst"); audit_dir.mkdir(parents=True, exist_ok=True)
    audit_csv = audit_dir / f"catalyst_news_{day}.csv"
    data_csv_dir = Path("data/catalyst"); data_csv_dir.mkdir(parents=True, exist_ok=True)
    data_csv = data_csv_dir / f"catalyst_news_{day}.csv"
    news_dump = audit_dir / f"news_found_{day}.txt"

    candidates = read_txt_symbols(inp)
    print(f"[INFO] {day} candidates={len(candidates)}  min_score={args.min_score}  limit={args.limit}")

    api_key = os.getenv("POLYGON_API_KEY","").strip()

    kept, rows = [], []
    dump_lines = []

    for i, sym in enumerate(candidates, 1):
        # If you want to exclude junk here, uncomment next two lines.
        # if is_junky(sym):
        #     print(f"[DROP] {sym:<6} junk-class"); continue

        titles = polygon_fetch_titles(sym, day, api_key, args.limit)
        score, best = score_headlines(titles)

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

        if score >= args.min_score:
            print(f"[KEEP] {sym:<6} score={int(score)} title='{(best or '')[:80]}'")
            kept.append(sym)
        else:
            print(f"[DROP] {sym:<6} score={int(score)}")

        rows.append({"symbol": sym.upper(), "score": int(score), "headline": best})
        if args.rate_sleep > 0 and i < len(candidates):
            time.sleep(args.rate_sleep)

    # Write kept list (TXT)
    out_kept.parent.mkdir(parents=True, exist_ok=True)
    out_kept.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    print(f"[OK ] Wrote {len(kept)} symbols -> {out_kept}")

    # Write news dump (for humans)
    if args.print_news:
        news_dump.write_text("\n".join(dump_lines) + ("\n" if dump_lines else ""), encoding="utf-8")
        print(f"[DUMP] {news_dump}")

    # Write AUDIT CSV (out/…)
    with audit_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["symbol","score","headline"])
        w.writeheader()
        for r in rows:
            w.writerow({"symbol": r["symbol"].upper(), "score": r["score"], "headline": r.get("headline","")})
    print(f"[AUDIT] {audit_csv}")

    # Write CANONICAL CSV (data/…)
    with data_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["symbol","score","headline"])
        w.writeheader()
        for r in rows:
            w.writerow({"symbol": r["symbol"].upper(), "score": r["score"], "headline": r.get("headline","")})
    print(f"[CANONICAL] {data_csv}")

    head = ", ".join((kept or [])[:12])
    print(f"[SUMMARY] kept={len(kept)}  head: {head}")

if __name__ == "__main__":
    main()