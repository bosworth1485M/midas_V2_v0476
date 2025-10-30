#!/usr/bin/env python3
import argparse, csv, pathlib, sys

def ffloat(x):
    try:
        return float(x)
    except:
        return 0.0

def read_results(results_csv: pathlib.Path):
    if not results_csv.exists():
        print(f"[ERR] results file not found:\n{results_csv}")
        sys.exit(1)
    rows_raw = list(csv.DictReader(results_csv.open(encoding="utf-8")))
    rows = []
    for r in rows_raw:
        sym = (r.get("symbol") or r.get("Symbol") or "").upper().strip()
        if not sym:
            continue
        outcome = (r.get("outcome") or r.get("Outcome") or "").upper().strip()
        pnl = ffloat(r.get("pnl") or r.get("PnL"))
        rows.append({"symbol": sym, "outcome": outcome, "pnl": pnl})
    return rows

def read_headlines(cat_csv: pathlib.Path):
    heads = {}
    if cat_csv.exists():
        with cat_csv.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sym = (row.get("symbol") or row.get("Symbol") or "").upper().strip()
                if sym and sym not in heads:
                    heads[sym] = (row.get("headline") or row.get("Headline") or "").strip()
    return heads

def main():
    ap = argparse.ArgumentParser(description="Show per-trade results for a given day/scenario.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--scenario", default="B", help="Scenario letter (default: B)")
    args = ap.parse_args()

    root = pathlib.Path(".")
    ymd = args.date.replace("-", "")
    results_csv = root / f"out/{ymd}/{args.scenario}_hybrid/results_{args.date}.csv"
    cat_csv = root / f"data/catalyst/catalyst_news_{args.date}_filtered.csv"
    if not cat_csv.exists():
        # fallback to unfiltered if filtered doesn't exist
        alt = root / f"data/catalyst/catalyst_news_{args.date}.csv"
        if alt.exists():
            cat_csv = alt

    rows = read_results(results_csv)
    heads = read_headlines(cat_csv)

    print(f"\nALL TRADES — {args.date} (scenario {args.scenario})  [worst → best]")
    print(f"{'symbol':7} {'out':3} {'pnl':>10}  headline")
    for r in sorted(rows, key=lambda x: x["pnl"]):
        h = heads.get(r["symbol"], "")
        print(f"{r['symbol']:7} {r['outcome']:<3} {r['pnl']:>10.2f}  {h[:100]}")

    tp = sum(1 for r in rows if r["outcome"] == "TP")
    sl = sum(1 for r in rows if r["outcome"] == "SL")
    used = tp + sl
    pnl_total = sum(r["pnl"] for r in rows)
    wr = (tp / used * 100.0) if used else 0.0

    print("\nSUMMARY")
    print(f"Trades={used}  TP={tp}  SL={sl}  WR={wr:.2f}%  PnL={pnl_total:.2f}")

    losers = [r for r in rows if r["outcome"] == "SL"]
    if losers:
        print("\nLOSERS ONLY (worst → best)")
        for r in sorted(losers, key=lambda x: x["pnl"]):
            print(f"{r['symbol']:7} {r['pnl']:>10.2f}")

if __name__ == "__main__":
    main()