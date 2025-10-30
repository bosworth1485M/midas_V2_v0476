# CATALYST_GUIDE_v0.3.13

## Version
**v0.3.13-catalyst-workflow**

---

## Purpose
This version builds on earlier work and **formally locks in the catalyst workflow**. The aim is to allow isolated testing of specific, news-driven tickers (catalysts) such as STTK and LPSN without altering or breaking the normal top-gapper workflow.

- Implemented via `scripts/run_catalyst.py` with a **safe universe swap**.  
- Ensures that enrichment and backtests run as usual but on catalyst tickers only.  
- After execution, the normal universe file is restored so no changes affect the main codebase.

---

## Approach
1. **Catalyst runner** (`scripts/run_catalyst.py`):
   - Inputs: `--date`, `--scenario`, `--symbols` or `--file`.
   - Writes a dated catalyst universe file (`data/catalyst/universe_<date>.txt`).
   - Temporarily swaps this into `data/samples/universe_sample.txt`.
   - Runs enrichment (`fetch_minutes_polygon.py`) + backtest (`midas_v2.cli` or `run_day_simple.py` fallback).
   - Restores the original universe afterward.

2. **Design principles**:
   - No edits to core code required.  
   - Catalyst output is stored in the normal `out\YYYYMMDD\<Scenario>` structure.  
   - Compatible with existing summarizers and analysis tools.

---

## What We Tested

### STTK — 2025-08-05 (Scenario D)
Command:
```
python scripts/run_catalyst.py --date 2025-08-05 --scenario D --symbols STTK --fetch-minutes
```
- Enrichment wrote `data/samples/sample_2025-08-05_STTK.csv`.
- Backtest saved:
  - `out/20250805/D/results_2025-08-05.csv`
  - `out/20250805/D/summary_2025-08-05.txt`
- STTK result confirmed: **TP +2.04%**.

### LPSN — 2025-08-06 (Scenario B)
Command:
```
python scripts/run_catalyst.py --date 2025-08-06 --scenario B --symbols LPSN --fetch-minutes
```
- Output saved to `out/20250806/B/results_2025-08-06.csv` and summary.

---

## Commands Used

- **STTK catalyst run**:
```
python scripts/run_catalyst.py --date 2025-08-05 --scenario D --symbols STTK --fetch-minutes
```

- **LPSN catalyst run**:
```
python scripts/run_catalyst.py --date 2025-08-06 --scenario B --symbols LPSN --fetch-minutes
```

- **Sanity check**:
```
$csv = 'out\20250805\D\results_2025-08-05.csv'; if (Test-Path $csv) { "$csv -> " + ((Get-Content $csv | Measure-Object -Line).Lines) }
```

---

## Current Status
- Catalyst workflow verified.  
- Safe swap + restore confirmed.  
- Catalyst-specific enrichment and backtests validated with STTK and LPSN.  
- Existing top-gapper code unaffected.  

---

## Next Stage

1. **Multi-day Catalyst Runs**  
   - Extend to multiple days (e.g., Aug 5 and Aug 6) and scenarios (B, D, E).  
   - Benchmark catalyst-only results against normal universe runs.  

2. **Polygon Catalyst Integration**  
   - Enrich catalysts with Polygon news data (e.g., `/v2/reference/news`).  
   - Record headlines and catalyst type alongside each run.  
   - Use this enrichment to evaluate whether news-driven catalysts outperform random gappers.  

3. **Filtering & Hygiene**  
   - Add blocklists (e.g., exclude Chinese tickers).  
   - Optional `--exclude-file` in `run_catalyst.py` for safe filtering.  
   - Paranoia mode (`--only-catalyst`) to ensure only chosen symbols are backtested.  

4. **Docs & Summaries**  
   - Merge catalyst results into existing summary reports.  
   - Tag outputs clearly as catalyst runs for historical analysis.  

---

## Summary
**v0.3.13-catalyst-workflow** finalizes the safe universe swap design and confirms catalyst backtests with STTK and LPSN. The next focus is expanding catalyst validation across days/scenarios and enriching catalysts with Polygon news data, while keeping the main codebase stable.
