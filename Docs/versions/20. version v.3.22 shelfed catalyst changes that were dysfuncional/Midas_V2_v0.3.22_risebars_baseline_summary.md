# Midas_V2 – v0.3.22-risebars-baseline (Ready to tag)

## What we finalized today
- **Stability first**
  - Restored **stable** `src\midas_v2\strategy.py` from **v0.3.21**.
  - Turned **off** any experimental toggle (`MIDAS_USE_EXPERIMENTAL` is unset).
  - Ignored/removed the experimental file to avoid confusion.

- **Scenarios configured**
  - Set **`rise_bars = 3`** for **B, D, E**.  
    - **Note:** `rise_bars` means **rising price candles** (each close > prior close), not MACD.
  - Left **`macd_rise_bars`** as a placeholder (stable strategy doesn’t enforce histogram rise).  
    - We **plan to implement histogram bars** soon. We attempted to add it today, but could not get the changes to **“strategy.pm”** (i.e., your strategy file; in this repo it’s **`strategy.py`**) working cleanly. We’ve parked it to avoid churn.

- **Catalyst + keys**
  - Parked complex catalyst gating; SAFE runs are fine. No key changes needed for backtests.

- **Results (Aug-05 single day)**
  - **B (baseline):** 11 TP / 9 SL → **55.00%** WR  
  - **D (strict):** 10 TP / 10 SL → **50.00%** WR  
  - **B (catalyst, earlier compare):** 2 TP / 1 SL → **66.67%** WR

---

## Full command log (today)

### Toggle / restore / cleanup
```powershell
# Ensure experimental toggle is OFF
Remove-Item Env:\MIDAS_USE_EXPERIMENTAL -ErrorAction SilentlyContinue

# Restore stable strategy
git restore --source v0.3.21 -- src\midas_v2\strategy.py

# (Optional) Remove experimental file to avoid confusion
if (Test-Path src\midas_v2\strategy_experimental.py) { Remove-Item src\midas_v2\strategy_experimental.py -Force }
```

### Scenario JSON updates
```powershell
# Set rise_bars for B, D, E (rising price candles)
python -c "import json; p='config/scenarios.json'; d=json.load(open(p,encoding='utf-8')); d['B']['params']['rise_bars']=3; json.dump(d, open(p,'w',encoding='utf-8'), ensure_ascii=False, indent=2)"
python -c "import json; p='config/scenarios.json'; d=json.load(open(p,encoding='utf-8')); d['D']['params']['rise_bars']=3; json.dump(d, open(p,'w',encoding='utf-8'), ensure_ascii=False, indent=2)"
python -c "import json; p='config/scenarios.json'; d=json.load(open(p,encoding='utf-8')); d['E']['params']['rise_bars']=3; json.dump(d, open(p,'w',encoding='utf-8'), ensure_ascii=False, indent=2)"

# (Optional clarity) Disable histogram flag in summaries for B/D/E
python -c "import json; p='config/scenarios.json'; d=json.load(open(p,encoding='utf-8')); [d[s]['params'].update({'macd_rise_bars':0}) for s in ('B','D','E')]; json.dump(d, open(p,'w',encoding='utf-8'), ensure_ascii=False, indent=2)"

# Sanity print
python -c "import json; d=json.load(open('config/scenarios.json',encoding='utf-8')); print({k:d[k]['params'].get('rise_bars') for k in ('B','D','E')})"
```

### Day runs (Aug-05)
```powershell
# Baseline B, no RVOL flags (stable path)
python scripts\run_day_simple_SAFE.py --date 2025-08-05 --scenario B
python scripts\summarize_results.py --date 2025-08-05

# Strict D for same day (compare)
python scripts\run_day_simple_SAFE.py --date 2025-08-05 --scenario D
python scripts\summarize_results.py --date 2025-08-05
```

### (Earlier catalyst compare you ran today—recorded for completeness)
```powershell
# Enrich + SAFE catalyst (B), then summarize
python scripts\enrich_universe_catalyst.py --date 2025-08-05 --limit 50 --allow-b-fill
python scripts\run_day_catalyst_SAFE.py --date 2025-08-05 --scenario B --min-grade 2 --allow-b-fill
python scripts\summarize_results.py --date 2025-08-05
```

*(You also ran several direct `-m midas_v2.cli backtest` calls with/without `--min-rvol-open`. Post-restore we’re not using RVOL flags until we reintroduce the histogram/RVOL work sanely.)*

---

## Version + Git (single lines; no `&&`)
```powershell
git add -A
```
```powershell
git commit -m "Scenarios: enable rising-candle gate (rise_bars) for B/D/E; revert to stable strategy; no catalyst changes"
```
```powershell
git tag -a v0.3.22-risebars-baseline -m "v0.3.22: rising-candle gate on stable strategy; B/D/E configured; catalyst parked; MACD histogram planned"
```
```powershell
git push
```
```powershell
git push --tags
```

---

## What “bars” means (clear terminology)
- **`rise_bars`** = **rising price candles** (close-to-close increasing; often ≥2–3).  
- **MACD histogram bars** (separate) = *indicator* values rising; will be enforced later via `macd_rise_bars` when we add it back in a single, tested drop-in.

---

## Next steps (after you tag)
1) Run August ranges on the stable setup:
```powershell
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario D
```
2) We’ll review B vs D outcomes.  
3) Then, if you want, we’ll re-introduce **MACD histogram rising** (and a clean opening-strength check) as a **single, isolated update**—no churn, no flow changes.
