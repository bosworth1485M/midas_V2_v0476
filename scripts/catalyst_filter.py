#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
catalyst_filter.py
Reads the canonical catalyst CSV and writes a filtered CSV, *preserving* the `score` column.
Options:
  --deny-negative (drop rows with clearly bearish language)
  --exclude-china (drop rows for symbols in a provided China list file)
"""

import os
import re
import csv
import argparse
from typing import Set

NEG_TERMS_DEFAULT = [
    r"\bfalls?\b", r"\bdeclines?\b", r"\bdrops?\b", r"\bplunges?\b", r"\btumbles?\b",
    r"\bmiss(?:es|ed)?\b", r"\bbelow (?:views|estimates|expectations)\b",
    r"\bcut(?:s|ting)?\s+guidance\b", r"\bdowngrade(?:s|d)?\b",
]
NEG_RE = re.compile("|".join(NEG_TERMS_DEFAULT), re.I)

def load_symbol_set(path: str) -> Set[str]:
    s: Set[str] = set()
    if not path or not os.path.exists(path):
        return s
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            t = line.strip()
            if t and not t.startswith("#"):
                s.add(t.split()[0])
    return s

def main() -> int:
    ap = argparse.ArgumentParser(description="Filter canonical catalyst CSV; preserve `score` column verbatim.")
    ap.add_argument("--in", dest="in_path", required=True)
    ap.add_argument("--out", dest="out_path", required=True)
    ap.add_argument("--deny-negative", action="store_true")
    ap.add_argument("--exclude-china", action="store_true")
    ap.add_argument("--neg-terms-file", default=None)
    ap.add_argument("--china-list-file", default=None)
    args = ap.parse_args()

    # Load negatives override if provided
    neg_re = NEG_RE
    if args.neg_terms_file and os.path.exists(args.neg_terms_file):
        try:
            terms = []
            with open(args.neg_terms_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    t = line.strip()
                    if t and not t.startswith("#"):
                        terms.append(t)
            if terms:
                neg_re = re.compile("|".join(terms), re.I)
        except Exception:
            pass

    china_set = load_symbol_set(args.china_list_file) if args.exclude_china else set()

    if not os.path.exists(args.in_path):
        print(f"[ERROR] input not found: {args.in_path}")
        return 2

    os.makedirs(os.path.dirname(os.path.abspath(args.out_path)), exist_ok=True)

    kept = 0
    dropped = 0

    with open(args.in_path, "r", encoding="utf-8", newline="") as fin, \
         open(args.out_path, "w", encoding="utf-8", newline="") as fout:
        rdr = csv.DictReader(fin)
        fieldnames = list(rdr.fieldnames or [])
        # Ensure `score` (and diagnostics if present) remain in output
        for extra in ["score", "base", "boost_flags", "source", "published_utc"]:
            if extra not in fieldnames:
                fieldnames.append(extra)
        w = csv.DictWriter(fout, fieldnames=fieldnames)
        w.writeheader()

        for row in rdr:
            sym = row.get("symbol", "").strip()
            title = (row.get("title") or row.get("headline") or "").strip()

            # exclude China list
            if args.exclude_china and sym in china_set:
                dropped += 1
                continue

            # deny-negative drops
            if args.deny_negative and title and neg_re.search(title):
                print(f"[DROP-NEG] {sym} headline='{title}'")
                dropped += 1
                continue

            # DO NOT recompute score. Preserve whatever canonical had.
            w.writerow(row)
            kept += 1

    print(f"[FILTER] {os.path.basename(args.in_path)} -> {os.path.basename(args.out_path)} kept={kept} dropped={dropped}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())