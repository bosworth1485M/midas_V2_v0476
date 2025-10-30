#!/usr/bin/env python3
# scripts/print_catalyst_decisions_plus.py
# Shows KEEP/DROP decisions with headlines:
# - [POS] = qualifying positive headline from scores CSV (best_headline)
# - [RAW] = fallback raw headline from news CSV if POS missing
import argparse, csv
from pathlib import Path

def trunc(s, n=110):
    s = (s or "").strip()
    return (s[: n - 1] + "…") if len(s) > n else s

def load_scores(scores_csv: Path):
    pos = {}  # symbol -> positive headline (if any) + score/grade
    order = []  # preserve symbol order as seen
    with scores_csv.open("r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            sym = (r.get("symbol") or r.get("ticker") or "").strip()
            if not sym:
                continue
            if sym not in pos:
                order.append(sym)
            pos[sym] = {
                "grade": r.get("grade") or "",
                "score": r.get("score") or r.get("best_score") or "",
                "pos_headline": (r.get("best_headline") or "").strip(),
            }
    return pos, order

def load_news(news_csv: Path):
    raw = {}  # symbol -> best raw headline
    if news_csv.exists():
        with news_csv.open("r", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                sym = (r.get("ticker") or r.get("symbol") or "").strip()
                if not sym:
                    continue
                h = (r.get("best_headline") or "").strip()
                if h and sym not in raw:
                    raw[sym] = h
    return raw

def load_kept(kept_txt: Path):
    return [s.strip() for s in kept_txt.read_text(encoding="utf-8").splitlines() if s.strip()] if kept_txt.exists() else []

def main():
    ap = argparse.ArgumentParser(description="Print catalyst KEEP/DROP with [POS]/[RAW] headlines.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--head", type=int, default=20, help="Max lines to display for each list (default 20)")
    args = ap.parse_args()

    ymd = args.date
    ymdc = ymd.replace("-", "")
    scores_csv = Path(f"out/{ymdc}/catalyst/catalyst_scores_{ymd}.csv")
    news_csv   = Path(f"out/{ymdc}/catalyst/catalyst_news_{ymd}.csv")
    kept_txt   = Path(f"data/universe_catalyst_{ymd}.txt")

    pos, order = load_scores(scores_csv)
    raw = load_news(news_csv)
    kept = load_kept(kept_txt)
    kept_set = set(kept)
    all_syms = order or list(pos.keys()) or list(raw.keys())
    dropped = [s for s in all_syms if s not in kept_set]

    print(f"[PICKER] kept={len(kept)} dropped={len(dropped)}  (from {len(all_syms)} candidates)")

    def line(sym):
        g = (pos.get(sym, {}).get("grade") or "").strip() or "?"
        sc = (pos.get(sym, {}).get("score") or "").strip() or "?"
        ph = (pos.get(sym, {}).get("pos_headline") or "").strip()
        if ph:
            return f"grade={g}  score={sc}  [POS] {trunc(ph)}"
        rh = raw.get(sym)
        if rh:
            return f"grade={g}  score={sc}  [RAW] {trunc(rh)}"
        return f"grade={g}  score={sc}  [RAW] NO NEWS"

    for s in kept[: args.head]:
        print(f"[KEEP] {s:<6}  {line(s)}")
    if len(kept) > args.head:
        print(f"[KEEP] ...(and {len(kept)-args.head} more)")

    for s in dropped[: args.head]:
        print(f"[DROP] {s:<6}  {line(s)}")
    if len(dropped) > args.head:
        print(f"[DROP] ...(and {len(dropped)-args.head} more)")

if __name__ == "__main__":
    main()
