# Midas_V2 — v0.3.46 Profit Guard (Release Notes & Quick Commands)

**Date:** 2025-10-07  
**Scope:** Scenario **B** (news-only, score ≥ 3), strict profit-first baseline with small guardrails.

---

## 1) What we fixed

- **Polygon auth:** Moved news fetch to **Authorization: Bearer** (matches your working scanner).
- **Scoring:** Earnings headlines now boost to **score=3** if they include **“Jumps ≥ 20%”**, **“Tops by …”**, or similar positive “beats” semantics.  
  *We now write the **boosted** `score` to the canonical CSV and **preserve** it in the filtered CSV.*
- **Selection policy (strict):** `--require-news --news-min-score 3` (trade only high-conviction catalysts).
- **Profit guards:** **Top-2**, **RVOL ≥ 2.4**, **gate = 20** to avoid early chop and weaker opens.
- **Viewers:** Confirmed Python-only flow works (`check_comparison_metrics.py`, `scan_run_bundles.py`, `show_latest_range.py`).

---

## 2) Results snapshot (Aug-05 → Aug-07, Scenario B)

### Strict baseline (Top-3, RVOL 2.0, gate 15) — for reference
- Trades: **7** · **WR 57.14%** · **PnL −50.09** (08-06 dragged)

### Profit Guard (Top-2, RVOL 2.4, gate 20) — **current baseline**
- **Totals:** Trades **5** · **WR 60.00%** · **PnL +3.33**
- **Per-day**
  - 2025-08-05: **+15.96** (TP/SL **1/0**)
  - 2025-08-06: **+11.16** (TP/SL **1/1**)
  - 2025-08-07: **−23.79** (TP/SL **1/1**)

**Conclusion:** Profit guards flipped the 3-day from negative to **positive** while keeping score≥3 strictness.

---

## 3) Exact test commands we used

### (A) Range runs

**Strict baseline (for reference)**
```powershell
python scripts\run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --require-news --news-min-score 3 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --deny-negative --exclude-china --compare --compare-label B_top3_score3_g15_rvol2_authFix
```

**Profit guard v1 (Top-2, RVOL 2.2, gate 20)**
```powershell
python scripts\run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --require-news --news-min-score 3 --top 2 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.2 --gate-minutes 20 --deny-negative --exclude-china --compare --compare-label B_top2_score3_g20_rvol22_authFix
```

**Profit guard v2 (Top-2, RVOL 2.4, gate 20) — *current best***
```powershell
python scripts\run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --require-news --news-min-score 3 --top 2 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.4 --gate-minutes 20 --deny-negative --exclude-china --compare --compare-label B_top2_score3_g20_rvol24_authFix
```

### (B) Write per-day comparison bundles (so viewers see latest)

```powershell
python scripts\write_compare_bundle.py --date 2025-08-05 --scenario B --summary out\20250805\B_hybrid\summary_hybrid_2025-08-05.txt --universe data\catalyst\universe_hybrid_2025-08-05.txt --catalyst-csv data\catalyst\catalyst_news_2025-08-05_filtered.csv --out-dir out\20250805\_comparisons --label B_top2_score3_g20_rvol24_authFix
python scripts\write_compare_bundle.py --date 2025-08-06 --scenario B --summary out\20250806\B_hybrid\summary_hybrid_2025-08-06.txt --universe data\catalyst\universe_hybrid_2025-08-06.txt --catalyst-csv data\catalyst\catalyst_news_2025-08-06_filtered.csv --out-dir out\20250806\_comparisons --label B_top2_score3_g20_rvol24_authFix
python scripts\write_compare_bundle.py --date 2025-08-07 --scenario B --summary out\20250807\B_hybrid\summary_hybrid_2025-08-07.txt --universe data\catalyst\universe_hybrid_2025-08-07.txt --catalyst-csv data\catalyst\catalyst_news_2025-08-07_filtered.csv --out-dir out\20250807\_comparisons --label B_top2_score3_g20_rvol24_authFix
```

### (C) View results — Python only

**Range totals (latest CSV)**
```powershell
python scripts\show_latest_range.py
```

**Per-day roll-up (from bundles)**
```powershell
python scripts\check_comparison_metrics.py
```

**Label-filtered 3-day scan**
```powershell
python scripts\scan_run_bundles.py --dates 2025-08-05,2025-08-06,2025-08-07 --scenario B --labels B_top2_score3_g20_rvol24_authFix --dedupe-latest --per-day
```

---

## 4) Next steps to increase profitability

**Micro-tunes (one at a time; keep if totals improve):**
- **Timing**: `--gate-minutes 25` (skip more open noise).  
- **Demand**: `--min-rvol-open 2.6` (only stronger opens).  
- **(Optional)** Tighten **Top-N** to **Top-1** on choppy days.

**Profit protection (no selection change):**
- Partial at **+1.0%**, move stop to **BE**; optional **time stop** at **2–3 min** if no progress.

**Adaptive sizing (Kelly-lite, capped) — v0.3.47 target:**
- Tiered sizes by signal strength (e.g., score 3 + “beats/tops” + big % → **1.25×**, plain score 3 → **1.0×**).  
- Guardrails: per-trade risk cap (e.g., **$50**), daily max loss (**$1,000**), drawdown throttle (reduce size after −2R day).  
- Implementation: add a simple `sizer.py` and config switch (e.g., `risk.sizer="tiered"`); log size & R per trade.

**Validation plan:**
- Run **Aug-01→Aug-31** with the chosen profile; then **July**.  
- Keep tagging each green checkpoint before changing parameters.

---

## 5) GitHub – create **v0.3.46**

```powershell
git add -A
git commit -m "v0.3.46: Scenario B profit-guard (score>=3 + Top-2 + RVOL>=2.4 + gate=20) + Bearer auth + boosted scoring + viewers ok"
git tag -a v0.3.46 -m "Scenario B profit-guard baseline"
git push
git push --tags
```
