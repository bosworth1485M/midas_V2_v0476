# scripts/build_filtered_universe.py
import argparse, pathlib, re

def parse_table_lines(lines):
    rows = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("Open-gap") or s.startswith("SYMBOL") or s.startswith("Wrote"):
            continue
        parts = s.split()
        if len(parts) < 3:
            continue
        sym = parts[0].strip()
        # price should be last column; gap% is the second column (like 13.21 or 13.21%)
        price_txt = parts[-1].strip().rstrip("%")
        gap_txt = parts[1].strip().rstrip("%")
        try:
            price = float(price_txt)
            gap = float(gap_txt)
        except ValueError:
            continue
        rows.append((sym, gap, price))
    return rows

def main():
    ap = argparse.ArgumentParser(description="Filter topgappers table into a clean universe file")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--min-gap", type=float, default=8.0)
    ap.add_argument("--min-price", type=float, default=1.0)
    ap.add_argument("--max-price", type=float, default=10.0)
    ap.add_argument("--exclude-dot", action="store_true", help="Exclude symbols containing a dot (warrants/preferreds)")
    ap.add_argument("--limit", type=int, default=40, help="Keep at most N symbols after filtering (in table order)")
    args = ap.parse_args()

    # This is where topgappers.py wrote the printed table earlier
    table_path = pathlib.Path("data/samples/universe_sample.txt")
    if not table_path.exists():
        raise SystemExit(f"Table not found: {table_path}")

    lines = table_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    rows = parse_table_lines(lines)

    keep = []
    for sym, gap, price in rows:
        if args.exclude_dot and "." in sym:
            continue
        if gap < args.min_gap:
            continue
        if not (args.min_price <= price <= args.max_price):
            continue
        keep.append(sym)

    # Keep original table order and trim to limit
    keep = keep[: args.limit]

    out_path = pathlib.Path("data") / f"universe_topgappers_{args.date}_filtered.txt"
    out_path.write_text("\n".join(keep), encoding="utf-8")
    print(f"[UNIVERSE] Filtered {len(keep)}/{len(rows)} -> {out_path}")

if __name__ == "__main__":
    main()