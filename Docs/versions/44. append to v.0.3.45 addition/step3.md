## v0.3.45-step3 — 2025-10-06
**Change:** Range provenance wired.  
- `scripts/run_catalyst_flow.py` accepts `--upstream-command` and passes it to `write_compare_bundle.py`.  
- `scripts/run_catalyst_range_and_summarize.py` now forwards its full CLI via `--upstream-command` to each day’s flow.

**Why:** Full reproducibility; comparison JSON now records the **top-level range command** in `provenance.upstream_command`.

**Verification:** 2025-08-05→2025-08-07 (B, newsOnly + Top-3, band 10–40, RVOL 2.0, gate 15) ran clean; per-day bundles include `provenance.upstream_command`.  
**Output:** `out\20250805\_comparisons\comparison_*.json`, `out\20250806\_comparisons\comparison_*.json`, `out\20250807\_comparisons\comparison_*.json` (newest files).

**Command used:**  
`python scripts\run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --require-news --news-min-score 2 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --deny-negative --exclude-china --compare --compare-label B_top3_rvol2_g15_step3test`