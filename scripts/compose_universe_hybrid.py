#!/usr/bin/env python3
# Compose HYBRID universe = Allowlist ∪ Top-N(raw) ∪ Catalyst-only (score>=2).

import argparse
from pathlib import Path

def read_list(p: Path):
    if not p or not p.exists(): return []
    return [ln.strip().upper() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]

def dedupe_preserve(seq):
    seen = set(); out = []
    for x in seq:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

def main():
    ap = argparse.ArgumentParser(description="Compose HYBRID universe from allowlist, raw, and catalyst lists.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (informational)")
    ap.add_argument("--raw", required=True, help="Raw top-gappers TXT (ordered)")
    ap.add_argument("--catalyst", required=True, help="Catalyst-only TXT (score>=2)")
    ap.add_argument("--allowlist", default=None, help="Allowlist TXT (Tier-A >=50% or manual)")
    ap.add_argument("--top", type=int, default=12, help="Top-N from raw (default 12)")
    ap.add_argument("--out", required=True, help="Output universe TXT")
    args = ap.parse_args()

    raw = read_list(Path(args.raw))[:max(0, args.top)]
    cat = read_list(Path(args.catalyst))
    allow = read_list(Path(args.allowlist)) if args.allowlist else []

    combined = dedupe_preserve(allow + raw + cat)
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text("\n".join(combined) + ("\n" if combined else ""), encoding="utf-8")

    print(f"[HYBRID] date={args.date} top={args.top} -> allow={len(allow)} rawTop={len(raw)} catalyst={len(cat)} final={len(combined)}")
    if combined:
        print("[HYBRID] HEAD:", ", ".join(combined[:min(len(combined), 20)]))

if __name__ == "__main__":
    main()