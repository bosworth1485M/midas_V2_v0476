==== BEGIN ====

Midas_V2 — TESTING_GUIDE_POLYGON_v1.0

Version target: v0.6.0-AE-polygon-minute-20250805
(This guide uses real Polygon data, Python-only. It does not replace the local-data regression guide.)

This guide captures the exact, tested Python commands to:

build a real open-gap universe (Cameron-style) from Polygon,

fetch 1-minute bars in Eastern Time for those symbols,

run Scenarios A–E using the Python runner,

summarize and save a regression snapshot.

It does not change scenario definitions; it changes only the runners and inputs to be Python-only.

Data files & locations

Active universe (tickers): data/samples/universe_sample.txt
(one symbol per line; overwritten by Top Gappers when run without --no-write)

Minute-bar inputs (what backtests read): data/samples/sample_<YYYY-MM-DD>_<SYMBOL>.csv
header: time,open,high,low,close,volume (timestamps in America/New_York, DST-aware)

Backtest outputs (per scenario): out/<YYYYMMDD>/<SCENARIO>/results_<YYYY-MM-DD>.csv

Regression snapshots: Docs/REGRESSION_<YYYYMMDD>_AE_<label>.csv

1) Build the real open-gap universe

Open-gap % = (today_open − yesterday_close) / yesterday_close × 100; filter $1–$20, gap ≥ 5%, sort desc.

View only (no files changed):

python .\scripts\topgappers.py --date 2025-08-05 --no-write


Write the universe (recommended) + optionally trim to Top-N (faster runs):

python .\scripts\topgappers.py --date 2025-08-05 --top 25
python .\scripts\trim_universe.py --top 12


Result: data/samples/universe_sample.txt contains your Top-N symbols, one per line.

2) Fetch 1-minute bars in Eastern Time (ET)

Default: all sessions (premarket, regular, after-hours). Add --session rth for 09:30–16:00 ET only.

python .\scripts\fetch_minutes_polygon.py --date 2025-08-05
# or (regular hours only)
python .\scripts\fetch_minutes_polygon.py --date 2025-08-05 --session rth


Writes: one CSV per symbol
data/samples/sample_2025-08-05_<SYMBOL>.csv

3) Run scenarios A–E (Python-only)
python .\scripts\run_AE_simple.py --date 2025-08-05


Default scenarios: A,B,C,D,E

To run a subset: --scenarios E or --scenarios A,B,E

4) Summarize results (TP/SL/Win%)
python .\scripts\summarize_results.py --date 2025-08-05

5) Save a regression snapshot (CSV in Docs/)
python .\scripts\save_regression_snapshot.py --date 2025-08-05 --label polygon


Creates: Docs\REGRESSION_20250805_AE_polygon.csv

Reverting to local test data (optional)

If you want to switch back to the local (non-Polygon) regression path:

python .\scripts\set_universe_from_local.py --date 2025-08-05
python .\scripts\run_AE_simple.py --date 2025-08-05
python .\scripts\summarize_results.py --date 2025-08-05

Notes & guardrails

Time zone: minute bars are written in America/New_York (ET), DST-aware.

Sessions: default = all; pass --session rth for 09:30–16:00 ET.

Top Gappers overwrites: running topgappers.py without --no-write overwrites the universe. After overwriting, make sure you’ve fetched minutes for those symbols before running A–E.

Troubleshooting

“API Key was not provided” → ensure POLYGON_API_KEY is set or present in .env.

“No minutes for <symbol>” → illiquid ticker or no trades that day; trim Top-N or continue.

Slow runs → keep Top-N small (12–25) initially; widen later.

Versioning (recommended order)

Refresh docs and commit only if changed:

.\Docs\Refresh-Docs.ps1; if(git diff --name-only .\Docs\DEV_GUIDE.md){ git add .\Docs\DEV_GUIDE.md; git commit -m "docs: refresh DEV_GUIDE for v0.6.0"; git push } else { "DEV_GUIDE.md unchanged" }


Commit this guide + scripts + snapshot, then tag:

git add .\Docs\TESTING_GUIDE_POLYGON_v1.0.md .\Docs\REGRESSION_20250805_AE_polygon.csv .\scripts\run_AE_simple.py .\scripts\fetch_minutes_polygon.py .\scripts\trim_universe.py .\scripts\set_universe_from_local.py .\scripts\save_regression_snapshot.py
git commit -m "docs: Polygon testing guide v1.0; real-data regression (Python-only) and snapshot for 2025-08-05"
git tag -a v0.6.0-AE-polygon-minute-20250805 -m "A–E on real Polygon minute data (Python-only)"
git push
git push --tags


==== END ====