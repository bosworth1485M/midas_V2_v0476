# Midas Backtesting — Complete Commands Reference (v1.2)

## Revision History
- 2025-09-21  **v1.2** — Add **Catalyst workflow** commands + examples; fix path typos.
- 2025-09-21  **v1.1** — Added revision list; appended docs refresh + clear_out sections; fixed analyzer paths.
- 2025-09-21  **v1.0** — Initial dated commands reference (Aug-05..Aug-31, 2025).

---

## Range Runs (August 2025)
```powershell
# B — full universe
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B

# B — Top-12 per day
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B --top 12

# D — Top-12 per day
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario D --top 12

# E — Top-12 per day
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario E --top 12

# Multi-scenario (comma-separated)
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B,D,E --top 12
```

## Single-Day Runs (August 2025)
```powershell
# Best day probe (Aug-13)
python scripts\run_day_simple.py --date 2025-08-13 --scenario B
python scripts\run_day_simple.py --date 2025-08-13 --scenario B --top 12
python scripts\run_day_simple.py --date 2025-08-13 --scenario D --top 12
python scripts\run_day_simple.py --date 2025-08-13 --scenario E --top 12

# Volatile day probe (Aug-07)
python scripts\run_day_simple.py --date 2025-08-07 --scenario B
python scripts\run_day_simple.py --date 2025-08-07 --scenario B --top 12
python scripts\run_day_simple.py --date 2025-08-07 --scenario D --top 12
python scripts\run_day_simple.py --date 2025-08-07 --scenario E --top 12

# Additional spot checks
python scripts\run_day_simple.py --date 2025-08-05 --scenario B --top 12
python scripts\run_day_simple.py --date 2025-08-06 --scenario B --top 12
python scripts\run_day_simple.py --date 2025-08-08 --scenario B --top 12
```

## Analyzers & Summaries
```powershell
# Quick sanity (latest summary)
python scripts\show_latest_range.py

# Analyze range CSVs (Aug-05..Aug-31)
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250805_20250831_B.csv
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250805_20250831_D.csv
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250805_20250831_E.csv

# Rebuild summaries, then re-analyze
python scripts\rebuild_range_summary.py --start 2025-08-05 --end 2025-08-31 --scenarios B D E
```

## Paths (Output)
```text
# Per-day trades CSV
out\YYYYMMDD\<SCENARIO>\results_YYYY-MM-DD.csv

# Per-day summary (text)
out\YYYYMMDD\<SCENARIO>\summary_YYYY-MM-DD.txt

# Range summary CSVs (Aug-05..Aug-31 examples)
out\auto\range_summary_20250805_20250831_B.csv
out\auto\range_summary_20250805_20250831_D.csv
out\auto\range_summary_20250805_20250831_E.csv
```

## Optional Utilities (Direct)
```powershell
# Build universe directly (preview + write Top-12)
python scripts\topgappers.py --date 2025-08-13 --top 12

# Fetch minutes directly (RTH session)
python scripts\fetch_minutes_polygon.py --date 2025-08-13 --session rth
```

---

# Catalyst Workflow (commands & examples)

## 1) Build a Catalyst Universe (news scoring + audit)
> Uses Polygon news to score symbols and writes an explicit **catalyst universe** + an audit CSV.
```powershell
# Example (Aug-05) — write a scored universe + audit
python scripts\enrich_universe_catalyst.py --date 2025-08-05 --limit 50 --out data\catalyst\catalyst_universe_2025-08-05.txt

# Audit output (per-day news list / scores)
# (path may vary slightly by repo version)
out\20250805\catalyst\catalyst_news_2025-08-05.csv
```

## 2) Run a Day using the Catalyst Universe
> Runs your normal backtest but **feeds the catalyst universe** instead of the generic list.
```powershell
# Scenario B with catalyst universe (Aug-05)
python scripts\run_day_catalyst.py --date 2025-08-05 --scenario B --universe data\catalyst\catalyst_universe_2025-08-05.txt

# (Optional) also force minute fetch for that day
python scripts\run_day_catalyst.py --date 2025-08-05 --scenario B --universe data\catalyst\catalyst_universe_2025-08-05.txt --fetch-minutes rth
```

## 3) Suggested Catalyst Test Days (August 2025)
```powershell
# Day 1
python scripts\enrich_universe_catalyst.py --date 2025-08-05 --limit 50 --out data\catalyst\catalyst_universe_2025-08-05.txt
python scripts\run_day_catalyst.py --date 2025-08-05 --scenario B --universe data\catalyst\catalyst_universe_2025-08-05.txt

# Day 2
python scripts\enrich_universe_catalyst.py --date 2025-08-06 --limit 50 --out data\catalyst\catalyst_universe_2025-08-06.txt
python scripts\run_day_catalyst.py --date 2025-08-06 --scenario B --universe data\catalyst\catalyst_universe_2025-08-06.txt

# Day 3
python scripts\enrich_universe_catalyst.py --date 2025-08-07 --limit 50 --out data\catalyst\catalyst_universe_2025-08-07.txt
python scripts\run_day_catalyst.py --date 2025-08-07 --scenario B --universe data\catalyst\catalyst_universe_2025-08-07.txt
```

## 4) Catalyst Outputs to Look For
```text
# Per-day audit (kept for review)
out\YYYYMMDD\catalyst\catalyst_news_YYYY-MM-DD.csv

# Normal per-day results & summary are still written under the scenario folder, e.g.:
out\YYYYMMDD\B\results_YYYY-MM-DD.csv
out\YYYYMMDD\B\summary_YYYY-MM-DD.txt
```

---

## Docs Refresh (how / why / outputs)
```powershell
# PowerShell (if present)
.\Docs\Refresh-Docs.ps1

# Python (alternative)
python Docs\refresh_docs.py
```
**Purpose:** regenerate project documentation from current code/config state so your guides don’t drift.  
**Typical outputs (in `Docs\`):**
- `USER_GUIDE.md` — end‑user “how to run” guide (commands, paths, examples).
- `DEV_GUIDE.md` — developer guide (scenarios, parameters, runners, data flow).
- `SCRIPTS_INDEX.md` — quick index of scripts with one‑line purpose notes.
- `versions\<timestamp or tag>\` — optional snapshots (MD/PDF) if your generator supports it.  
*Note:* exact filenames may vary slightly by repo version; run with `--help` if available.

## Cleanup — `clear_out.py` (safe use)
```powershell
# See available flags
python scripts\clear_out.py --help

# Examples (adjust to your script’s --help)
# Remove auto range summaries only (if supported)
python scripts\clear_out.py --auto-only

# Remove a specific day (if supported)
python scripts\clear_out.py --date 2025-08-13

# Remove a date range (if supported)
python scripts\clear_out.py --start 2025-08-05 --end 2025-08-31
```
**Purpose:** remove old per‑day outputs and auto summaries under `out\` to ensure clean reruns.  
**Safe procedure:**
1. Back up: rename `out\` to `out_backup_YYYYMMDD` (so nothing is lost).  
2. Use `clear_out.py` for targeted deletes (e.g., days, scenarios) if flags are available.  
3. Recreate fresh outputs by rerunning your range/day commands.  

**Manual fallback (if flags aren’t supported):**
```powershell
ren out out_backup_YYYYMMDD & mkdir out
```
