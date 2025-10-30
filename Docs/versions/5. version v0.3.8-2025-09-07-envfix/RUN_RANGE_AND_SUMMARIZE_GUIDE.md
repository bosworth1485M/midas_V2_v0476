# RUN_RANGE_AND_SUMMARIZE_GUIDE.md

Use the classic runner and analyzers you already have (pure Python).

## Run August (Scenario D)
```
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario D
python scripts\show_latest_range.py --root out\auto --scenario D
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250805_20250831_D.csv
```

## Run September (Scenario D)
```
python scripts\run_range_and_summarize.py --start 2025-09-01 --end 2025-09-30 --scenario D
python scripts\show_latest_range.py --root out\auto --scenario D
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250901_20250930_D.csv
```

## Optionally also Scenario E
```
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario E
python scripts\show_latest_range.py --root out\auto --scenario E
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250805_20250831_E.csv
```

## Common error (and fix)
If you see `ModuleNotFoundError: midas_v2` in this terminal:
```
$env:PYTHONPATH="$PWD\src"
```
(Then re-run your command.)

The runners can also be patched with the small bootstrap later (no behavior changes).
