## v0.3.45-step1b — 2025-10-06
**Change:** `scripts/run_catalyst_flow.py` now passes `--upstream-command` into `write_compare_bundle.py`, so comparison JSON includes `provenance.upstream_command`.  
**Why:** Full reproducibility/audit — records the exact top-level CLI used.  
**Verification:** 2025-08-05 (B) re-run OK (WR 100%, TP/SL 3/0, PnL 28.51). New JSON shows the field:
`"upstream_command": "python scripts\\run_catalyst_flow.py --date 2025-08-05 ... --compare --compare-label B_top3_rvol2_g15_cmdwire"`  
**Output:** `out\20250805\_comparisons\comparison_*.json` (newest file).  
**Command used:**  
`python scripts\run_catalyst_flow.py --date 2025-08-05 --scenario B --news-first --require-news --news-min-score 2 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --deny-negative --exclude-china --compare --compare-label B_top3_rvol2_g15_cmdwire`