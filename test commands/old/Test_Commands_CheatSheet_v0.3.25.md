# Midas_V2 – Test Commands Cheat Sheet (v0.3.25)
**Last updated:** 2025-09-21 (America/Chicago)
> One-liners only. Default to Python scripts; avoid PowerShell wrappers unless noted.

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
# Baseline Scenario B
python scripts/run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B

# Strict Scenario D
python scripts/run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario D

# Scenario E (dip reclaim)
python scripts/run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario E
```


## Limitations & WR Probes
- **Current limitation:** The range runner does **not** support `--top N`. Use full universes (Top-50 default) for ranges.
- To test WR impact of a trimmed universe, run **single-day** Top-12 checks and compare.

### Single-Day (Top-12 quick checks)
```powershell
python scripts/run_day_simple.py --date 2025-08-07 --scenario B --top 12   # worst day probe
python scripts/run_day_simple.py --date 2025-08-13 --scenario B --top 12  # best day probe
python scripts/run_day_simple.py --date 2025-08-07 --scenario D --top 12
python scripts/run_day_simple.py --date 2025-08-13 --scenario D --top 12
python scripts/run_day_simple.py --date 2025-08-07 --scenario E --top 12
python scripts/run_day_simple.py --date 2025-08-13 --scenario E --top 12
```
## Analyzer (Range Summaries)
Use the auto-generated CSVs in `out\\auto\\`.

**Scenario B:**
```powershell
python scripts/analyze_range_explained.py --csv out\\auto\\range_summary_20250805_20250831_B.csv
```

**Scenario D:**
```powershell
python scripts/analyze_range_explained.py --csv out\\auto\\range_summary_20250805_20250831_D.csv
```

**Scenario E:**
```powershell
python scripts/analyze_range_explained.py --csv out\\auto\\range_summary_20250805_20250831_E.csv
```

## Quick Paths
- Per-day CSVs: `out\\YYYYMMDD\\<Scenario>\\results_YYYY-MM-DD.csv`
- Per-day summary: `out\\YYYYMMDD\\<Scenario>\\summary_only_YYYY-MM-DD.txt`
- Range summary CSVs: `out\\auto\\range_summary_YYYYMMDD_YYYYMMDD_<Scenario>.csv`

## Notes
- Top behavior: Default is Top-50 gappers. Use `--top N` to override (e.g., `--top 12`, `--top 20`).
- Current gates: `rise_bars=3` (on), `macd_rise_bars=0` (off).
- First compare B vs D vs E for August before changing parameters.
