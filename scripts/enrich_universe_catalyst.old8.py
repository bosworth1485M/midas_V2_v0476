#!/usr/bin/env python3
# scripts/enrich_universe_catalyst.py
# v0.3.21: A-only catalysts (no B-fill), denylist hygiene, magnitude-aware scoring, .WS drop, VIS log

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from dotenv import load_dotenv  # optional
    load_dotenv()
except Exception:
    pass

ALLOW_LIST_POSITIVE = [

# Helper: tidy headline for console output
def _trunc_headline(s: str, n: int = 110) -> str:
    try:
        s = (s or '').strip()
        return (s[: n - 1] + 'â€¦') if len(s) > n else s
    except Exception:
        return ''
    r"beats", r"tops", r"crushes", r"above\s+guidance",
    r"profit\s+up", r"turns?\s+profitable", r"returns?\s+to\s+profit",
    r"revenue\s+up", r"sales\s+(?:jump|surge|soar|rise|grow)",
    r"eps\s+up", r"guidance\s+raise", r"raises?\s+guidance",
    r"approval", r"clearance", r"fda", r"partnership", r"contract\s+win"
]

_DENY_PATTERNS = re.compile(
    r"(?:"  # hard/soft negatives â†’ DROP
    r"loss\s+narrows|narrower\s+loss|lower\s+loss|reduced\s+loss|net\s+loss|wider\s+loss|loss\s+widens|"
    r"miss(?:es)?|below\s+expectations|falls\s+short|"
    r"guidance\s+cut|guidance\s+lower(?:s|ed)?|lowers\s+outlook|cuts\s+outlook|"
    r"downgrade|downgraded|"
    r"investigation|probe|sec\s+inquiry|accounting\s+issues|"
    r"going\s+concern|bankruptcy|chapter\s+11|de-?list|delisting|"
    r"layoffs|job\s+cuts|"
    r"halts?\s+trading"
    r")",
    flags=re.IGNORECASE
)

def mag_to_score(pct: float) -> float:
    if pct >= 80: return 3.5
    if pct >= 60: return 3.0
    if pct >= 40: return 2.5
    if pct >= 25: return 2.0
    return 1.0

def perc_match(headline: str) -> float:
    if not headline:
        return 0.0
    tokens = [
        "beat", "beats", "tops", "crushes", "above guidance", "profit up", "turns profitable",
        "returns to profit", "revenue up", "sales jump", "sales surge", "sales soar",
        "eps up", "approval", "clearance", "fda", "partnership", "contract win", "raises guidance"
    ]
    h = (headline or "").lower()
    hits = sum(1 for t in tokens if t in h)
    base = max(1, len(tokens))
    pct = 100.0 * hits / base
    return min(100.0, pct * 6.0)

def is_headline_denied(headline: str) -> bool:
    return bool(_DENY_PATTERNS.search(headline or ""))

def grade_from_score(score: float) -> str:
    if score >= 2.0: return "A"
    if score >= 1.0: return "B"
    return "0"

def polygon_fetch_news(symbol: str, date_ymd: str, limit: int = 5) -> List[Dict]:
    import urllib.request, urllib.parse
    key = os.getenv("POLYGON_API_KEY")
    if not key:
        return []
    base = "https://api.polygon.io/v2/reference/news"
    params = {
        "ticker": symbol.upper(),
        "limit": str(limit),
        "published_utc.gte": f"{date_ymd}T00:00:00Z",
        "published_utc.lte": f"{date_ymd}T23:59:59Z",
        "apiKey": key
    }
    url = f"{base}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            out = []
            for r in results:
                out.append({
                    "published_utc": r.get("published_utc") or "",
                    "title": (r.get("title") or "").strip()
                })
            return out
    except Exception:
        return []

