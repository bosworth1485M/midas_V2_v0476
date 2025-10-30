# Midas_V2 — v0.3.8-2025-09-07-envfix (Release Notes)
**Date:** 2025-09-07  
**Scope:** Stable fixes for `.env` loading and `PYTHONPATH` for reliable runner behavior.

---

## Summary
This version locks in the environment/bootstrap improvements on the 0.3.6 line and confirms prior trading-day gap logic. It keeps runtime behavior the same while removing shell-setup friction.

---

## Changes
- **`.env` auto-load (project root):** Runners call `python-dotenv` to load `ROOT/.env` at startup.
- **Import path fix:** `src/` is injected into `sys.path` and propagated via `PYTHONPATH` to child processes (so `python -m midas_v2.cli ...` works).
- **Files updated:**
  - `scripts/run_day_simple.py` — bootstrap + child env propagation; summary auto-save.
  - `scripts/topgappers.py` — bootstrap; keeps `prev_trading_day_polygon.py` for prior trading day.
  - `scripts/fetch_minutes_polygon.py` — bootstrap; logic unchanged.

> Range runners (`run_range_and_summarize.py`, `run_range_safe.py`) remain unmodified; they can receive the same bootstrap later without behavior changes.

---

## Verification

### Single-day checks
- **2025-08-05 D** — CSV and summary written under `out\20250805\D\`.
- **2025-09-02 D/E** — D: 3 trades, 0 TP, TotalPnL -30.79; E: 10 trades, 4 TP, TotalPnL -24.18.

### August regression (Scenario D, 2025-08-05 → 2025-08-31)
- **Total trades:** 79  
- **Wins / Losses:** 50 / 29  
- **Win rate:** **63.29%**  
- **Total PnL:** **+167.57**  
- Best Day: 2025-08-06 (+174.33, 38 trades, WR 65.79%)  
- Worst Day: 2025-08-05 (-19.39, 3 trades, WR 0.00%)

---

## How to reproduce (pure Python)

### Single day
```bat
python scripts\run_day_simple.py --date 2025-08-05 --scenario D
python scripts\summarize_results.py --date 2025-08-05
python scripts\view_results.py --date 2025-08-05
```

### August range (Scenario D)
```bat
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario D
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250805_20250831_D.csv
```

---

## Notes
- `.env` stays local; not tracked by Git. Keeping a `.env.bak` copy in the root is recommended.
- `topgappers.py` computes gaps vs the **previous trading day** (weekends/US holidays handled).

---

## Historical context
- `v0.3.7-cleanup` intentionally removed several legacy scripts; this release continues from the **0.3.6** line with all required runners present.
