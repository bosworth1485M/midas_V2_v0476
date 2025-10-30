# scripts/trim_universe.py
# Trim the active universe file to the first N symbols (preserving order).
# Usage examples:
#   python scripts/trim_universe.py --top 12
#   python scripts/trim_universe.py --top 25 --path data/samples/universe_sample.txt

import argparse
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(description="Trim universe_sample.txt to the first N symbols (preserving order).")
    ap.add_argument("--top", type=int, default=12, help="How many symbols to keep (default: 12)")
    ap.add_argument("--path", default="data/samples/universe_sample.txt",
                    help="Path to the universe file (default: data/samples/universe_sample.txt)")
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        raise SystemExit(f"[ERR] universe file not found: {p}")

    lines = [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    before = len(lines)
    lines = lines[: max(0, args.top)]
    p.write_text("\n".join(lines), encoding="ascii")
    print(f"Universe trimmed from {before} -> {len(lines)} symbols  ->  {p}")

if __name__ == "__main__":
    main()