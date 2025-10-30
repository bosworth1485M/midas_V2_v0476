# DEV_GUIDE

## Version
- Current tag: **v0.3.31**
- Updated: 2025-09-24

## Catalyst Hybrid — Single Day (B baseline)
```powershell
python scripts/run_catalyst_flow.py --date 2025-08-05 --scenario B --news-first --news-min-score 1 --top 12 --enforce-band
```

## Catalyst Hybrid — Date Range (B baseline)
```powershell
python scripts/run_catalyst_flow.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --news-min-score 1 --top 12 --enforce-band
```

### Notes
- Wrapper passes the **full RAW file** to compose (reliable hybrid fill).
- Compose builds **news + RAW fillers**; run-day applies junk-class → news-first → Top-N → **10–40% band** (B).

### Gotcha
Compose expects **full RAW path** for `--raw` (e.g., `data/raw/universe_topgappers_<DATE>.txt`).
Using a prefix may produce `rawTop=0` (news-only).
