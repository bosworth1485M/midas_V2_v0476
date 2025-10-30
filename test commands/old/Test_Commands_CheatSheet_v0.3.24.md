# Midas_V2 – Test Commands Cheat Sheet (v0.3.24)

**Last updated:** 2025-09-20 21:36 (America/Chicago)

> One-liners only (your preference). Default: Python scripts, no PowerShell wrappers necessary.

## Single Day
**Scenario B (baseline):**
```powershell
# Default (Top-50)
python scripts/run_day_simple.py --date 2025-08-05 --scenario B

# Trim to Top-12
python scripts/run_day_simple.py --date 2025-08-05 --scenario B --top 12

# Trim to Top-20
python scripts/run_day_simple.py --date 2025-08-05 --scenario B --top 20
```

**Scenario D (strict):**
```powershell
python scripts/run_day_simple.py --date 2025-08-05 --scenario D
```

**Scenario E (dip reclaim):**
```powershell
python scripts/run_day_simple.py --date 2025-08-05 --scenario E
```

## Range (August 2025)
```powershell
# Default (Top-50)
python scripts/run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B

# Trim to Top-12 per day (requires patched runner)
python scripts/run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario D --top 12
```

## Analyzer (Range Summaries)
Use the CSVs in `out/auto/` folders (not `out/range_summaries`).

**Scenario B:**
```powershell
python scripts/analyze_range_explained.py --csv out\auto\range_summary_20250805_20250831_B.csv
```

**Scenario D:**
```powershell
python scripts/analyze_range_explained.py --csv out\auto\range_summary_20250805_20250831_D.csv
```

**Scenario E:**
```powershell
python scripts/analyze_range_explained.py --csv out\auto\range_summary_20250805_20250831_E.csv
```

## Quick Paths
- Per-day CSVs: `out\YYYYMMDD\<Scenario>\results_YYYY-MM-DD.csv`
- Per-day summary: `out\YYYYMMDD\<Scenario>\summary_only_YYYY-MM-DD.txt`
- Range summary CSVs: `out\auto\range_summary_YYYYMMDD_YYYYMMDD_<Scenario>.csv`

## Notes
- **Top behavior:** By default, universes are trimmed to Top-50 gappers. Use `--top N` to override (e.g., `--top 12`, `--top 20`).
- Current gates: `rise_bars=3` (on), `macd_rise_bars=0` (off).
- Keep B as baseline; run D and E after to compare.
