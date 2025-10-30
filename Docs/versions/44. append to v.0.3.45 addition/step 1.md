git tag -a v0.3.45-step1-ok -m "Step 1: write_compare_bundle.py adds metrics+provenance; verified on 2025-08-05 (B) WR=100% TP/SL=3/0 PnL=28.51"
git push --tags

echo "$(Get-Date -Format 'yyyy-MM-dd HH:mm') | v0.3.45-step1-ok | write_compare_bundle.py: metrics+provenance; verified 2025-08-05 (B) WR=100% TP/SL=3/0 PnL=28.51" >> Docs\CHANGELOG.md
git add Docs\CHANGELOG.md; git commit -m "log: v0.3.45-step1-ok"; git push

2025-10-06 12:40 | v0.3.45-step1b | run_catalyst_flow -> passes --upstream-command to write_compare_bundle; provenance now shows top-level CLI. Verified 2025-08-05 (B): WR=100% TP/SL=3/0 PnL=28.51.

## v0.3.45 additions — Step 1 (2025-10-06)
**Change:** `scripts/write_compare_bundle.py` now writes guaranteed **metrics** (Used/WR%/TP/SL/PnL) with **robust fallbacks**, plus a **provenance** block (`command_used`, cwd, python, platform, timestamp).  
**Why:** eliminate “NULL metrics” and make runs reproducible/auditable.  
**Regression evidence:**  
- 2025-08-05 (B, newsOnly+Top-3, band 10–40, RVOL 2.0, gate=15): **WR 100%**, TP/SL 3/0, **PnL 28.51** (see `out\20250805\_comparisons\comparison_*.json`).  
- 2025-08-06 (B) shows expected negative case coverage; metrics populate reliably.  
- 2025-08-07 (B) shows positive cases; metrics populate reliably.  
**Key output:** JSON now includes `"provenance": { "command_used": "… write_compare_bundle.py …" }`.  
**Status:** ✅ Applied.

### Next (Step 1b – planned)
Wire **top-level runner CLI** into the bundle by passing  
`--upstream-command "python scripts\run_catalyst_flow.py …"`  
from `run_catalyst_flow.py` when it calls `write_compare_bundle.py`.  
**Result:** JSON will also show `"upstream_command": "python scripts\run_catalyst_flow.py …"`.

### Baseline commands used
- Single-day check:  
  `python scripts\run_catalyst_flow.py --date 2025-08-05 --scenario B --news-first --require-news --news-min-score 2 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --deny-negative --exclude-china --compare --compare-label B_top3_rvol2_g15`
- Metrics sanity:  
  `python scripts\check_comparison_metrics.py`

### Tag/checkpoint
- `v0.3.45-step1-ok` – write_compare_bundle metrics+provenance working.
- (Planned) `v0.3.45-step1b` – `run_catalyst_flow.py` passes `--upstream-command`.