# Midas_V2 — Scenario B Cheat Sheet  
*(One-Day Tests with Polygon, and Multi-Day Range Runs)*

---

## One Day (Polygon, Scenario B)

```powershell
python scripts\run_day_simple.py --date 2025-08-05 --scenario B
.\scripts\Summarize-Scenarios.ps1 -Date 2025-08-05
Replace 2025-08-05 with any date you want to test.
Results are written to:

css
Copy code
out\YYYYMMDD\B\results_YYYY-MM-DD.csv
Another Day (same flow)
powershell
Copy code
python scripts\run_day_simple.py --date 2025-08-06 --scenario B
.\scripts\Summarize-Scenarios.ps1 -Date 2025-08-06
Multi-Day (when ready)
Python range runner
powershell
Copy code
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-07
PowerShell per-day runner
powershell
Copy code
.\scripts\run_backtest.ps1 -Date 2025-08-05 -Scenario B
.\scripts\run_backtest.ps1 -Date 2025-08-06 -Scenario B
.\scripts\run_backtest.ps1 -Date 2025-08-07 -Scenario B
.\scripts\Summarize-Scenarios.ps1 -Start 2025-08-05 -End 2025-08-07
Docs & Versioning (after a working checkpoint)
powershell
Copy code
.\Docs\Refresh-Docs.ps1
git add -A
git commit -m "Checkpoint: Scenario B Cameron baseline; Polygon one-day tests; docs refreshed"
git tag -a v0.3.x-b-baseline-check -m "Working B baseline checkpoint"
git push && git push --tags
Notes
Scripts to use (existing only):

scripts/run_day_simple.py → one-day Polygon tests

scripts/run_range_and_summarize.py → multi-day range

scripts/run_backtest.ps1 / scripts/Summarize-Scenarios.ps1 → PowerShell runners & summaries

Scenario B (Cameron baseline):

gap ≥ 10%

price $1–$20

EMA + VWAP + MACD confirm

gate = 10 minutes

TP = 2.0%, SL = 2.5%

min_pm_vol = 30k

guardrails: max 1 trade per symbol, daily stop = 1000

Polygon key: stored in .env and loaded automatically.
No need to set it manually in normal use.

