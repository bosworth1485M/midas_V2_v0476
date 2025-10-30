# Midas_V2 — v0.3.6-prev-trading-day-fix (Sep 2–5 window) — Results & Next Steps

This version documents a **single, surgical change** to restore your fast workflow and fix the Sep‑2 holiday edge case, plus the exact commands we ran and what we observed.

---

## What changed (tiny, safe)
- **topgappers.py**: now calls your existing **`scripts/prev_trading_day_polygon.py`** to resolve the **prior trading day** (not prior calendar day).  
- **Arg compatibility**: accepts/ignores extra args (e.g., `--session`) so `run_day_simple.py` works unchanged.  
- **Nothing else changed**: same outputs, same defaults, same strategy code and scripts.

**Why:** Sep‑1, 2025 was Labor Day. Using the prior *calendar* day made Sep‑2 look broken. Calling your helper guarantees Sep‑2 uses **Aug‑29** as “previous trading day.”

---

## Commands we used (your normal flow)

### Single-day checks (D and/or E)
```powershell
# Run a single day
python scripts\run_day_simple.py --date 2025-09-02 --scenario D
python scripts\summarize_results.py --date 2025-09-02
```

### Short range (auto-rebuilds summary)
```powershell
python scripts\run_range_safe.py --start 2025-09-02 --end 2025-09-05 --scenario D
python scripts\run_range_safe.py --start 2025-09-02 --end 2025-09-05 --scenario E

# View and analyze rebuilt summaries
python scripts\show_latest_range.py --root out\auto --scenario D
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250902_20250905_D.csv

python scripts\show_latest_range.py --root out\auto --scenario E
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250902_20250905_E.csv
```

---

## Results we saw (September 2–5, 2025)

### D (continuation; strict)
Per-day (from rebuilt range summary):
- **2025‑09‑02**: trades **3**, **0/3**, WR **0.00%**, PnL **−30.79**  
- **2025‑09‑03**: trades **3**, **0/3**, WR **0.00%**, PnL **−33.04**  
- **2025‑09‑04**: trades **7**, **2/5**, WR **28.57%**, PnL **−76.87**  
- **2025‑09‑05**: trades **5**, **1/4**, WR **20.00%**, PnL **−22.83**  

Totals (Sep 2–5): **18 trades**, **3/15**, WR **16.67%**, PnL **−163.53**.

### E (dip‑reclaim) — same span
Per-day (from rebuilt range summary):
- **2025‑09‑02**: trades **10**, **4/6**, WR **40.00%**, PnL **−24.18**  
- **2025‑09‑03**: trades **4**, **1/3**, WR **25.00%**, PnL **−15.06**  
- **2025‑09‑04**: trades **3**, **0/3**, WR **0.00%**, PnL **−27.61**  
- **2025‑09‑05**: trades **3**, **0/3**, WR **0.00%**, PnL **−18.66**  

Totals (Sep 2–5): **20 trades**, **5/15**, WR **25.00%**, PnL **−85.51**.

> **Interpretation:** The software is fast again; the holiday edge is fixed. This particular week was simply unfavorable for our momentum profiles (both D and E).

---

## What to do next (pick one)

**A) Move to a cleaner window** (recommended):  
Run **Oct 1–5** for D (and optionally E) to validate in a fresh market regime.
```powershell
python scripts\run_range_safe.py --start 2025-10-01 --end 2025-10-05 --scenario D
python scripts\run_range_safe.py --start 2025-10-01 --end 2025-10-05 --scenario E
```

**B) Tiny hygiene (for choppy weeks, no redesign):**  
For a given day, exclude obvious noisy tickers (warrants/units/leveraged ETFs) right after gappers **just for that run**, then proceed as normal.
```powershell
python scripts\topgappers.py --date 2025-09-02
(Get-Content data\samples\universe_sample.txt) ^
  | Where-Object { $_ -notmatch '\.WS$|\.U$|UVXY|SOXS|VIXI|FNGD|SSG|TSLL|TSLT' } ^
  | Set-Content data\samples\universe_sample.txt
python scripts\run_day_simple.py --date 2025-09-02 --scenario D
python scripts\summarize_results.py --date 2025-09-02
```

**C) Keep September D‑only, archive, and proceed to router (later):**  
When ready, implement the **v0.3.6‑hybrid‑router** (D>E precedence, one position per symbol, risk split) as discussed, but only after validating another clean window.

---
**D) Regression check on known‑good August days (no regressions):**  
Re‑run the August days that historically worked to confirm nothing regressed after the tiny fix.
```powershell
# D_strict sanity
python scripts\run_day_simple.py --date 2025-08-06 --scenario D
python scripts\summarize_results.py --date 2025-08-06

# E_dip sanity (if applicable in your current branch/settings)
python scripts\run_day_simple.py --date 2025-08-22 --scenario E
python scripts\summarize_results.py --date 2025-08-22
```


## Version & tagging

This is a small, documented step on top of your prior tag (no redesign). If you want to tag it:

```powershell
git add scripts/topgappers.py
git commit -m "Fix: topgappers uses prev_trading_day_polygon (arg‑compatible); no behavior change"
git tag -a v0.3.6-prev-trading-day-fix -m "Holiday edge fixed; software fast again; Sep 2–5 results recorded"
git push; git push --tags
```

*Prepared on 2025‑09‑06.*
