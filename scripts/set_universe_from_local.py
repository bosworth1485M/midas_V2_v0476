# scripts/set_universe_from_local.py
import argparse, glob, os, re, pathlib
ap=argparse.ArgumentParser(); ap.add_argument("--date", required=True)
a=ap.parse_args(); d=a.date
pat = os.path.join("data","samples", f"sample_{d}_*.csv")
syms = sorted({ re.sub(rf"^sample_{re.escape(d)}_", "", pathlib.Path(p).stem)
                for p in glob.glob(pat) })
out = pathlib.Path("data/samples/universe_sample.txt")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(syms), encoding="ascii")
print(f"Universe set to {len(syms)} symbols -> {out}")