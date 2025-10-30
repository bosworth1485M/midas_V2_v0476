# Midas_V2 — Release Notes v0.3.25 (aka “3.25”)  
**Date:** 2025-09-21

## Summary
This version introduces **range‑level Top‑N trimming** (`--top`) and cleans up **universe logging**, then validates the change by re‑running **August 2025** ranges for Scenario **B** with **Top‑12**. We also refreshed the test command references.

## What we changed
1) **Range runner: `--top` support (safe, minimal patch)**  
   - Added `--top` (1..50) to the range runner and **forwarded** it to `run_day_simple.py`.  
   - Validates the value (`1..50`), **backwards‑compatible** (None = unchanged).  
   - No key/.env changes; only argument parsing & command forwarding.

2) **Universe builder logging (`scripts/topgappers.py`)**  
   - Only prints **“Trimmed to Top‑N (from X)”** when an actual slice occurs.  
   - Otherwise prints **“Using full list (no trim)”** or **“Default cap=50 applied …”**.  
   - Removed duplicate **“has N symbols”** line to avoid double logging.

3) **Runner rename (finalizing interface)**  
   - After validation, renamed:  
     - `scripts/run_range_and_summarize_top.py` → **`scripts/run_range_and_summarize.py`**.

4) **Docs / references**  
   - Added/updated commands references (MD/TXT) with **dated** August examples and analyzers.  
   - Kept a “commands‑only” sheet and a longer dated reference with Revision History.

## Tests performed (August 5 → 31, 2025, Scenario B)
- **Baseline (full universe)** — previously recorded:  
  - Trades **235**, Wins/Losses **113/122**, **WR 48.09%**, **PnL −351.42**.
- **With Top‑12 per day (this version):**  
  - Trades **161**, Wins/Losses **80/81**, **WR 49.69%**, **PnL −168.44**.
- **Effect:** **−74 trades**, **+1.6 pp WR**, **+182.98 PnL** vs full baseline.  
  Directionally better, but still sub‑50% WR → compare D/E next.

> Analyzer one‑liners used:  
> `python scripts/analyze_range_explained.py --csv out\auto\range_summary_20250805_20250831_B.csv`

## Files updated / added
- **Added**: `scripts/run_range_and_summarize_top.py` (temporary during validation)  
  - Argparse: `--top` with validation; forward to day runner; unchanged defaults.  
- **Renamed (final)**: `scripts/run_range_and_summarize.py` (from *_top.py)  
- **Modified**: `scripts/topgappers.py`  
  - Conditional **trim** message; removed duplicate **has N symbols** print.  
- **Docs** (examples):  
  - `Docs/Test Commands/Midas_Backtesting_Commands_v1.1.md/.txt` (dated Aug‑2025 commands)  
  - `Test_Commands_CheatSheet_v0.3.26.md/.pdf` (runner rename reflected; commands‑only variant)  

## Known impacts
- **No changes** to keys, `.env`, or data loaders.  
- Range summaries keep the same filenames; if you run with Top‑N, note the setting in your commit message.

## Quick commands (for reproducibility)
```powershell
# Range — Scenario B, Top-12 (Aug)
python scripts/run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B --top 12

# Analyzer
python scriptsnalyze_range_explained.py --csv oututoange_summary_20250805_20250831_B.csv
```

## Next steps
1) Run **Scenario D** and **Scenario E** over **Aug‑05..Aug‑31** with **--top 12** and compare.  
2) Consider adding **Opening RVOL gate** (≥1.5, first 10–15m vs prior day).  
3) Evaluate **SL 2.0** vs 2.5 if WR target ≥55% takes priority.

---

### Appendix A — Rationale
- Trimming the daily universe reduces thin/low‑quality names and often **raises WR** at similar TP/SL.  
- Logging clarity prevents misreads (“trimmed to 50 from 17” when nothing changed).

### Appendix B — Exact analyzer paths
```powershell
python scriptsnalyze_range_explained.py --csv oututoange_summary_20250805_20250831_B.csv
python scriptsnalyze_range_explained.py --csv oututoange_summary_20250805_20250831_D.csv
python scriptsnalyze_range_explained.py --csv oututoange_summary_20250805_20250831_E.csv
```
