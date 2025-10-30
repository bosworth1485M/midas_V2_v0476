==== BEGIN ====

Midas_V2 — Regression Testing Guide (Stage 2: Python-only)

Version target: v0.5.4-regression-local-python

This stage replaces PowerShell wrappers with Python scripts only. It reproduces A–E using local minute-bar CSVs you already have. The Top Gappers and Previous Trading Day utilities are documented but not integrated here.

Scope

✅ Run Scenarios A–E using local minute CSVs under data/samples/

✅ Use data/samples/universe_sample.txt (one symbol per line)

✅ Summarize results (TP/SL/Win%) with Python

❌ Do not fetch real minute bars in this stage

❌ Top Gappers / Previous Trading Day are standalone utilities, not integrated

Data files & locations (clarification)

Inputs (minute bars): data/samples/sample_<YYYY-MM-DD>_<SYMBOL>.csv
Header: time,open,high,low,close,volume — these are what backtests read.

Active universe (tickers): data/samples/universe_sample.txt
One symbol per line; only these symbols are processed.

Outputs (results): out/<YYYYMMDD>/<SCENARIO>/results_<YYYY-MM-DD>.csv

Other CSVs (not inputs): data/samples/topgappers_<DATE>*.csv (Polygon lists; not minute inputs)

Stage 2 — A–E (LOCAL) with Python only

1) Set the universe from local CSVs (no guessing)

python .\scripts\set_universe_from_local.py --date 2025-08-05


2) Run A–E (Python CLI only; uses the current universe)

python .\scripts\run_AE_local.py --date 2025-08-05


3) Summarize results (TP/SL/Win%)

python .\scripts\summarize_results.py --date 2025-08-05


These three commands are the canonical local-regression flow.
They do not call any PowerShell wrapper and do not fetch real data.

Standalone utilities (not integrated in this stage)

Top Gappers (open-gap; real Polygon list)

View only (no files changed):

python .\scripts\topgappers.py --date 2025-08-05 --no-write


Overwrite active universe (optional):

python .\scripts\topgappers.py --date 2025-08-05


⚠️ Overwriting the universe switches A–E to real symbols. Unless you also fetch minute bars for those symbols, backtests will warn “Missing sample file …”.
To revert to local regression, re-run “Set the universe from local CSVs” above.

Previous Trading Day (Polygon)

Date only (for piping):

python .\scripts\prev_trading_day_polygon.py --date 2025-08-05 --quiet


Verbose:

python .\scripts\prev_trading_day_polygon.py --date 2025-08-05

Troubleshooting

“Missing sample file … sample_YYYY-MM-DD_SYMBOL.csv”
→ Your universe lists symbols without local minute bars. Re-run the Set universe step or fetch minutes first.

“API Key was not provided” (Top Gappers / Prev Day)
→ Ensure POLYGON_API_KEY is set or present in .env.

Versioning

When satisfied, tag as: v0.5.4-regression-local-python
“Regression testing (local data) with Python-only runners; Top Gappers & Previous Trading Day documented, not integrated.”
==== END ====