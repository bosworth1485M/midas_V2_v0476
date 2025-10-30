# SINGLE_DAY_RUN_GUIDE.md

Minimal day run and quick summaries (pure Python).

## Run a single day (Scenario D)
```
python scripts\run_day_simple.py --date 2025-08-05 --scenario D
python scripts\summarize_results.py --date 2025-08-05
```

## View results with the tiny viewer
```
python scripts\view_results.py --date 2025-08-05
python scripts\view_results.py --date 2025-09-02 --scenario D --preview 20 --top 5
```

## Notes
- Output paths: `out\YYYYMMDD\<SCENARIO>\results_YYYY-MM-DD.csv` (+ `summary_YYYY-MM-DD.txt`).
- Universe + minutes are under `data\samples\`.
- `topgappers.py` uses PRIOR TRADING DAY for gaps via `prev_trading_day_polygon.py`.
