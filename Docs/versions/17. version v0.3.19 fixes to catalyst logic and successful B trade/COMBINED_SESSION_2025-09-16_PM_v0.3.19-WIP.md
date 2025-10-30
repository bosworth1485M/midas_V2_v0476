# Midas_V2 — Afternoon Session (Combined Report)
*(2025‑09‑16 PM, v0.3.19‑WIP)*

## Executive Summary
- Objective: make the catalyst flow simple and reliable using **A‑priority + B‑fill** (Top‑N=3), without touching keys.
- Baseline B (2025‑08‑05): **10 trades → TP=4, SL=6, Win% 40.0**.
- Catalyst B (2025‑08‑05, Top‑N=3): **picked MD** → **1 trade → TP=1, Win% 100.0**.
- Key changes:
  - **SAFE wrappers** added; subprocesses now set **PYTHONPATH=./src**.
  - `topgappers.py` default **min_gap=10%** (was 5%) for Cameron simplicity.
  - **Catalyst picker** hardened: A‑priority + B‑fill, robust CSV parsing (case‑insensitive headers, BOM/delimiter auto‑detect) and **news fallback** (uses per‑symbol `max(best_score)`).

## What We Did (in order, with exact commands)
1) **Baseline day — Scenario B (2025‑08‑05)**
````
python scripts/run_day_simple_SAFE.py --date 2025-08-05 --scenario B
python scripts/summarize_results.py --date 2025-08-05
````
Observed: header `min_gap=10.0%`; universe=36 symbols; results at `out\20250805\B\results_2025-08-05.csv`; **B: TP=4 SL=6 Win%=40.0**.

2) **Catalyst day — Scenario B (2025‑08‑05) — A‑priority + B‑fill, Top‑N=3**
````
python scripts/run_day_catalyst_SAFE.py --date 2025-08-05 --scenario B --topn 3 --min-grade 2 --allow-b-fill
python scripts/summarize_results.py --date 2025-08-05
````
Observed: `catalyst_scores_…` malformed (header parsed as `['MD']`), but news audit existed; picker debug:
``[PICKER] scores_headers=['MD'] rows_in_scores=0 news_symbols=1 min_grade=2 allow_b_fill=True -> picked=['MD']``
Universe: `data\universe_catalyst_2025-08-05.txt` contained **MD**; minutes fetched; **B: TP=1 SL=0 Win%=100.0**.

## Catalyst Selection — Process & Policy
**Process**
1. Build top‑gappers (`topgappers.py`) → `data/samples/universe_sample.txt` (price 1–20, **gap ≥10%**).
2. Enrich catalysts (`enrich_universe_catalyst.py --in … --out …`) →
   - `out/<YYYYMMDD>/catalyst/catalyst_scores_<DATE>.csv` (symbol scores),
   - `out/<YYYYMMDD>/catalyst/catalyst_news_<DATE>.csv` (news audit).
3. Picker (SAFE): read **scores**; if empty/zero, **promote** via news audit `max(best_score)`;
4. **A‑priority + B‑fill**: take A’s (score ≥2) first; B’s (score =1) only if `--allow-b-fill`;
5. Safety net: if still empty but rows exist, pick top few by score; write universe + audit; run and summarize.

**Defaults now**
- Top‑N = **3**; A‑priority; **B‑fill** allowed; confirms on (EMA + VWAP + MACD); later we can add an **opening RVOL gate (≥1.5)**.

## Catalyst CSVs — What’s Inside
**A) `catalyst_scores_<DATE>.csv` (symbol scores, primary)**
- Columns (case‑insensitive): `symbol`/`ticker`, `score`/`catalyst_score`, optional `grade` (derived: A if ≥2; B if =1; else 0).
- Today’s issue: parsed header as `['MD']` → **0 usable rows**; picker’s robust reader + news fallback handled it.

**B) `catalyst_news_<DATE>.csv` (news audit, fallback + debugging)**
- Columns (case‑insensitive): `symbol`/`ticker`, **`best_score`** (or `score`), `count`, `title`, `published`.
- Note: **`count` ≠ score**; we rely on **`best_score`** for fallback.

## Problems & Fixes
1) `midas_v2.cli` not found → **Fix:** SAFE wrappers set **PYTHONPATH=./src** for subprocesses.
2) `--in/--out` and `--universe` args missing → **Fix:** wrapper now passes required arguments.
3) Scanner too loose (5%) → **Fix:** default **min_gap=10%**.
4) Early empty‑pick bug despite B‑fill → **Fix:** corrected A‑priority + B‑fill; added safety net.
5) Malformed symbol‑scores CSV → **Fix:** robust CSV reader + **news fallback** to avoid dropping catalysts.
6) YMAB confusion → news shows `count=3` but **`best_score=0`**, so not A/B; correctly excluded. MD had **best_score=1** (B‑grade) and was picked.

## Files Written (Aug‑05)
- `data\samples\universe_sample.txt` (36 symbols, 10% gap)
- `out\20250805\B\results_2025-08-05.csv` (baseline)
- `out\20250805\catalyst\catalyst_scores_2025-08-05.csv` (malformed in this run)
- `out\20250805\catalyst\catalyst_news_2025-08-05.csv` (news audit; MD best_score=1, YMAB best_score=0)
- `out\20250805\catalyst\catalyst_universe_2025-08-05.csv` (audit)
- `data\universe_catalyst_2025-08-05.txt` (final Top‑N universe)

## Results (Aug‑05)
- **Baseline B**: **TP=4, SL=6 → Win% 40.0**
- **Catalyst B (Top‑N=3)**: **MD picked** → **TP=1, SL=0 → Win% 100.0**

## Next Steps (one step at a time)
1) Aug‑06 baseline then catalyst (Top‑N=3) and compare:
````
python scripts/run_day_simple_SAFE.py --date 2025-08-06 --scenario B; python scripts/summarize_results.py --date 2025-08-06
python scripts/run_day_catalyst_SAFE.py --date 2025-08-06 --scenario B --topn 3 --min-grade 2 --allow-b-fill; python scripts/summarize_results.py --date 2025-08-06
````
2) If catalyst wins again, keep **Top‑N=3**; later add opening **RVOL gate ≥1.5**.

## Commit Snippet (PowerShell)
````
git add .\scripts\run_day_simple_SAFE.py .\scripts\run_day_catalyst_SAFE.py .\scripts\topgappers.py
git commit -m "PM: SAFE wrappers + PYTHONPATH; catalyst picker robust CSV + news fallback; min_gap=10%; Aug-05 catalyst B: MD TP=1"
````