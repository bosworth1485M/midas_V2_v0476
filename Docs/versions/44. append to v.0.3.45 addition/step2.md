## v0.3.45-step2 — 2025-10-06
**Change:** `scripts/scan_runs_simple.py` now prints key flags (newsOnly/newsFirst, Top-N, band, RVOL, gate, score) and falls back to the summary text when JSON metrics are missing.  
**Why:** Faster review of ranges + resilient metrics display.  
**Verification:** 2025-08-05→2025-08-07 (B) shows correct TP/SL, WR%, PnL and profiles.  
**Outputs:** Console table; optional CSV/MD via `--write`.
**Command used:** `python scripts\scan_runs_simple.py --start 2025-08-05 --end 2025-08-07 --scenarios B`