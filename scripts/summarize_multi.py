# scripts/summarize_multi.py
import argparse, csv, pathlib

def summarize(csv_path: pathlib.Path):
    t=w=l=0; pnl=0.0
    if csv_path.exists():
        with csv_path.open(newline="") as f:
            r=csv.DictReader(f)
            for row in r:
                t += 1
                pnl += float(row["pnl"])
                o = row.get("outcome","")
                if o == "TP": w += 1
                elif o == "SL": l += 1
    return t,w,l,pnl

def main():
    ap = argparse.ArgumentParser(description="Summarize PnL across multiple dates")
    ap.add_argument("--dates", required=True, help="Comma-separated YYYY-MM-DD list")
    ap.add_argument("--scenario", default="B", help="Scenario key (default B)")
    ap.add_argument("--out-root", default="out/auto", help="Results root (default out/auto)")
    args = ap.parse_args()

    dates = [d.strip() for d in args.dates.split(",") if d.strip()]
    T=W=L=0; total=0.0; pos=neg=flat=0

    for d in dates:
        p = pathlib.Path(args.out_root) / d.replace("-","") / args.scenario / f"results_{d}.csv"
        t,w,l,pnl = summarize(p)
        print(f"{d}: trades={t}, wins={w}, losses={l}, pnl={pnl:.2f}")
        T+=t; W+=w; L+=l; total+=pnl
        if pnl>0: pos+=1
        elif pnl<0: neg+=1
        else: flat+=1

    wr = 0.0 if T==0 else 100*W/T
    print(f"TOTAL: trades={T}, wins={W}, losses={L}, winrate={wr:.2f}%, totalPnL={total:.2f}")
    print(f"Days: positive={pos}, negative={neg}, flat={flat}")

if __name__ == "__main__":
    main()