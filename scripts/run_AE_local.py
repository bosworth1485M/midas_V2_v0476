# scripts/run_AE_local.py
import argparse, subprocess, os
ap=argparse.ArgumentParser(); ap.add_argument("--date", required=True)
a=ap.parse_args(); day=a.date; d8=day.replace("-","")
scenarios=["A","B","C","D","E"]
for s in scenarios:
    out = os.path.join("out", d8, s)
    cmd = ["python","-m","midas_v2.cli","backtest",
           "--date", day, "--scenario", s,
           "--universe", "data/samples/universe_sample.txt",
           "--out", out]
    print("RUN:", " ".join(cmd))
    subprocess.run(cmd, check=True)
print("Done.")