# Catalyst Continuation Cheat Sheet with Commands (v0.3.17)

## Continuation Steps
1. **Top-N Catalyst Universe per Day**
   - Build enriched universe (A backbone, B filler only).
   - Cap list to 3–5 tickers.
2. **Apply Denylist**
   - Exclude Chinese ADRs, OTC, garbage tickers.
   - File: `data/denylist.txt`.
3. **Set Active Universe**
   - Write final Top-N (after denylist) to `data/universe_active.txt`.
4. **Opening RVOL Gate**
   - Require ≥1.5× RVOL in first 10–15 min vs prev day.
5. **Run Tests**
   - Run **D_strict** first, then **B**, then **E_dip**.
   - Test across **August** then **September**, summarize WR/PnL.

---

## Catalyst Scoring System
- **3 (A-grade)**: Strong catalyst (earnings beat, FDA approval, big PR). Clean $1–20, high RVOL. → Backbone.
- **2 (B-grade)**: Moderate catalyst (analyst, partnership). Volume present. → Filler if Top-N too short.
- **1 (C-grade)**: Weak/hype-only/unclear. → Exclude normally.
- **0 / Denylist**: Exclude outright (Chinese ADRs, OTC, garbage).

---

## Definition of "Wired Scenarios"
- “Wired” means **implemented in code**, runnable end-to-end.
- Each scenario has parameter sets (EMA/VWAP, MACD, dip reclaim, TP/SL).
- Wiring = test harness for measurement, **not** validation or profitability.
- Low WRs highlight the need for catalyst, denylist, RVOL, and router logic.

---

## Key Commands (One-Liners)

### Catalyst Workflow
- Enrich with news:  
  `python scripts/enrich_universe_catalyst.py --date 2025-08-05 --out data/catalyst`
- Apply denylist + finalize active universe:  
  *(built-in or wrapper logic)* → outputs `data/universe_active.txt`

### Daily Runs (using active universe)
- Scenario D:  
  `python scripts/run_day_simple.py --date 2025-08-05 --scenario D`
- Scenario B:  
  `python scripts/run_day_simple.py --date 2025-08-05 --scenario B`
- Scenario E:  
  `python scripts/run_day_simple.py --date 2025-08-05 --scenario E`

### Range Runs (Validation)
- D strict:  
  `python scripts/run_range_safe.py --start 2025-08-05 --end 2025-08-31 --scenario D`
- B baseline:  
  `python scripts/run_range_safe.py --start 2025-08-05 --end 2025-08-31 --scenario B`
- E dip:  
  `python scripts/run_range_safe.py --start 2025-08-05 --end 2025-08-31 --scenario E`

### Results & Summaries
- Summarize single date:  
  `python scripts/summarize_results.py --date 2025-08-05`
- Summarize range:  
  `python scripts/run_range_and_summarize.py --start 2025-09-05 --end 2025-09-30 --scenario D`

### Git – Tagging
- Tag:  
  `git tag -a v0.3.17-catalyst-rvol -m "v0.3.17: catalyst Top-N + denylist + RVOL gate + Aug/Sep validation"`
- Push:  
  `git push && git push --tags`

---

⚠️ **Reminder**: To truthfully claim a WR >60%, results must be tested across **hundreds of trading days**.
