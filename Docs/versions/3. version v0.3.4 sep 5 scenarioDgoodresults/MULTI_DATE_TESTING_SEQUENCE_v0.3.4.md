# Midas_V2 — Multi‑Date Testing Sequence (Validated) — v0.3.4 candidate

This note records exactly what we ran today, why earlier results looked off, how we fixed it, and the *validated* results for Scenario **D** with a fresh universe per day.

---

## What changed (so today’s results are genuine)
- **topgappers.py** now **writes a fresh universe** every run (no `--no-write`), and tolerates extra args via `parse_known_args()`.
- **run_range_and_summarize.py** was fixed to use `--scenario` and to stop passing unsupported flags to `run_day_simple.py`.
- Verified on **2025‑08‑06**: `Wrote 94 symbols -> data\samples\universe_sample.txt` and backtest ran clean.

---

## Commands we executed (Scenario D)

### Short range (sanity check)
```powershell
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-10 --scenario D
python scripts\show_latest_range.py --root out\auto --scenario D
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250805_20250810_D.csv
```

### Single-day verification (universe written & used)
```powershell
python scripts\run_day_simple.py --date 2025-08-06 --scenario D
# observed: Wrote 94 symbols -> data\samples\universe_sample.txt
```

### Long range (validated)
```powershell
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario D
python scripts\show_latest_range.py --root out\auto --scenario D
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250805_20250831_D.csv
```

---

## Results (Scenario D, 2025‑08‑05 → 2025‑08‑31)
- **Total trades:** 79  
- **Wins / Losses:** 50 / 29  
- **Overall Win Rate:** **63.29%**  
- **Total PnL:** **+167.57**  
- **Days with trades / zero‑trade days:** 3 / 13  
- **Best day:** 2025‑08‑06 (PnL +174.33, Trades 38, WR 65.79%)  
- **Worst day:** 2025‑08‑05 (PnL −19.39, Trades 3, WR 0.00%)

**Interpretation:** D exceeds the 55% WR target. Good candidate baseline. Many zero‑trade days → we can broaden universe or ease guards later *after* baseline is locked.

> Note: Earlier **B** results were produced before the universe fix and may reflect a STTK‑only universe. Re‑run B after the fix to get a fair baseline.

---

## Next steps
1) Run **D** across more dates (e.g., 2025‑09‑01 → 2025‑09‑30) to increase sample size.  
2) Re‑run **B** (fresh universe) for a true baseline comparison.  
3) Trial **E (dip‑reclaim)** against D to evaluate added entries vs WR.  
4) Only after baselines: consider 1‑second entries and multiple trades per ticker.

---

## Version tagging
**Proposed tag:** `v0.3.4-rangefix`

Two lines:
```powershell
git add -A; git commit -m "Docs: validated multi-date testing; D >60% WR with daily universe; range runner & gappers fixed"
git tag -a v0.3.4-rangefix -m "Milestone: daily-universe validation; Scenario D ~63% WR (Aug '25)"; git push; git push --tags
```

---

## Appendix — Analyzer outputs (verbatim)

### D (Validated) — range_summary_20250805_20250831_D.csv
```text
------------------------------------------------------------------------
Range Analysis — range_summary_20250805_20250831_D.csv
------------------------------------------------------------------------
Overview
  Rows                      : 16 (days in range)
  Days with trades          : 3
  Days with zero trades     : 13
Totals
  Total Trades              : 79
  Wins / Losses             : 50 / 29
  Overall Win Rate          : 63.29%   (wins / (wins+losses))
  Total PnL                 : 167.57     (sum of daily PnL)
Daily Quality (on trade days)
  Avg Daily Win Rate        : 43.86%
  Median Daily Win Rate     : 65.79%
Best Day                    : 2025-08-06  PnL +174.33  Trades 38  WR 65.79%
Worst Day                   : 2025-08-05  PnL -19.39  Trades 3  WR 0.00%
------------------------------------------------------------------------
Interpretation
  ✔ Baseline WR is in the target zone (≥55%). Continue expanding the sample.
  Note: Many zero‑trade days — consider broadening the universe or easing filters later (after baseline).
------------------------------------------------------------------------
Next Actions
  1) Run another range to increase sample size (same scenario).
  2) If WR <55%, compare with Scenario D_strict (tighter early guard) or E_dip (reclaim entries).
  3) Only after baseline is validated, consider 1‑sec entries or multiple trades per ticker.
------------------------------------------------------------------------
```

### B (Pre-fix, stale universe) — range_summary_20250805_20250831_B.csv
```text
------------------------------------------------------------------------
Range Analysis — range_summary_20250805_20250831_B.csv
------------------------------------------------------------------------
Overview
  Rows                      : 16 (days in range)
  Days with trades          : 7
  Days with zero trades     : 9
Totals
  Total Trades              : 91
  Wins / Losses             : 45 / 46
  Overall Win Rate          : 49.45%   (wins / (wins+losses))
  Total PnL                 : -92.44     (sum of daily PnL)
Daily Quality (on trade days)
  Avg Daily Win Rate        : 41.78%
  Median Daily Win Rate     : 44.44%
Best Day                    : 2025-08-05  PnL +76.78  Trades 27  WR 66.67%
Worst Day                   : 2025-08-08  PnL -79.96  Trades 20  WR 50.00%
------------------------------------------------------------------------
Interpretation
  ✖ WR < 50%. Prioritize guard tuning before expanding sample size.
  Note: Many zero‑trade days — consider broadening the universe or easing filters later (after baseline).
------------------------------------------------------------------------
Next Actions
  1) Run another range to increase sample size (same scenario).
  2) If WR <55%, compare with Scenario D_strict (tighter early guard) or E_dip (reclaim entries).
  3) Only after baseline is validated, consider 1‑sec entries or multiple trades per ticker.
------------------------------------------------------------------------
```

