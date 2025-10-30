======================== START: RUN_DAY_SIMPLE GUIDE ========================

# 📘 Guide: Using run_day_simple.py in Midas_V2

## 1. Purpose
`run_day_simple.py` is a one-shot helper. It:
1. Builds the **universe** for the chosen date (from Polygon top gappers).
2. Fetches the **minute-bar samples** into `data/samples/`.
3. Rebuilds a clean **universe file** and runs the **backtest scenarios**.

## 2. How to Run

### Basic run (default Scenario B):
python scripts/run_day_simple.py --date 2025-08-06

### Multiple scenarios (e.g. B and E):
python scripts/run_day_simple.py --date 2025-08-06 --scenarios B,E

### Refresh samples (delete any old files first):
python scripts/run_day_simple.py --date 2025-08-06 --scenarios B,E --refresh-samples

## 3. What It Produces
1. **Samples** in `data/samples/`  
   → e.g. `data/samples/sample_2025-08-06_LPSN.csv`
2. **Universe file** in `data/universe_topgappers_2025-08-06.txt`  
   → clean list of tickers, one per line.
3. **Backtest outputs** in `out/auto/<DATE>/<SCENARIO>/results_<DATE>.csv`  
   → e.g. `out/auto/20250806/B/results_2025-08-06.csv`
4. **Console log**  
   → shows `[SAMPLES]`, `[UNIVERSE]`, `[OK]`, `[DONE]`.

## 4. Next Steps
1. Summarize PnL:
   python scripts/summarize_pnl.py --date 2025-08-06 --scenarios B,E
2. Compare with Aug 5:
   python scripts/run_day_simple.py --date 2025-08-05 --scenarios B,E --refresh-samples
   python scripts/summarize_pnl.py --date 2025-08-05 --scenarios B,E
3. Decide baseline:
   - Aug 5: Scenario B → profitable (+16)
   - Aug 6: Scenario B → loss (–54)
   - Scenario E → consistently negative
4. Future:
   - Add guardrails to Scenario B (TP=2.0, SL=2.5, MACD confirm, exclude `.WS`)
   - Re-test Aug 5 and 6
   - If stable, tag as v0.5.1-B_safe

======================== END: RUN_DAY_SIMPLE GUIDE ========================