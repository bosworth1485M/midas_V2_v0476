#!/usr/bin/env python3
# scripts/print_catalyst_decisions.py
# Print per-symbol KEEP/DROP with grades, scores, and headlines for a given date.

import argparse
import csv
from pathlib import Path

def trunc(s: str, n: int = 110) -> str:
    s = (s or "").strip()
    return (s[: n - 1] + "…") if len(s) > n else s

def load_scores(scores_csv: Path):
    rows = []
    with scores_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "symbol": r.get("symbol") or r.get("ticker") or "",
                "grade": (r.get("grade") or "").strip(),
                "score": r.get("score") or r.get("best_score") or "",
                "headline": r.get("best_headline") or ""
            })
    return rows

def load_kept(kept_txt: Path):
    if not kept_txt.exists():
        return []
    return [line.strip() for line in kept_txt.read_text(encoding="utf-8").splitlines() if line.strip()]

def main():
    ap = argparse.ArgumentParser(description="Print catalyst KEEP/DROP decisions for a given date.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--head", type=int, default=15, help="Max items to display for each list (default 15)")
    args = ap.parse_args()

    ymd_compact = args.date.replace("-", "")
    scores_csv = Path(f"out/{ymd_compact}/catalyst/catalyst_scores_{args.date}.csv")
    kept_txt   = Path(f"data/universe_catalyst_{args.date}.txt")

    if not scores_csv.exists():
        raise SystemExit(f"[ERR] Not found: {scores_csv}")

    rows = load_scores(scores_csv)
    all_syms = [r["symbol"] for r in rows if r["symbol"]]
    meta = {r["symbol"]: r for r in rows}

    kept = load_kept(kept_txt)
    kept_set = set(kept)
    dropped = [s for s in all_syms if s not in kept_set]

    print(f"[PICKER] kept={len(kept)} dropped={len(dropped)}  (from {len(all_syms)} candidates)")
    # Print KEEP lines
    for s in kept[: args.head]:
        m = meta.get(s, {})
        print(f"[KEEP] {s:<6}  grade={m.get('grade','?')}  score={m.get('score','?')}  headline={trunc(m.get('headline') or 'NO HEADLINE')}")
    if len(kept) > args.head:
        print(f"[KEEP] ...(and {len(kept) - args.head} more)")

    # Print DROP lines
    for s in dropped[: args.head]:
        m = meta.get(s, {})
        headline = m.get('headline') or "NO NEWS"
        print(f"[DROP] {s:<6}  grade={m.get('grade','?')}  score={m.get('score','?')}  headline={trunc(headline)}")
    if len(dropped) > args.head:
        print(f"[DROP] ...(and {len(dropped) - args.head} more)")

if __name__ == "__main__":
    main()