---

## Appendix — Scenario **D (strict)** explained, end‑to‑end

**Goal.** Scenario **D** is our stricter momentum profile designed to avoid early‑session chop and prioritize higher win rate. It keeps confirmations tight and limits entries early in the day with a short **gate**.

### A) Data & universe (inputs)
1. **Daily universe** comes from `scripts/topgappers.py` (now writes fresh each run).  
   - Source: Polygon grouped bars (today open vs yesterday close).  
   - Defaults: `--min-price 1`, `--max-price 20`, `--min-gap 5`, `--top 50`.  
   - Output: `data/samples/universe_sample.txt` (one symbol per line).
2. **Minute data** is fetched per symbol/day by `scripts/fetch_minutes_polygon.py --session rth` and cached under `data/samples/*.csv`.

> Why you saw zero‑trade days earlier: before the fix, the universe was stale (often STTK‑only). Now it refreshes daily; zero‑trade days simply mean no setups met D’s stricter conditions that day.

### B) Current default parameters (from run logs)
```
min_pm_vol = 30000         # premarket liquidity floor
ema_confirm = True         # require 9‑EMA alignment
vwap_confirm = True        # require VWAP alignment
ema_period = 9
macd_confirm = True        # MACD must be supportive
rise_bars = 2              # need 2 rising MACD bars
gate_minutes = 5           # wait the first 5 minutes after the open
tp_pct = 2.0               # take‑profit at +2.0%
sl_pct = 2.5               # stop‑loss at −2.5%
dip_reclaim = False        # (off in D) dip‑reclaim entries disabled
reclaim_pmh = False        # (off) breakout over pre‑market high not required
min_reclaim_pct = 0.5      # if reclaim logic is used by the engine, min reclaim size (bps)
reclaim_ref = "ema"        # reclaim measured against EMA baseline
```
These came from the engine banner during your runs on 2025‑08‑06 and others.

### C) Confirmation stack (what must be true)
- **EMA(9) & VWAP confirm**: price action aligns above/with these baselines (helps filter weak pops).  
- **MACD confirm (rise_bars=2)**: histogram rising for ≥2 bars, momentum direction supportive.  
- **Premarket volume ≥ 30k**: thin issues are filtered out.

### D) Timing guard (gate)
- **gate_minutes = 5**: No entries allowed until 9:35 ET. This cuts out the noisiest 5 minutes.

### E) Entry logic (how a trade is allowed)
- The engine requires the **confirmation stack** first.  
- With **dip_reclaim=False** and **reclaim_pmh=False**, D focuses on **clean momentum continuation** with EMA/VWAP conformity and MACD support.  
- Where the engine uses reclaim sizing, **min_reclaim_pct=0.5**% and **reclaim_ref='ema'** provide a minimum move against the EMA to qualify the trigger.
- Result: fewer, cleaner entries than B; typically higher WR, lower frequency.

### F) Exits & risk
- **Hard TP/SL**: +2.0% TP, −2.5% SL.  
- **EOD flatten**: positions closed by end of day (no overnights).  
- Engine logging writes `results_YYYY-MM-DD.csv` per day and scenario with PnL outcomes.

### G) Why D can show many zero‑trade days
- Conditions are **strict**: EMA+VWAP+MACD alignment plus gate and liquidity floor.  
- Some days simply have no compliant setups in the price/gap band. That’s acceptable for a high‑WR baseline.

### H) How D differs from B (baseline)
- **D is stricter**: shorter gate (5 vs 10), identical TP/SL, same EMA/VWAP+MACD confirmations, dip‑reclaim disabled.  
- **Effect**: fewer early whipsaws, fewer trades overall, **higher WR** in your August sample.

### I) Recommended usage
- Use **D** as your safer baseline while building sample size and validating.  
- Once D is stable (≥55% WR over many dates), compare against **E (dip‑reclaim)** to potentially add entries without sacrificing WR.

### J) Quick commands (recap)
```powershell
# Run long D range
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario D

# Show latest D summary
python scripts\show_latest_range.py --root out\auto --scenario D

# Explain totals (D)
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250805_20250831_D.csv
```

### K) Troubleshooting checklist
- Universe shows “Wrote N symbols”: if **N=0**, check Polygon key / market holiday.  
- Too many zero‑trade days? Confirm `min_pm_vol`, price band, and MACD `rise_bars`.  
- Unexpected arg errors? You’re already on the hardened `topgappers.py` (parse_known_args, `--out`). Re‑run `Docs/refresh_docs.py` if scripts list looks stale.
