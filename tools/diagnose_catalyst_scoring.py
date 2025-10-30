#!/usr/bin/env python3
# tools/diagnose_catalyst_scoring.py
import argparse, csv, os, re, sys, json
from collections import defaultdict

POS_VERBS_RE = re.compile(r"\b(jump|surge|soar|spike|leap|rise|climb|advance)\w*\b", re.I)
EARNINGS_CUES_RE = re.compile(r"\b(q[1-4]|quarter|earnings|eps|revenue)\b", re.I)
PCT_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")
SEMANTIC_BOOSTERS = [
    r"\bbeat(?:s|en)?\b",
    r"\btop(?:s|ped)?\b",
    r"\babove (?:views|estimates|expectations)\b",
    r"\braise(?:s|d)?\s+guidance\b",
    r"\bupgrade(?:s|d)?\b",
    r"\bfda (?:approv(?:es|ed)|clear(?:s|ed))\b",
    r"\brecord\b|\ball[-\s]?time high\b",
]
SEMANTIC_RE = re.compile("|".join(SEMANTIC_BOOSTERS), re.I)

DEF_PCT_BOOST = 20.0

def read_csv_rows(path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def as_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default

def wants_boost(title, pct_threshold=DEF_PCT_BOOST):
    """Return True if title looks like it deserves +1 boost."""
    tl = (title or "").lower()
    # semantic booster keywords
    if SEMANTIC_RE.search(tl):
        return True, "semantic"
    # magnitude booster (positive verb + % >= threshold)
    mverb = POS_VERBS_RE.search(tl)
    mpct = PCT_RE.search(tl)
    if mverb and mpct:
        pct = as_float(mpct.group(1))
        if pct is not None and pct >= pct_threshold:
            return True, f"posverb_pct>={pct_threshold}"
    return False, ""

def is_earnings_like(title):
    return bool(EARNINGS_CUES_RE.search((title or "")))

def grep_file_for(path, patterns):
    hits = defaultdict(list)
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                for p in patterns:
                    if re.search(p, line, re.I):
                        hits[p].append((i, line.rstrip("\n")))
    except FileNotFoundError:
        pass
    return hits

def main():
    ap = argparse.ArgumentParser(description="Diagnose catalyst scoring bugs (score==2 vs expected 3).")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--root", default=".", help="Project root (default current dir)")
    ap.add_argument("--pct-threshold", type=float, default=DEF_PCT_BOOST, help="Percent needed for magnitude boost (default 20)")
    ap.add_argument("--symbols", nargs="*", help="Optional symbols to focus on (e.g., AVDL MATV XERS)")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    ymd = args.date.replace("-", "")
    canon = os.path.join(root, "data", "catalyst", f"catalyst_news_{args.date}.csv")
    filt  = os.path.join(root, "data", "catalyst", f"catalyst_news_{args.date}_filtered.csv")
    uni   = os.path.join(root, "data", "catalyst", f"universe_hybrid_{args.date}.txt")  # optional, for context

    issues = []

    print(f"[INFO] root={root}")
    print(f"[INFO] canonical CSV: {canon}  (exists={os.path.exists(canon)})")
    print(f"[INFO] filtered  CSV: {filt}   (exists={os.path.exists(filt)})")
    if not os.path.exists(canon):
        print("[FATAL] Canonical catalyst CSV not found. Run enrich_universe_catalyst.py first.")
        return 2

    rows_canon = read_csv_rows(canon)
    rows_filt  = read_csv_rows(filt) if os.path.exists(filt) else []

    # Index by symbol -> latest row (if dupes exist, take last)
    def index_by_symbol(rows):
        idx = {}
        for r in rows:
            sym = r.get("symbol") or r.get("Symbol") or ""
            idx[sym] = r
        return idx

    canon_idx = index_by_symbol(rows_canon)
    filt_idx  = index_by_symbol(rows_filt) if rows_filt else {}

    focus_syms = set(args.symbols or canon_idx.keys())

    print("\n=== CHECK 1: Rows that look earnings-like & deserving boost but score<3 ===")
    flagged = []
    for sym in focus_syms:
        r = canon_idx.get(sym)
        if not r: 
            continue
        title = r.get("title") or r.get("headline", "")
        base  = as_float(r.get("base"), 0)
        score = as_float(r.get("score"), base)
        earn  = is_earnings_like(title)
        needs_boost, why = wants_boost(title, args.pct_threshold)
        if earn and needs_boost and (score is None or score < 3):
            flagged.append({
                "symbol": sym,
                "base": base,
                "score": score,
                "why": why,
                "title": title
            })
    if not flagged:
        print("[OK] No obvious under-scored headlines in canonical CSV.")
    else:
        print(f"[BUG?] {len(flagged)} headline(s) appear under-scored (should be 3). Examples:")
        for item in flagged[:12]:
            print(f"  - {item['symbol']}: base={item['base']} score={item['score']} why={item['why']} | {item['title']}")
        issues.append("canonical_under_scored")

    print("\n=== CHECK 2: Did filtered CSV drop/alter the score? ===")
    dropped = []
    for sym in focus_syms:
        c = canon_idx.get(sym); f = filt_idx.get(sym)
        if not c or not f: 
            continue
        cs = as_float(c.get("score"), as_float(c.get("base"), None))
        fs = as_float(f.get("score"), as_float(f.get("base"), None))
        if cs is not None and fs is not None and fs != cs:
            dropped.append((sym, cs, fs, (f.get("title") or "")[:100]))
    if not rows_filt:
        print("[WARN] Filtered CSV missing; skipping this check.")
    elif not dropped:
        print("[OK] Filtered CSV preserves the `score` values.")
    else:
        print("[BUG?] Filtered CSV changed `score` for some rows:")
        for sym, cs, fs, t in dropped[:12]:
            print(f"  - {sym}: canonical={cs} -> filtered={fs} | {t}")
        issues.append("filtered_changed_score")

    print("\n=== CHECK 3: Does run_day_catalyst.py read the `score` column? ===")
    runday_path = os.path.join(root, "scripts", "run_day_catalyst.py")
    hits = grep_file_for(runday_path, [r"news-min-score", r"\bscore\b", r"require-news"])
    if not os.path.exists(runday_path):
        print(f"[WARN] {runday_path} not found.")
    else:
        for pat, lines in hits.items():
            for (lineno, line) in lines[:6]:
                print(f"[HIT run_day_catalyst.py:{lineno}] {line}")
        if not hits.get(r"\bscore\b"):
            print("[BUG?] Could not find references to `score` in run_day_catalyst.py; it may be reading the wrong column.")
            issues.append("runday_no_score_ref")

    print("\n=== CHECK 4: Does catalyst_filter.py preserve `score`? ===")
    filt_path = os.path.join(root, "scripts", "catalyst_filter.py")
    hits_f = grep_file_for(filt_path, [r"\bscore\b", r"DictWriter", r"fieldnames", r"writerow", r"to_csv", r"read_csv"])
    if not os.path.exists(filt_path):
        print(f"[WARN] {filt_path} not found.")
    else:
        for pat, lines in hits_f.items():
            for (lineno, line) in lines[:6]:
                print(f"[HIT catalyst_filter.py:{lineno}] {line}")
        # Heuristic: if no `score` mention, likely it's being dropped
        if not hits_f.get(r"\bscore\b"):
            print("[BUG?] `score` not referenced in catalyst_filter.py; it may be dropped when writing *_filtered.csv.")
            issues.append("filter_drops_score")

    # Optional: show a tiny summary JSON so you can paste results into chat
    summary = {
        "date": args.date,
        "root": root,
        "issues": issues,
        "flagged_examples": flagged[:8],
        "files": {
            "canonical": canon,
            "filtered": filt,
            "run_day_catalyst.py": runday_path,
            "catalyst_filter.py": filt_path,
            "universe_hybrid": uni,
        }
    }
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if issues:
        print("\n[RESULT] ❌ Potential bugs detected. See sections above.")
        return 1
    else:
        print("\n[RESULT] ✅ No obvious scoring issues detected.")
        return 0

if __name__ == "__main__":
    sys.exit(main())