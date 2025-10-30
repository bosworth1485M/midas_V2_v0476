# Step 1: create STTK-only universe, run Scenario B, print a short report
import os, sys, subprocess, pandas as pd
from pathlib import Path

# (a) Tiny universe
u = Path("data/samples/universe_sample.txt")
u.parent.mkdir(parents=True, exist_ok=True)
u.write_text("STTK\n")
print(f"[OK] Wrote {u} with STTK")

# (b) Run Scenario B baseline
date = "2025-08-05"
outdir = os.path.join("out", date.replace("-",""), "B")
cmd = [sys.executable, "-m", "midas_v2.cli", "backtest",
       "--date", date, "--scenario", "B",
       "--universe", str(u),
       "--out", outdir]
print("[RUN]", " ".join(cmd))
ret = subprocess.call(cmd)
print(f"[EXIT] backtest -> {ret}")

# (c) Report
csv_path = os.path.join(outdir, f"results_{date}.csv")
print("[CHECK]", csv_path)
if not os.path.exists(csv_path):
    print("[WARN] Results CSV not found. Check logs above.")
    raise SystemExit(0)

df = pd.read_csv(csv_path)
if df.empty:
    print("[INFO] Results CSV is empty (no trades).")
else:
    # Basic summary
    wr = (df["outcome"].eq("TP").mean()*100.0)
    total_pnl = df["pnl"].sum()
    print(df.head(12).to_string(index=False))
    print("\n[SUMMARY] Win rate: %.1f%% | Total PnL: %.2f" % (wr, total_pnl))
    print("\n[BREAKDOWN]\n", df.groupby("outcome")["pnl"].agg(["count","mean","sum"]))