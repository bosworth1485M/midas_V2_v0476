# Midas_V2 — v0.3.45 Summary (Restored Hybrid + v44 Range Runner)
*Scope:* Lock the stable hybrid backtester, add the v44 range runner & analysis tools, and resume the **B** profitability push (tag after every tiny change).  
*Folder used for tests:* `midas_V2_v044_working` (worktree pinned to `v0.3.44-working` → commit `01e188b`).

---

## What went wrong (root cause)
- **main repointed to v0.3.44** (included engine edits) while configs/expectations weren’t aligned.
- **Config/engine drift**: code referenced `max_daily_loss` while configs/logs used `daily_max_loss` → `AttributeError` in `risk.py`.
- **Import source shift**: enforcing `$env:PYTHONPATH="src"` moved execution from an installed package to the repo code, exposing the mismatch.
- **Secrets not in git**: worktree lacked `.env` → Polygon 401 until copied.
- **PowerShell encoding**: using `>` saved UTF‑16; first copy of `run_catalyst_range_and_summarize.py` failed as non‑UTF‑8. Fixed via `-Encoding utf8`.

## What we restored & verified
- **Known-good hybrid backtester** via pinned worktree: tag `v0.3.44-working` @ `01e188b`.
- **.env copied** and **PYTHONPATH set** so Python uses repo code.
- **Added only the v44 range runner + tools** (kept stable engine):
  - `scripts/run_catalyst_range_and_summarize.py` (UTF‑8)
  - `scripts/check_comparison_metrics.py`
  - `scripts/analyze_compare_label.py`
- **Validated** hybrid on 2025‑08‑05 and ran **Aug‑05→07** and **Aug‑05→31** ranges (Top‑4, RVOL 1.8, gate 15). Bundles and label CSVs generated.

### Key evidence
- 2025‑08‑05: **3/0, +28.51**
- 2025‑08‑07: **4/0, +41.03**
- Range Aug‑05→31 (Top‑4, RVOL 1.8, gate 15): **used=19, WR=68.42%, PnL=−46.52** (drag day 08‑06; several 0‑used days).

---

## Exact commands we used

### Git / Worktree / Version restore
```powershell
git fetch --all --tags
git tag -f v0.3.44-working 01e188b
git worktree add ..\midas_V2_v044_working v0.3.44-working
```

### Enter working folder & ensure repo code is used
```powershell
cd ..\midas_V2_v044_working
$env:PYTHONPATH="src"; python -c "import midas_v2,inspect; print(inspect.getfile(midas_v2))"
```

### Copy secrets into worktree
```powershell
Copy-Item ..\midas_V2\.env .\.env -Recurse -Force
```

### Single-day hybrid smoke test (Aug‑05)
```powershell
$env:PYTHONPATH="src"; python scriptsun_catalyst_flow.py --date 2025-08-05 --scenario B --news-first --require-news --news-min-score 2 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15
```

### Bring in v44 range runner (UTF‑8) and verify
```powershell
git show v0.3.44:scripts/run_catalyst_range_and_summarize.py | Set-Content -Path .\scriptsun_catalyst_range_and_summarize.py -Encoding utf8
$env:PYTHONPATH="src"; python scriptsun_catalyst_range_and_summarize.py --help
```

### Multi-day probe (Aug‑05→07) with label
```powershell
$env:PYTHONPATH="src"; python scriptsun_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --require-news --news-min-score 2 --top 4 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 1.8 --gate-minutes 15 --compare --compare-label B_primary_top4_rvol18_g15
```

### Full August range (Aug‑05→Aug‑31)
```powershell
$env:PYTHONPATH="src"; python scriptsun_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B --news-first --require-news --news-min-score 2 --top 4 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 1.8 --gate-minutes 15 --compare --compare-label B_primary_top4_rvol18_g15
```

### Metrics & label analysis
```powershell
$env:PYTHONPATH="src"; python scripts\check_comparison_metrics.py

$env:PYTHONPATH="src"; python scriptsnalyze_compare_label.py --root .\out --pattern "202508*/_comparisons/comparison_*.json" --label B_primary_top4_rvol18_g15 --csv .\oututo_catalyst\label_B_primary_top4_rvol18_g15_Aug.csv

python scripts\show_latest_range.py
```

### Utility (UTF‑8 copying pattern from any tag)
```powershell
git show <tag>:path	oile | Set-Content -Path .\path	oile -Encoding utf8
```

