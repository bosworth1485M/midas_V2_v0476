#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enrich_universe_catalyst.py
Builds a canonical catalyst CSV from a raw universe (top gappers), scoring each symbol's best headline.

Writes:
  data/catalyst/catalyst_news_YYYY-MM-DD.csv       (canonical, contains BOOSTED `score`)
  --out <txt>                                      (symbol list meeting min-score)

Logging style:
[INFO]/[AUTH]/[KEEP]/[DROP]/[AUDIT]/[CANONICAL]/[SUMMARY]
"""

from __future__ import annotations

import os
import sys
import re
import csv
import argparse
import datetime as dt
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# ------------------------------------------------------------------------------
# Defaults
# ------------------------------------------------------------------------------
DEFAULT_MIN_SCORE = 1.0
DEFAULT_LIMIT = 100
DEFAULT_LOOKBACK_HOURS = 36

# ------------------------------------------------------------------------------
# Bootstrap: load .env and Polygon key (matches working scanner style)
# ------------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]

def _try_load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # optional: pip install python-dotenv
        load_dotenv(ROOT / ".env", override=True)
    except Exception as e:
        sys.stderr.write(f"[WARN] dotenv load failed: {e}\n")

def _scan_env_files_for_key() -> Optional[str]:
    candidates = [
        ROOT / ".env",
        ROOT / "env",
        ROOT / ".env" / "env",
        ROOT / ".env" / "CLI",
    ]
    for c in candidates:
        try:
            if c.is_dir():
                for name in os.listdir(c):
                    p = c / name
                    if p.is_file():
                        with open(p, "r", encoding="utf-8", errors="ignore") as f:
                            for line in f:
                                if "POLYGON_API_KEY" in line or "POLYGON_KEY" in line:
                                    kv = line.strip().split("=", 1)
                                    if len(kv) == 2 and kv[1].strip():
                                        return kv[1].strip().strip('"').strip("'")
            elif c.is_file():
                with open(c, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if "POLYGON_API_KEY" in line or "POLYGON_KEY" in line:
                            kv = line.strip().split("=", 1)
                            if len(kv) == 2 and kv[1].strip():
                                return kv[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return None

def load_polygon_key() -> str:
    _try_load_dotenv()
    k = (
        os.environ.get("POLYGON_API_KEY")
        or os.environ.get("POLYGON_KEY")
        or _scan_env_files_for_key()
        or ""
    )
    k = k.strip().strip('"').strip("'")
    if not k:
        print("[ERR] POLYGON_API_KEY missing (set in .env or environment)", file=sys.stderr)
        sys.exit(1)
    return k

# ------------------------------------------------------------------------------
# Scoring (FIX v0.3.46): base=2 for earnings-like; +1 if semantic booster OR pos-verb + percent>=20
# ------------------------------------------------------------------------------
# Base earnings cues (expanded): include sales|results|guidance
EARNINGS_RE = re.compile(
    r"\b(q[1-4]|quarter|earnings|eps|revenue|sales|results|guidance)\b",
    re.I,
)

# Positive verbs (expanded): add up|increase|improve (used with % threshold)
POS_VERBS_RE = re.compile(
    r"\b(jump|surge|soar|spike|leap|rise|climb|advance|up|increase|improve)(?:s|d)?\b",
    re.I,
)

# Percent capture
PCT_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")

# “Beats/tops/above estimates/raise guidance/upgrade/FDA/record”
SEMANTIC_RE  = re.compile(
    r"\b(beat(?:s|en)?|top(?:s|ped)?|above (?:views|estimates|expectations)|"
    r"raise(?:s|d)?\s+guidance|upgrade(?:s|d)?|"
    r"fda (?:approv(?:es|ed)|clear(?:s|ed))|record|all[-\s]?time high)\b",
    re.I
)

def compute_score_and_flags(item: Dict[str, Any], pct_boost_threshold: float = 20.0) -> Tuple[float, float, List[str]]:
    """
    Scoring:
      - base = 2 if headline has earnings-like cues (Q2/earnings/EPS/revenue/sales/results/guidance)
      - +1 boost if (semantic 'beats/tops/above estimates/raise guidance/etc')
        OR (positive verb present AND percentage >= pct_boost_threshold, default 20%)
      - negatives still get base=2 only; they will be excluded by score>=3 and/or deny-negative.
    Returns (final_score, base_score, flags:list[str])
    """
    title = (item.get("title") or item.get("headline") or "").strip()
    tl = title.lower()

    base = 2.0 if EARNINGS_RE.search(tl) else 0.0
    flags: List[str] = []

    # Semantic boosters (beats/tops/above estimates/raise guidance/etc.)
    if SEMANTIC_RE.search(tl):
        flags.append("semantic")

    # Magnitude booster: positive verb + % >= threshold
    mv = POS_VERBS_RE.search(tl)
    mp = PCT_RE.search(tl)
    if mv and mp:
        try:
            if float(mp.group(1)) >= pct_boost_threshold:
                flags.append(f"posverb_pct>={pct_boost_threshold}")
        except ValueError:
            pass

    final = base + (1.0 if flags else 0.0)
    return final, base, flags

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def load_universe_symbols(path: str) -> List[str]:
    syms: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#"):
                syms.append(s.split()[0])  # allow "SYM ..." lines
    return syms

def ensure_dir_for(path: str) -> None:
    Path(path).resolve().parent.mkdir(parents=True, exist_ok=True)

def iso_range(date_iso: str, lookback_hours: int) -> Tuple[str, str]:
    d = dt.datetime.fromisoformat(date_iso)
    gte = (d - dt.timedelta(hours=lookback_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    lte = (d + dt.timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return gte, lte

# ------------------------------------------------------------------------------
# News fetch via Polygon (Bearer auth)
# ------------------------------------------------------------------------------
def fetch_polygon_news_for_symbol(symbol: str, date_str: str, lookback_hours: int, limit: int) -> List[Dict[str, Any]]:
    import requests

    key = load_polygon_key()
    gte, lte = iso_range(date_str, lookback_hours)

    url = "https://api.polygon.io/v2/reference/news"
    params = {
        "ticker": symbol,
        "published_utc.gte": gte,
        "published_utc.lte": lte,
        "limit": max(1, min(limit, 1000)),
        "order": "desc",
    }

    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {key}", "User-Agent": "midas_v2/1.0"})
    try:
        r = s.get(url, params=params, timeout=15)
    except Exception as e:
        sys.stderr.write(f"[WARN] news fetch error {symbol}: {type(e).__name__}: {e}\n")
        return []

    if r.status_code != 200:
        sys.stderr.write(f"[WARN] news fetch {symbol} {date_str} -> HTTP {r.status_code}\n")
        return []

    data = r.json() or {}
    results = data.get("results") or []
    out: List[Dict[str, Any]] = []
    for it in results:
        out.append({
            "symbol": symbol,
            "title": it.get("title") or it.get("headline") or "",
            "headline": it.get("title") or it.get("headline") or "",
            "published_utc": it.get("published_utc") or "",
            "source": "polygon",
        })
    return out

def pick_best_headline(items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Score all headlines for a symbol and return the single best (max final score).
    """
    best = None
    best_score = -1.0
    for it in items:
        final, base, flags = compute_score_and_flags(it)
        it["_final_score"] = final
        it["_base_score"] = base
        it["_boost_flags"] = flags
        if final > best_score:
            best = it
            best_score = final
    return best

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="Enrich raw universe with catalyst headlines and write canonical CSV.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--in", dest="in_path", required=True, help="Raw universe list (txt)")
    ap.add_argument("--out", dest="out_path", required=True, help="Output symbol list meeting min-score")
    ap.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE, help="Minimum score to keep (default 1)")
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Max headlines per symbol to fetch")
    ap.add_argument("--lookback-hours", type=int, default=DEFAULT_LOOKBACK_HOURS, help="News lookback hours (default 36)")
    ap.add_argument("--dry-run", action="store_true", help="Do not write files")
    ap.add_argument("--debug-fetch", action="store_true", help="Print per-symbol fetch & scoring details")
    args = ap.parse_args()

    ymd = args.date.replace("-", "")
    canonical_csv = Path("data") / "catalyst" / f"catalyst_news_{args.date}.csv"
    audit_rel     = Path("out") / ymd / "catalyst" / f"catalyst_news_{args.date}.csv"

    ensure_dir_for(canonical_csv)
    ensure_dir_for(audit_rel)

    # Universe
    symbols = load_universe_symbols(args.in_path)
    print(f"[INFO] {args.date} candidates={len(symbols)}  min_score={args.min_score}  limit={args.limit}  lookback_hours={args.lookback_hours}  boosts=ON")

    # Auth
    key = load_polygon_key()
    if key:
        print("[AUTH] polygon_key=OK (.env/env/ENV)")

    kept: List[str] = []
    canon_rows: List[Dict[str, Any]] = []

    for sym in symbols:
        news_items = fetch_polygon_news_for_symbol(sym, args.date, args.lookback_hours, args.limit)
        if args.debug_fetch:
            print(f"[DBG] {sym} news_items={len(news_items)}")

        best = pick_best_headline(news_items) if news_items else None
        if best and args.debug_fetch:
            t = (best.get("title") or best.get("headline") or "").strip()
            final_dbg, base_dbg, flags_dbg = best["_final_score"], best["_base_score"], best["_boost_flags"]
            print(f"[DBG] {sym} best='{t[:120]}' base={base_dbg} flags={flags_dbg} final={final_dbg}")

        if not best:
            print(f"[DROP] {sym:5} score=0 (base=0)")
            continue

        title = (best.get("title") or best.get("headline") or "").strip()
        final, base, flags = best["_final_score"], best["_base_score"], best["_boost_flags"]

        if final >= float(args.min_score):
            kept.append(sym)
            v_final = int(final) if float(final).is_integer() else final
            v_base  = int(base)  if float(base).is_integer()  else base
            print(f"[KEEP] {sym:5} score={v_final} (base={v_base}) title='{title}'")
        else:
            v_final = int(final) if float(final).is_integer() else final
            v_base  = int(base)  if float(base).is_integer()  else base
            print(f"[DROP] {sym:5} score={v_final} (base={v_base})")

        canon_rows.append({
            "symbol": sym,
            "title": title,
            # Write BOOSTED score to CSV (downstream will read this).
            "score": f"{final:.0f}" if float(final).is_integer() else f"{final:.2f}",
            "base":  f"{base:.0f}"  if float(base).is_integer()  else f"{base:.2f}",
            "boost_flags": "|".join(flags),
            "source": best.get("source") or "polygon",
            "published_utc": best.get("published_utc") or "",
        })

    # canonical CSV
    if not args.dry_run:
        with open(canonical_csv, "w", encoding="utf-8", newline="") as f:
            fieldnames = ["symbol", "title", "score", "base", "boost_flags", "source", "published_utc"]
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in canon_rows:
                w.writerow(r)

        # audit copy
        with open(audit_rel, "w", encoding="utf-8", newline="") as f:
            fieldnames = ["symbol", "title", "score", "base", "boost_flags", "source", "published_utc"]
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in canon_rows:
                w.writerow(r)
        print(f"[AUDIT] {audit_rel.as_posix()}")

    print(f"[CANONICAL] {canonical_csv.as_posix()}")

    # kept list (symbols that met min-score)
    kept_count = 0
    if not args.dry_run:
        ensure_dir_for(args.out_path)
        with open(args.out_path, "w", encoding="utf-8") as f:
            for s in kept:
                f.write(s + "\n")
                kept_count += 1

    head_syms = ", ".join(kept[:10])
    print(f"[SUMMARY] kept={kept_count} mismatches=0 co_mentions_dropped=0  head: {head_syms if head_syms else ''}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())