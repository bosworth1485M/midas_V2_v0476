# Midas_V2 — v0.3.10 (Release Notes)
**Date:** 2025-09-09

## Summary
- Elegant handling of **non‑trading days** (holidays/weekends): `topgappers.py` writes an empty universe; `run_day_simple.py`/minutes gracefully **skip** with clear INFO messages (no failures).
- New **regression smoke test**: `scripts/regression_smoke_v1.py` (streams live output). Checks non‑trading days, a single‑day sanity run, and a small range + analyzer.
- Polygon callers aligned on **Authorization: Bearer <key>** with **sanitized key** loading (`.env` override=True). **No scenario/strategy logic changed.**

## Files updated
- `scripts/topgappers.py`: header auth + empty‑universe write on non‑trading days.
- `scripts/prev_trading_day_polygon.py`: header auth; original “resultsCount>0” logic retained.
- `scripts/fetch_minutes_polygon.py`: header auth; **skip** when universe is empty/missing.
- `scripts/run_day_simple.py`: prints universe count; shows INFO skip on non‑trading days.
- `scripts/regression_smoke_v1.py`: new helper (non‑trading days + single day + small range).

## Verification
- **Holiday/weekend:** 2025‑09‑01, 2025‑09‑06, 2025‑09‑07 → skip cleanly (no failures).
- **August D** (reference): WR **63.29%**, PnL **+167.57** (unchanged baseline).
- **September D (through 2025‑09‑09):** 0 trades (strict guards) → pipeline stable.

## How to run
```bat
# Single day
python scripts\run_day_simple.py --date 2025-09-02 --scenario D
python scripts\view_results.py --date 2025-09-02 --scenario D --preview 20 --top 5

# Small range (Sep 1 → 9)
python scripts\run_range_and_summarize.py --start 2025-09-01 --end 2025-09-09 --scenario D
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250901_20250909_D.csv

# Regression smoke test
python scripts\regression_smoke_v1.py
```

## Tagging
```bat
git tag -a v0.3.10 -m "v0.3.10: non-trading-day handling + regression smoke test; auth fixes"
git push --tags
```

## Notes
- `.env` remains local; scripts load it automatically (override=True).
- Future dates will not have grouped data; ranges should stop at the last available trading day.
