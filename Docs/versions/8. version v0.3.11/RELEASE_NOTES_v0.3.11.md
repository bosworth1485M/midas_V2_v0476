# Midas_V2 — v0.3.11 (Release Notes)
**Date:** 2025-09-09

## Summary
- Clarified and locked config source to **JSON** (`config/scenarios.json`) for this repo; eliminated confusion with the abandoned TOML project.
- Added **`scripts/preflight_project_guard.py`** to print branch/tag, `scenarios.json` SHA and D/E keys, `.env` booleans, and key-script presence before runs.
- Confirmed **elegant non‑trading‑day handling** remains in place: holidays/weekends skip cleanly with INFO messages.
- Confirmed **Polygon auth** stable (Authorization: Bearer + sanitized key; `.env` override=True).
- September (1→9) smoke: D/E produced **0 trades** (strict guards); pipeline stable. August D baseline remains **WR 63.29%**, **+167.57 PnL**.

## What changed in this version
- **New:** `scripts/preflight_project_guard.py` (Windows‑friendly). Shows the live D/E config values so runs are reproducible.
- **Docs:** v0.3.10 materials updated; v0.3.11 notes created.
- **No strategy/entry logic changed**; this version focuses on correctness, environment clarity, and test flow.

## How to run (quick)
```bat
# 1) Preflight sanity
python scripts\preflight_project_guard.py

# 2) Single day
python scripts\run_day_simple.py --date 2025-09-02 --scenario D
python scripts\view_results.py --date 2025-09-02 --scenario D --preview 20 --top 5

# 3) Small September window (to last available day)
python scripts\run_range_and_summarize.py --start 2025-09-01 --end 2025-09-09 --scenario D
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250901_20250909_D.csv
```

## Next steps (to push WR > 60% and increase PnL)
- Measure **July** D/E to confirm where D struggled; compare with E.
- If months are quiet: minimally loosen guards in JSON (already applied for D/E), then A/B:
  - **Universe hygiene ON** (drop warrants/units/leveraged ETFs),
  - **Opening RVOL gate ON** (first 10–15m vs prior day ≥ 1.5).
- Prefer **D+E** together for mixed regimes; router and sizing later.

## Tagging
```bat
git tag -a v0.3.11 -m "v0.3.11: preflight guard; JSON config clarity; smoke stable; plan to push WR>60%"
git push --tags
```
