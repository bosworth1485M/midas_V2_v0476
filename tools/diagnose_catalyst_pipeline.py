#!/usr/bin/env python3
"""
diagnose_catalyst_pipeline.py
Pinpoints where catalyst selection fails (env, fetch, scoring, filter, or run_day usage).

Usage:
  python tools/diagnose_catalyst_pipeline.py --date 2025-08-07
  python tools/diagnose_catalyst_pipeline.py --date 2025-08-07 --root .

Exit codes:
  0 = No obvious issues
  1 = Potential bugs detected
  2 = Fatal (missing files, unreadable inputs)
"""

import argparse, csv, json, os, re, sys
from typing import Dict, List, Tuple

# ---------- regexes for heuristic scoring checks ----------
POS_VERBS_RE = re.compile(r"\b(jump|surge|soar|spike|leap|rise|climb|advance)(?:s|ed)?\b", re.I)
PCT_RE       = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")
EARNINGS_RE  = re.compile(r"\b(q[1-4]|quarter|earnings|eps|revenue)\b", re.I)
SEMANTIC_RE  = re.compile(
    r"\b(beat(?:s|en)?|top(?:s|ped)?|above (?:views|estimates|expectations)|"
    r"raise(?:s|d)?\s+guidance|upgrade(?:s|d)?|"
    r"fda (?:approv(?:es|ed)|clear(?:s|ed))|record|all[-\s]?time high)\b", re.I
)

# ---------- helpers ----------
def read_csv_rows(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def is_file_with_rows(path: str) -> Tuple[bool, int]:
    if not os.path.exists(path):
        return (False, 0)
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            # count rows minus header
            rdr = csv.reader(f)
            count = -1
            for count, _ in enumerate(rdr):
                pass
            nrows = max(0, count)  # header included
        # header-only file yields 0 data rows
        rows = max(0, nrows - 0)  # we report raw line count; details later
        return (True, rows)
    except Exception:
        return (False, 0)

def wants_boost(title: str, pct_threshold: float = 20.0) -> Tuple[bool, str]:
    tl = (title or "").lower()
    if not tl:
        return (False, "")
    if SEMANTIC_RE.search(tl):
        return (True, "semantic")
    mv = POS_VERBS_RE.search(tl)
    mp = PCT_RE.search(tl)
    if mv and mp:
        try:
            if float(mp.group(1)) >= pct_threshold:
                return (True, f"posverb_pct>={pct_threshold}")
        except ValueError:
            pass
    return (False, "")

def grep_file_for(path: str, patterns: List[str]) -> Dict[str, List[Tuple[int, str]]]:
    hits: Dict[str, List[Tuple[int, str]]] = {p: [] for p in patterns}
    if not os.path.exists(path):
        return hits
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f, 1):
            for p in patterns:
                if re.search(p, line, re.I):
                    hits[p].append((i, line.rstrip("\n")))
    return hits

def try_import_requests() -> bool:
    try:
        import requests  # noqa
        return True
    except Exception:
        return False

def as_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default

# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description="Diagnose catalyst pipeline issues (env, fetch, scoring, filter, run_day).")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--root", default=".", help="Project root (default=.)")
    ap.add_argument("--pct-threshold", type=float, default=20.0, help="Boost trigger for 'jumps' (default 20%)")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    ymd  = args.date.replace("-", "")

    # Paths
    canon = os.path.join(root, "data", "catalyst", f"catalyst_news_{args.date}.csv")
    filt  = os.path.join(root, "data", "catalyst", f"catalyst_news_{args.date}_filtered.csv")
    audit = os.path.join(root, "out", ymd, "catalyst", f"catalyst_news_{args.date}.csv")
    universe_raw = os.path.join(root, "data", "raw", f"universe_topgappers_{args.date}.txt")

    enrich_py  = os.path.join(root, "scripts", "enrich_universe_catalyst.py")
    filter_py  = os.path.join(root, "scripts", "catalyst_filter.py")
    runday_py  = os.path.join(root, "scripts", "run_day_catalyst.py")

    problems: List[str] = []
    notes:    List[str] = []

    # 1) Environment checks
    print(f"[INFO] root={root}")
    print(f"[INFO] Python={sys.version.split()[0]} exe={sys.executable}")
    req_ok = try_import_requests()
    print(f"[ENV]  requests_import={'OK' if req_ok else 'MISSING'}")

    poly = os.environ.get("POLYGON_API_KEY") or os.environ.get("POLYGON_KEY") or ""
    print(f"[ENV]  POLYGON_KEY={'SET' if bool(poly) else 'NOT_SET'}")

    # 2) File existence checks
    for p in [enrich_py, filter_py, runday_py]:
        print(f"[SRC]  {os.path.relpath(p, root)} exists={os.path.exists(p)}")

    for p in [universe_raw, canon, filt, audit]:
        exists = os.path.exists(p)
        size = os.path.getsize(p) if exists else 0
        print(f"[DATA] {os.path.relpath(p, root)} exists={exists} size={size}")

    # 3) Source scans: does code reference/keep the right columns?
    enrich_hits = grep_file_for(enrich_py, [r"compute_score_and_flags", r"\bscore\b", r"boost_flags", r"DictWriter", r"fieldnames"])
    filt_hits   = grep_file_for(filter_py,   [r"\bscore\b", r"boost_flags", r"DictWriter", r"fieldnames", r"writerow"])
    rd_hits     = grep_file_for(runday_py,   [r"news-min-score", r"\brequire-news\b", r"\bscore\b"])

    def show_hits(label, hits):
        any_hit = False
        for pat, lines in hits.items():
            if lines:
                any_hit = True
                for (ln, txt) in lines[:5]:
                    print(f"[HIT {label}:{ln}] {txt}")
        return any_hit

    print("\n=== CODE CHECK: enrich_universe_catalyst.py ===")
    show_hits("enrich", enrich_hits)

    print("\n=== CODE CHECK: catalyst_filter.py ===")
    show_hits("filter", filt_hits)
    if not filt_hits.get(r"\bscore\b"):
        print("[BUG?] filter script may not preserve `score` (no references found).")
        problems.append("filter_may_drop_score")

    print("\n=== CODE CHECK: run_day_catalyst.py ===")
    show_hits("runday", rd_hits)
    if not rd_hits.get(r"\bscore\b"):
        print("[BUG?] run_day_catalyst.py may not read `score` column.")
        problems.append("runday_may_ignore_score")

    # 4) CSV presence & content
    canon_exists, _ = is_file_with_rows(canon)
    filt_exists,  _ = is_file_with_rows(filt)

    if not canon_exists and os.path.exists(audit):
        print(f"[INFO] canonical missing; audit CSV exists: {audit}")
        notes.append("use_audit_csv_as_source")

    flagged_examples: List[Dict[str, str]] = []
    n_canon = n_canon_ge3 = 0
    if os.path.exists(canon):
        rows = read_csv_rows(canon)
        n_canon = len(rows)
        # count >=3
        for r in rows:
            s = as_float(r.get("score"), None)
            if s is not None and s >= 3:
                n_canon_ge3 += 1
        print(f"\n[SCAN] canonical rows={n_canon}, rows_with_score>=3={n_canon_ge3}")

        # flag likely under-scored rows (earnings + jumps ≥ threshold but score<3)
        for r in rows:
            title = r.get("title") or r.get("headline") or ""
            if not title:
                continue
            if EARNINGS_RE.search(title) and wants_boost(title, args.pct_threshold)[0]:
                s = as_float(r.get("score"), None)
                if s is None or s < 3:
                    flagged_examples.append({
                        "symbol": r.get("symbol",""),
                        "score": str(r.get("score","")),
                        "title": title[:160],
                        "why": wants_boost(title, args.pct_threshold)[1]
                    })
        if flagged_examples:
            print(f"[BUG?] {len(flagged_examples)} canonical row(s) look under-scored (<3) but match earnings+jump≥{args.pct_threshold}%:")
            for ex in flagged_examples[:10]:
                print(f"  - {ex['symbol']:6} score={ex['score']!s:>3} why={ex['why']:<18} | {ex['title']}")

    else:
        print("\n[WARN] canonical CSV missing or empty for this date.")
        problems.append("canonical_missing")

    # filtered CSV preservation check (score squashed?)
    if os.path.exists(canon) and os.path.exists(filt):
        crows = { r.get("symbol",""): r for r in read_csv_rows(canon) }
        frows = { r.get("symbol",""): r for r in read_csv_rows(filt) }
        changed = []
        for sym, cr in crows.items():
            fr = frows.get(sym)
            if not fr:
                continue
            cs = as_float(cr.get("score"), None)
            fs = as_float(fr.get("score"), None)
            if cs is not None and fs is not None and cs != fs:
                changed.append((sym, cs, fs))
        if changed:
            print("[BUG?] filtered CSV changed `score` values vs canonical:")
            for sym, cs, fs in changed[:12]:
                print(f"  - {sym}: {cs} -> {fs}")
            problems.append("filtered_changed_score")
        else:
            print("[OK]   filtered CSV preserves `score` values from canonical.")
    else:
        print("[WARN] filtered CSV missing; skipping preservation check.")

    # 5) Environment-level root cause hints
    if n_canon == 0 or n_canon_ge3 == 0:
        # if requests missing AND no polygon key -> fetch layer likely the cause of zeros
        if not try_import_requests():
            problems.append("requests_missing")
            print("[CAUSE] `requests` not importable (fetch inside enrich will return 0 headlines).")
        if not poly:
            problems.append("polygon_key_missing")
            print("[CAUSE] POLYGON_API_KEY/POLYGON_KEY not set (fetch will return 0).")
        # also: if enrich.py does NOT contain compute_score_and_flags or `score` write, scoring will be wrong
        if not enrich_hits.get(r"compute_score_and_flags"):
            print("[CAUSE] scoring helper not found in enrich file (scores may remain base-only).")
            problems.append("enrich_scoring_helper_missing")

    # 6) Summarize
    summary = {
        "date": args.date,
        "root": root,
        "env": {
            "python": sys.version.split()[0],
            "requests_import": req_ok,
            "polygon_key_set": bool(poly),
        },
        "files": {
            "enrich_py": os.path.relpath(enrich_py, root),
            "filter_py": os.path.relpath(filter_py, root),
            "runday_py": os.path.relpath(runday_py, root),
            "canonical_csv": os.path.relpath(canon, root),
            "filtered_csv": os.path.relpath(filt, root),
            "audit_csv": os.path.relpath(audit, root),
            "universe_raw": os.path.relpath(universe_raw, root),
        },
        "canonical": {
            "rows": n_canon,
            "rows_score_ge_3": n_canon_ge3,
            "flagged_under_scored": flagged_examples[:20],
        },
        "issues": problems,
        "notes": notes,
    }

    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if problems:
        print("\n[RESULT] ❌ Potential bugs detected.")
        return 1
    print("\n[RESULT] ✅ No obvious issues detected.")
    return 0

if __name__ == "__main__":
    sys.exit(main())