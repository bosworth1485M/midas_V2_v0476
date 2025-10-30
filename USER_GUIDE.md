# USER_GUIDE

## Catalyst Hybrid — Single Day (B baseline)
```powershell
python scripts/run_catalyst_flow.py --date 2025-08-05 --scenario B --news-first --news-min-score 1 --top 12 --enforce-band
```

## Catalyst Hybrid — Date Range (B baseline)
```powershell
python scripts/run_catalyst_flow.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --news-min-score 1 --top 12 --enforce-band
```

### Outputs
- Kept news: `data/catalyst/catalyst_only_<DATE>.txt`
- Hybrid: `data/catalyst/universe_hybrid_<DATE>.txt`
- Results: `out/<YYYYMMDD>/B_hybrid/results_<DATE>.csv`
- Summaries: `summary_hybrid_<DATE>.txt`, `run_summary.(txt|csv)`

### What the runner prints
- `[PREFLIGHT]` band (min=10, max=40)
- `[FILTER] enforce-band removed …`
- `[RUN SUMMARY]` line
- Per-symbol table with `included_by`, `news_score`, `in_band`, and **Type** (`standard` / `rocket`)