def pick_best_headline(news_items: List[Dict]) -> Tuple[str, str]:
    best = ("", "")
    best_score = -1.0
    for n in news_items:
        title = (n.get("title") or "").strip()
        tscore = perc_match(title)
        if tscore > best_score:
            best = (title, n.get("published_utc") or "")
            best_score = tscore
    return best

def read_universe(path: Path) -> List[str]:
    syms: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        t = line.strip()
        if not t: continue
        syms.append(t.split(",")[0].strip().upper())
    return syms

def write_txt(path: Path, rows: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        for r in rows:
            f.write(r + "\n")

def write_csv(path: Path, headers: List[str], rows: List[List[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in rows:
            w.writerow(r)

def enrich_and_pick(date_ymd: str,
                    src_universe: Path,
                    out_scores_csv: Path,
                    min_grade: int = 2,
                    allow_b_fill: bool = False,
                    news_limit: int = 5,
                    drop_ws: bool = True) -> None:

    ymd_compact = date_ymd.replace("-", "")
    out_dir = Path(f"out/{ymd_compact}/catalyst")
    out_dir.mkdir(parents=True, exist_ok=True)

    symbols = read_universe(src_universe)
    original_len = len(symbols)

    if drop_ws:
        symbols = [s for s in symbols if not s.endswith(".WS")]
        dropped = original_len - len(symbols)
        if dropped > 0:
            print(f"[DENYLIST] Dropped {dropped} .WS symbols pre-enrich")

    print(f"[INFO] {date_ymd} candidates={len(symbols)}  min_grade={min_grade} allow_b_fill={bool(allow_b_fill)}")

    audit_rows: List[List[str]] = []
    scores_rows: List[List[str]] = []  # [grade, symbol, score, best_headline]

    kept_symbols: List[str] = []
    kept_meta: Dict[str, Dict] = {}
    meta_all: Dict[str, Dict] = {}

    for sym in symbols:
        news_items = polygon_fetch_news(sym, date_ymd, limit=news_limit)
        best_headline, best_time = pick_best_headline(news_items)

        if is_headline_denied(best_headline):
            print(f"[DROP NEG] {sym:<6} reason='denylist' headline={best_headline!r}")
            continue

        pct = perc_match(best_headline)
        score = mag_to_score(pct)
        grade = grade_from_score(score)
        scores_rows.append([grade, sym, f"{score:.1f}", best_headline])
        meta_all[sym] = {"grade": grade, "score": score, "headline": best_headline}

        if pct >= 1.0:
            print(f"[MAG] {sym} news matched {pct:.1f}% -> score {score:.1f}")

        audit_rows.append([sym, str(len(news_items)), f"{score:.1f}", best_time, best_headline])

        numeric_grade = 2 if grade == "A" else (1 if grade == "B" else 0)
        if numeric_grade >= min_grade:
            kept_symbols.append(sym)
            kept_meta[sym] = {"grade": grade, "score": score, "headline": best_headline}

    # Optional B-fill if no A-grade kept and flag is set
    if not kept_symbols and allow_b_fill:
        b_candidates = [s for s in symbols if meta_all.get(s, {}).get('grade') == 'B']
        b_candidates.sort(key=lambda s: meta_all[s]['score'], reverse=True)
        b_take = b_candidates[:5]
        for s in b_take:
            kept_symbols.append(s)
            kept_meta[s] = meta_all[s]
        if b_take:
            print(f"[FALLBACK] allow_b_fill=True â†’ added {len(b_take)} B-grade symbols: {', '.join(b_take)}")

    kept_symbols.sort(key=lambda s: kept_meta[s]["score"], reverse=True)

    # scores
    write_csv(out_scores_csv, ["grade", "symbol", "score", "best_headline"], scores_rows)
    print(f"[OK ] Wrote {len(scores_rows)} rows -> {out_scores_csv}")

    # audit
    audit_csv = out_dir / f"catalyst_news_{date_ymd}.csv"
    write_csv(audit_csv, ["ticker", "count", "best_score", "best_time_utc", "best_headline"], audit_rows)
    print(f"[AUDIT] {audit_csv}")

    # picked
    picked_csv = out_dir / f"catalyst_universe_{date_ymd}.csv"
    picked_rows = [[s, kept_meta[s]["grade"], f"{kept_meta[s]['score']:.1f}", kept_meta[s]["headline"]] for s in kept_symbols]
    write_csv(picked_csv, ["symbol", "grade", "score", "best_headline"], picked_rows)

    picked_txt = Path(f"data/universe_catalyst_{date_ymd}.txt")
    write_txt(picked_txt, kept_symbols)
    picked_txt2 = Path(f"data/catalyst/universe_catalyst_{date_ymd}.txt")
    write_txt(picked_txt2, kept_symbols)

    kept_set = set(kept_symbols)
    dropped = [s for s in symbols if s not in kept_set]
    print(f"[PICKER] kept={len(kept_symbols)} dropped={len(dropped)} min_grade={min_grade} allow_b_fill={bool(allow_b_fill)}")
    if kept_symbols:
        for _s in kept_symbols[:15]:
        _m = kept_meta.get(_s) or meta_all.get(_s, {})
        print(f"[KEEP] {_s}  grade={_m.get('grade','?')} score={_m.get('score','?')}  headline={((_m.get('headline') or 'NO HEADLINE').strip())[:110]}")
    if len(kept_symbols) > 15:
        print(f"[KEEP] ...(and {len(kept_symbols)-15} more)")
    for _s in dropped[:15]:
        _m = meta_all.get(_s, {})
        print(f"[DROP] {_s}  grade={_m.get('grade','?')} score={_m.get('score','?')}  headline={((_m.get('headline') or 'NO NEWS').strip())[:110]}")
    if len(dropped) > 15:
        print(f"[DROP] ...(and {len(dropped)-15} more)")
    print(f"[CATALYST] picked={len(kept_symbols)} -> {picked_txt}")
    print(f"[VIS] news_found={sum(1 for _,_,_,_,h in audit_rows if h)} news_missing={sum(1 for _,_,_,_,h in audit_rows if not h)} total={len(audit_rows)}")
    print(f"[SANITIZE] Applied negative-headline guard in {out_scores_csv.name}")

def main():
    p = argparse.ArgumentParser(description="Enrich universe with catalyst scores and pick A-only symbols.")
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--in", dest="infile", default=None, help="Universe input txt (default: data/samples/universe_sample.txt)")
    p.add_argument("--out", dest="outfile", default=None, help="Scores CSV output path (default: out/<YYYYMMDD>/catalyst/catalyst_scores_<DATE>.csv)")
    p.add_argument("--min-grade", type=int, default=2, help="2=A-only, 1=allow B, 0=all (default: 2)")
    p.add_argument("--allow-b-fill", action="store_true", help="(Disabled in v0.3.21 by default)")
    p.add_argument("--limit", type=int, default=5, help="Max news items per symbol (Polygon)")
    p.add_argument("--drop-ws", action="store_true", default=True, help="Drop *.WS from universe (default on)")
    args = p.parse_args()

    # Defaults to match older UX
    infile  = args.infile  or "data/samples/universe_sample.txt"
    ymd_compact = args.date.replace("-", "")
    default_out = f"out/{ymd_compact}/catalyst/catalyst_scores_{args.date}.csv"
    outfile = args.outfile or default_out
    Path(outfile).parent.mkdir(parents=True, exist_ok=True)

    try:
        dt.datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print("[ERR] --date must be YYYY-MM-DD", file=sys.stderr)
        sys.exit(2)

    enrich_and_pick(
        date_ymd=args.date,
        src_universe=Path(infile),
        out_scores_csv=Path(outfile),
        min_grade=args.min_grade,
        allow_b_fill=args.allow_b_fill,
        news_limit=args.limit,
        drop_ws=args.drop_ws
    )

if __name__ == "__main__":
    main()