---

## Create **v0.3.45** (Docs included)

> Run in the working folder `midas_V2_v044_working`

**Refresh Docs and include them:**
```powershell
$env:PYTHONPATH="src"; python Docsefresh_docs.py
git add Docs
```

**Stage runner + tools:**
```powershell
git add scriptsun_catalyst_range_and_summarize.py scripts\check_comparison_metrics.py scriptsnalyze_compare_label.py
```

**Commit + Tag (v0.3.45):**
```powershell
git commit -m "v0.3.45: stable hybrid backtester + v44 range runner + label/metrics tools + Docs"
git tag v0.3.45
git push && git push --tags
```

*(Optional) Release branch for 45:*
```powershell
git switch -c rel/v0.3.45
git push -u origin rel/v0.3.45
```

*(Optional) Merge into your normal repo’s `main` (from `..\midas_V2`):*
```powershell
git fetch --all --tags
git checkout main
git pull
git merge --no-ff origin/rel/v0.3.45 -m "Merge v0.3.45 (stable hybrid + v44 range runner + analysis + Docs)"
git push
```

---

## Roadmap to increase **B** profitability (tag every tiny change)

**Baseline again (Top‑3, RVOL 2.0, gate 15):**
```powershell
$env:PYTHONPATH="src"; python scriptsun_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --require-news --news-min-score 2 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --compare --compare-label B_top3_rvol20_g15
```

**Knob-by-knob probes (each one separately; commit+tag after):**
```powershell
# Tight list
... --top 2 --compare --compare-label B_top2_rvol20_g15
# Higher opening RVOL gate
... --min-rvol-open 2.2 --compare --compare-label B_top3_rvol22_g15
# Longer opening gate
... --gate-minutes 20 --compare --compare-label B_top3_rvol20_g20
# Stronger catalyst threshold
... --news-min-score 3 --compare --compare-label B_top3_score3_rvol20_g15
# Headline hygiene
... --deny-negative --exclude-china --compare --compare-label B_top3_rvol20_g15_deny
```

**Range confirm (Aug‑05→31) for any winning probe:**
```powershell
$env:PYTHONPATH="src"; python scriptsun_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B --news-first --require-news --news-min-score 2 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --compare --compare-label B_primary_top3_rvol20_g15
```

**Analyze & tag that improvement as v0.3.45-1 (or v0.3.46 if you prefer bumping):**
```powershell
$env:PYTHONPATH="src"; python scriptsnalyze_compare_label.py --root .\out --pattern "202508*/_comparisons/comparison_*.json" --label B_primary_top3_rvol20_g15 --csv .\oututo_catalyst\label_B_primary_top3_rvol20_g15_Aug.csv

git commit -am "v0.3.45-1: B_top3_rvol20_g15 probe + results"
git tag v0.3.45-1
git push && git push --tags
```

### Adaptive sizing plan (after baseline is solid)
- **Step A (enable simple throttles):** per‑trade risk cap (e.g., $50) and daily max loss ($1000) already effective; verify they’re applied in logs.
- **Step B (confidence-weighted sizing):** map higher‑quality setups (higher news score, stronger RVOL, green‑streak confirmation) to slightly larger size (e.g., 1.2×), keep losers at 1.0×.
- **Step C (drawdown throttle):** reduce size by 50% after 2 consecutive losses within a day; restore next day.
- **Step D (volatility adjustment):** scale shares by `1 / ATR_norm` (cap between 0.7× and 1.3×).  
- **Step E (router guard):** one position per symbol; no re‑entry on same ticker until outcome logged.
- **Each sub‑step gets its own tag:** `v0.3.45-sizeA`, `v0.3.45-sizeB`, etc.

---

## FAQ — When did **B profiles** start?
- **v0.3.43** introduced the **B profitability push** (adaptive sizing groundwork, “V2 sized profile”, profile runner), and 
- **v0.3.44** range runner added the explicit `--profile {B_profit_v1,B_profit_v2}` convenience flags for quickly swapping B presets.

---

## Pre‑flight checklist (repeat before runs)
- `$env:PYTHONPATH="src"` set **in this shell**.
- `.env` present; Polygon key loads.
- Config and engine names aligned (current working build OK).
- When copying files out of tags: **write with UTF‑8**.

*End of v0.3.45 summary*
