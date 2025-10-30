# Scripts Quick Reference — Single Day & Range (v0.3.9)

**Purpose:** One-page guide for the scripts we use most often — with exact command examples.  
**Note:** No Pandoc needed. Our runners auto-load `.env` and expose `src/` (v0.3.8 envfix).

---

## Single-Day Workflow

### 1) Run a day (build universe → fetch minutes → backtest)
```
python scripts\run_day_simple.py --date 2025-08-05 --scenario D
```

### 2) Summarize that day (all scenarios on the date)
```
python scripts\summarize_results.py --date 2025-08-05
```

### 3) View results (overview or detail)
```
# Overview for the date (+ D detail if present)
python scripts\view_results.py --date 2025-08-05

# Detail for a single scenario with a quick table preview
python scripts\view_results.py --date 2025-08-05 --scenario D --preview 20 --top 5
```

**Outputs**
- CSV: `out\YYYYMMDD\<SCENARIO>\results_YYYY-MM-DD.csv`  
- Summary (auto-saved by the day runner): `out\YYYYMMDD\<SCENARIO>\summary_YYYY-MM-DD.txt`  
- Universe & minutes: `data\samples\universe_sample.txt` and `data\samples\sample_<DATE>_<SYMBOL>.csv`

**Scenarios**: `A`, `B`, `C`, `D`, `E` (use your baseline settings).

---

## Range / Regression Workflow

### 1) Run a month (per scenario)
```
python scripts\run_range_and_summarize.py --start 2025-09-01 --end 2025-09-30 --scenario D
```

### 2) See what file was written (helper)
```
python scripts\show_latest_range.py --root out\auto --scenario D
```

### 3) Explain the range results (analyzer)
```
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250901_20250930_D.csv
```

**Outputs**
- Range CSV: `out\auto\range_summary_<START>_<END>_<SCENARIO>.csv`  
- Auto-generated per-day results live under `out\auto\<YYYYMMDD>\<SCENARIO>\...` (implementation-dependent).

**Repeat** for `E`, `B`, `A`, `C` to complete the month.

---

## Behind the Scenes (FYI)
- `scripts\topgappers.py` computes gaps vs the **previous trading day** using `prev_trading_day_polygon.py` (weekends/US holidays handled).  
- `scripts\fetch_minutes_polygon.py` fetches 1‑minute bars for tickers in `universe_sample.txt`.

---

## Troubleshooting (fast)
- **Import error (`midas_v2`) in this terminal only:**  
  Run once, then retry your command:  
  ```
  $env:PYTHONPATH="$PWD\src"
  ```
- **Empty universe / no trades:** check `.env` keys (Polygon), and re-run `run_day_simple.py` so it rebuilds the universe & minutes.  
- **Docs refresh says Pandoc missing:** safe to ignore; we decided **not** to use Pandoc.

---

## Handy Examples

**Single day — D**
```
python scripts\run_day_simple.py --date 2025-09-02 --scenario D
python scripts\view_results.py --date 2025-09-02 --scenario D --preview 20 --top 5
```

**September — D then E**
```
python scripts\run_range_and_summarize.py --start 2025-09-01 --end 2025-09-30 --scenario D
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250901_20250930_D.csv

python scripts\run_range_and_summarize.py --start 2025-09-01 --end 2025-09-30 --scenario E
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250901_20250930_E.csv
```

---

**File this under:**  
`Docs\versions\6. documents for v0.3.9\`
