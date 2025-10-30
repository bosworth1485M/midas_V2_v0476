# Midas Backtesting — Complete Commands Reference (v1.1)

## Revision History
- 2025-09-21  **v1.1** — Added revision list; appended docs refresh + clear_out sections; fixed analyzer paths.
- 2025-09-21  **v1.0** — Initial dated commands reference (Aug-05..Aug-31, 2025).

---

## Range Runs (August 2025)
```powershell
# B — full universe
python scripts
un_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B

# B — Top-12 per day
python scripts
un_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B --top 12

# D — Top-12 per day
python scripts
un_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario D --top 12

# E — Top-12 per day
python scripts
un_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario E --top 12

# Multi-scenario (comma-separated)
python scripts
un_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B,D,E --top 12
```

## Single-Day Runs (August 2025)
```powershell
# Best day probe (Aug-13)
python scripts
un_day_simple.py --date 2025-08-13 --scenario B
python scripts
un_day_simple.py --date 2025-08-13 --scenario B --top 12
python scripts
un_day_simple.py --date 2025-08-13 --scenario D --top 12
python scripts
un_day_simple.py --date 2025-08-13 --scenario E --top 12

# Volatile day probe (Aug-07)
python scripts
un_day_simple.py --date 2025-08-07 --scenario B
python scripts
un_day_simple.py --date 2025-08-07 --scenario B --top 12
python scripts
un_day_simple.py --date 2025-08-07 --scenario D --top 12
python scripts
un_day_simple.py --date 2025-08-07 --scenario E --top 12

# Additional spot checks
python scripts
un_day_simple.py --date 2025-08-05 --scenario B --top 12
python scripts
un_day_simple.py --date 2025-08-06 --scenario B --top 12
python scripts
un_day_simple.py --date 2025-08-08 --scenario B --top 12
```

## Analyzers & Summaries
```powershell
# Quick sanity (latest summary)
python scripts\show_latest_range.py

# Analyze range CSVs (Aug-05..Aug-31)
python scripts nalyze_range_explained.py --csv out uto
ange_summary_20250805_20250831_B.csv
python scripts nalyze_range_explained.py --csv out uto
ange_summary_20250805_20250831_D.csv
python scripts nalyze_range_explained.py --csv out uto
ange_summary_20250805_20250831_E.csv

# Rebuild summaries, then re-analyze
python scripts
ebuild_range_summary.py --start 2025-08-05 --end 2025-08-31 --scenarios B D E
```

## Paths (Output)
```text
# Per-day trades CSV
out\YYYYMMDD\<SCENARIO>
esults_YYYY-MM-DD.csv
# Per-day summary (text)
out\YYYYMMDD\<SCENARIO>\summary_YYYY-MM-DD.txt
# Range summary CSVs (Aug-05..Aug-31 examples)
out uto
ange_summary_20250805_20250831_B.csv
out uto
ange_summary_20250805_20250831_D.csv
out uto
ange_summary_20250805_20250831_E.csv
```

## Optional Utilities (Direct)
```powershell
# Build universe directly (preview + write Top-12)
python scripts	opgappers.py --date 2025-08-13 --top 12

# Fetch minutes directly (RTH session)
python scriptsetch_minutes_polygon.py --date 2025-08-13 --session rth
```

---

## Docs Refresh (how / why / outputs)
```powershell
# PowerShell (if present)
.\Docs\Refresh-Docs.ps1

# Python (alternative)
python Docs
efresh_docs.py
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
