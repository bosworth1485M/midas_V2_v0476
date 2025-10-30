# Session Summary for Midas_V2 v0.4.2
## Use this file at the start of the next session to restore context.

### Overview
Version **v0.4.2** marks a stable checkpoint after several important fixes and validations to the catalyst flow. The focus was on correcting logic inconsistencies, improving reliability, and preparing the system for adaptive sizing and profitability improvements.

---

## 🔧 Code Changes

### 1. **`run_catalyst_flow.py` fully updated**
- Fixed core logic so that **compose_universe_hybrid.py** now receives the **filtered catalyst list** derived from `catalyst_news_{date}_filtered.csv`.
- Added a function `build_filtered_symbol_txt()` that generates `catalyst_news_{date}.FILTERED.txt` (symbols with score ≥ `--news-min-score`).
- Corrected the pipeline sequence: `topgappers → enrich_universe_catalyst → catalyst_filter → compose_universe_hybrid → run_day_catalyst`.
- Removed invalid argument errors by explicitly supporting the `--upstream-command` parameter (range runner metadata).
- Ensured compatibility with `--deny-negative` and `--exclude-china` for catalyst filtering, while omitting them from day-run arguments.

### 2. **Price Hygiene Update (`scanner.json`)**
- Updated minimum and maximum price filters:
  ```json
  {
    "price_min": 2.0,
    "price_max": 20.0
  }
  ```
  This excludes ultra-low-priced junk (pennies, warrants) that frequently cause poor fills or random reversals.

### 3. **Execution Testing Fixes**
- Patched multi-day range execution to accept metadata flags.
- Range runner no longer fails on `unrecognized arguments: --upstream-command`.
- Verified across full date range 2025-08-05 → 2025-08-31.

---

## 📊 Observed Problems (Post-Fix)

### 1. **Pipeline correctness restored but profitability low**
- The code is now logically correct (all score filters, catalysts, deny lists working).
- However, backtests over August 2025 show high win-rate volatility and flat/negative PnL.

### 2. **Root Causes Identified**
| Category | Description | Impact |
|-----------|--------------|---------|
| **Limited catalyst coverage** | Many days show `0 symbols met score threshold`. With score ≥ 3 and strict filters, there are often no A-grade names. | Missed trades → no opportunity |
| **Flat risk sizing** | All trades risk 35 USD regardless of quality (`tier=C risk_usd=35.00`). | Good setups under-sized, weak ones over-sized |
| **Sub-$2 stocks pre-fix** | Earlier versions allowed 1-dollar gappers (e.g. SWAG 1.69 USD, WKHS 1.74 USD). | Frequent instant reversals |
| **No adaptive response** | All environments treated equally (quiet vs. hot days). | Expectancy swings wildly |

---

## ✅ Fixes Implemented
1. **Compose alignment fix** → filtered list (score ≥ 3) correctly passed to day runner.
2. **Upstream argument handling** → range jobs complete without crash.
3. **Price floor 2 USD** → removes penny-stock noise.
4. **Verified range run** across 2025-08-05 → 08-31 shows clean logs.

---

## 🧮 Commands Executed

### Patch & Verification
```powershell
# Applied filtered compose patch
python scripts\run_catalyst_flow.py --date 2025-08-06 --scenario B --news-first --require-news --news-min-score 3 --top 3 --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15

# Patched to accept upstream arg
python -c "from pathlib import Path; import sys; p=Path('scripts/run_catalyst_flow.py'); s=p.read_text(); s=s.replace('ap = argparse.ArgumentParser()', 'ap = argparse.ArgumentParser()\n    ap.add_argument(\"--upstream-command\", nargs=\"+\", default=None, help=\"ignored upstream metadata\")'); p.write_text(s); print('patched')"

# Price hygiene update
python -c "import json; p='config\\scanner.json'; d=json.load(open(p)); d['price_min']=2.0; d['price_max']=20.0; json.dump(d,open(p,'w'),indent=2); print('price band -> 2–20 set')"

# Full August re-run
python scripts\run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B --news-first --require-news --news-min-score 3 --top 5 --enforce-band --band-min 8 --band-max 45 --min-rvol-open 1.8 --gate-minutes 15 --deny-negative --exclude-china --compare --compare-label B_profit_tune1
```

### Result Summary (Aug 05 → Aug 31 2025)
```
Trades = 16 | Wins = 5 | Losses = 11 | Win-Rate = 31.25 % | PnL = –244.25
```
**Good days:** Aug 05 (+27.78 MD), Aug 29 (+27.97 WOOF).  
**Loss clusters:** Aug 06–08 (ARDT / EHTH / ZETA / SOUN / SOUNW etc.).  
**Most days:** `0 symbols met score threshold` → no trades.

---

## 🚧 Current Limitations
- Score ≥ 3 combined with strict gap + RVOL filters leaves too few trades.
- Lack of dynamic sizing punishes expectancy.
- 0-symbol days reduce opportunity.

---

## 🧭 Next Steps

### Step 1 – Version Tagging
Tag this build before making behavioral changes.
```powershell
git add -A
git commit -m "v0.4.2: compose fix + price floor 2USD + stability checkpoint"
git tag -a v0.4.2 -m "Stable baseline; filtered compose, upstream accepted, hygiene applied"
git push && git push --tags
```

### Step 2 – Adaptive Sizing (planned)
Implement score/RVOL-weighted risk sizing to replace flat 35 USD per trade.
| Tier | Criteria | Risk USD |
|------|-----------|----------|
| A | score ≥ 3 and RVOL ≥ 2.6 | 50 USD |
| B | score ≥ 3 and RVOL 1.8–2.6 | 35 USD |
| C | else | 20 USD |

### Step 3 – Trade Management
- Break-even at +1 %, trail 0.5 % above that.
- Expected: –50 % smaller losses, higher expectancy.

### Step 4 – Momentum Context Filter
- Skip trading days where SPY < VWAP after 15 min or total top gappers < 5.

---

## 🧩 Expected Impact
| Update | Effect |
|---------|---------|
| Price floor 2 USD | Removes low-quality reversals |
| Adaptive sizing | Increases expectancy per trade |
| BE + trail logic | Cuts losses ~40 % |
| Momentum context | Skips low-volatility days |

---

**Checkpoint summary:**  
✅ Pipeline correct and stable.  
⚙️ Score ≥ 3 functioning.  
⚠️ Profitability pending (requires adaptive sizing + context filter).  
Next development version will build directly on **v0.4.2**.
