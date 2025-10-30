#!/usr/bin/env python3
# Drop tickers whose catalyst audit headlines match a negative regex.

import argparse, re, csv
from pathlib import Path

DEF_BAN = r"(reverse split|offering|ATM|shelf|going private|delist|compliance)"

def read_list(p: Path):
    return [ln.strip().upper() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()] if p.exists() else []

def main():
    ap = argparse.ArgumentParser(description="Filter universe by negative headline patterns.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--in", dest="inp", required=True, help="Input universe TXT")
    ap.add_argument("--audit", default=None, help="Catalyst audit CSV (default out\\YYYYMMDD\\catalyst\\catalyst_news_YYYY-MM-DD.csv)")
    ap.add_argument("--out", required=True, help="Output universe TXT (filtered)")
    ap.add_argument("--ban", default=DEF_BAN, help="Case-insensitive regex of negative terms")
    args = ap.parse_args()

    d = args.date
    audit = Path(args.audit) if args.audit else Path("out") / d.replace("-", "") / "catalyst" / f"catalyst_news_{d}.csv"
    U = read_list(Path(args.inp))
    if not U:
        Path(args.out).write_text("", encoding="utf-8"); print("[FILTER] empty universe; wrote 0"); return

    bad = set()
    if audit.exists():
        with audit.open(newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            cols = {c.lower(): c for c in r.fieldnames}
            tcol = cols.get("ticker") or cols.get("symbol") or list(r.fieldnames)[0]
            hcol = cols.get("headline") or cols.get("title")
            if not hcol:
                for c in r.fieldnames:
                    if "head" in c.lower() or "title" in c.lower(): hcol = c; break
            rx = re.compile(args.ban, re.I)
            for row in r:
                t = (row.get(tcol) or "").strip().upper()
                h = (row.get(hcol) or "")
                if t and h and rx.search(h):
                    bad.add(t)
    else:
        print(f"[FILTER] audit not found: {audit} (skipping headline filter)")

    kept = [t for t in U if t not in bad]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    print(f"[FILTER] ban={args.ban}  in={len(U)}  drop={len(bad & set(U))}  out={len(kept)}")
    if bad:
        print("[FILTER] dropped:", ", ".join(sorted(bad & set(U))[:30]))

if __name__ == "__main__":
    main()