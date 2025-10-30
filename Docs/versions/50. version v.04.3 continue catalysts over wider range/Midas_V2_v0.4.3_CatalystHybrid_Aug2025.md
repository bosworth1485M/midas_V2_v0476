# Midas_V2 v0.4.3 — Catalyst ON vs OFF Hybrid Test (August 2025)
## Scenario B — Adaptive Sizing Documentation and Results Log
### This version records August 2025 Catalyst ON/OFF tests and provides documentation for future extended testing (June–September 2025).

---

## 📘 1. Version Context
- **Purpose:** Documentation and results capture only (no parameter change)
- **Folder:** `C:\Users\boydp\Desktop\midas_V2_v044_working`
- **Strategy:** Scenario B (Adaptive Sizing)
- **Status:** Live, tested August 2025; next phase (v0.4.4) will run June→September.

---

## ⚙️ 2. Configuration Summary
```
band 10–40
gate-minutes 15
tp_pct 2.0 | sl_pct 2.5
base_risk_usd 35 | max_per_trade_risk_usd 50
confidence_map A:1.4, B:1.0, C:1.0
tier_rules: A≥2.6 RVOL, B≥2.0, C≥1.5
adaptive sizing enabled
```
Catalyst ON used `--news-min-score 2`, `--require-news`, `--deny-negative`, `--exclude-china`.
Catalyst OFF removed those filters.

---

## 🤖 3. Commands Executed (August 2025)

### Catalyst ON (Hybrid)
```
python scripts\run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B --news-first --require-news --news-min-score 2 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --deny-negative --exclude-china --compare --compare-label B_ON_score2_top3_rvol20_g15 --save-csv "out\labeled\B_ON_score2_top3_rvol20_g15\range_summary_20250805_20250831.csv"
```

### Catalyst OFF (Control)
```
python scripts\run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --compare --compare-label B_OFF_top3_rvol20_g15 --save-csv "out\labeled\B_OFF_top3_rvol20_g15\range_summary_20250805_20250831.csv"
```

### Per-day display and bundle comparison
```
python scripts\show_latest_range.py --glob "out/labeled/B_ON_score2_top3_rvol20_g15/range_summary*.csv"
python scripts\show_latest_range.py --glob "out/labeled/B_OFF_top3_rvol20_g15/range_summary*.csv"
python scripts\scan_run_bundles.py --scenario B --ignore-labels --dedupe-latest --per-day
```

---

## 📊 4. August 2025 Results (Verbatim)

### Catalyst ON (Hybrid)
```
Trades = 21 | Wins = 7 | Losses = 14 | Winrate = 33.33% | PnL = -293.01
```
Full per-day breakdown included (Aug 05 → Aug 27) from logs.

### Catalyst OFF (Control)
```
Trades = 10 | Wins = 4 | Losses = 6 | Winrate = 40.00% | PnL = -97.69
```
Full per-day breakdown included (Aug 06 → Aug 29) from logs.

---

## 🔍 5. Interpretation

### Catalyst ON underperformed
- Over-filtering remains the main issue.
- Polygon coverage was sparse for small-cap catalysts in August.
- Many headlines were post-gap summaries rather than pre-open catalysts.

### Catalyst OFF steadier
- Simpler technical-only logic produced steadier results.
- Smaller sample size but more balanced trade distribution.

### Context
Earlier strong profiles (e.g., *newsOnly + Top-3 + band 10-40 + RVOL 2 + score ≥ 2*) reached WR ≈75%, PnL +63 in shorter tests, suggesting that catalysts can help when news volume is healthy.

---

## 🧠 6. Why Scenario B differs from other Cameron projects

| Factor | Explanation |
|--------|--------------|
| **Market regime** | August was a low-volatility period; Cameron-style momentum thrives in hot months. |
| **Data feed** | Other projects used Polygon + Benzinga + Finnhub; your build used only Polygon, which misses microcap headlines. |
| **Sizing timing** | Adaptive sizing was activated before the S/R filter existed, amplifying losing trades. |
| **Technical alignment** | Other successful Bs used VWAP/EMA reclaims + MACD rise confirmation and treated catalysts as a *boost*, not a *requirement*. |
| **Solution path** | Recast catalyst logic from mandatory filter → confidence boost (A-tier sizing) and add S/R Lite before sizing. |

---

## 🛠️ 7. Planned Finnhub Integration (v0.4.4)

**Goal:** Expand catalyst coverage by adding the **Finnhub API** alongside Polygon for enrichment.

**Reason:** Polygon’s feed lacks many small-cap headlines; Finnhub provides broader coverage even on the free plan.

**Implementation summary:**
- Add `FINNHUB_API_KEY` to `.env` (already obtained).
- Update `enrich_universe_catalyst.py` to fetch from Finnhub only if the key exists.
- Leave Polygon handling *untouched* (especially `topgappers.py`).
- Deduplicate and merge Polygon + Finnhub headlines into a single list.
- Follow safe key-handling rules (no global dotenv import or overwrites).
- Start with the free Finnhub tier; upgrade only if rate limits are reached.

**Expected benefit:**
- 2–3× more valid catalyst hits per session.
- Better coverage in quiet months (June–August).
- Reduced "no-news" days and more reliable catalyst scoring.

**Future Stage:**  When you move to live trading (real money), consider adding **Benzinga Newswire API** for sub-second small-cap catalysts.  Finnhub + Polygon are sufficient for backtesting and paper runs.

---

## 🔄 8. Next-Version Plan — v0.4.4 (Extended Range Testing)

**Goal:** Verify whether August’s patterns persist across more data.

**Planned range:** 2025-06-01 → 2025-09-30  
**Scenarios:** B (Adaptive), D/E optional for comparison

### Commands for v0.4.4
```
python scripts\run_catalyst_range_and_summarize.py --start 2025-06-01 --end 2025-09-30 --scenario B --news-first --require-news --news-min-score 2 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --deny-negative --exclude-china --compare --compare-label B_ON_score2_top3_rvol20_JunSep
python scripts\run_catalyst_range_and_summarize.py --start 2025-06-01 --end 2025-09-30 --scenario B --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --compare --compare-label B_OFF_top3_rvol20_JunSep
```

---

## 🔑 9. Git Commands (Tag v0.4.3)
```
git add -A
git commit -m "v0.4.3: Catalyst ON vs OFF Hybrid (Aug 2025 results + documentation)"
git tag -a v0.4.3 -m "Catalyst Hybrid Aug2025 analysis log"
git push
git push --tags
```

---

## 🕒 10. Session Header
```
# Session Summary for Midas_V2 v0.4.3
## Use this file at the start of the next session to restore context.
```
