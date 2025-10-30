# Midas_V2 — B Baseline Summary & Commands (Updated)
_Date: 2025-09-01 (America/Chicago)_

## What’s locked in
- **Scenario B = B_safe** (promoted):  
  - `tp_pct=2.0`, `sl_pct=2.5`, `macd_confirm=True`, `gate_minutes=10`, `min_pm_vol=30000`, `ema_confirm=True`, `vwap_confirm=True`, `rise_bars=2`.
- **Range runner**: `scripts/run_range_and_summarize.py` (fresh-start defaults: *skips weekends & empty days*, overwrites CSV).
- **Day runner**: `scripts/run_day_simple.py` (Top‑N-by-gap upgrade pending).

---

## Results to date (Scenario B)
- **2025-08-05** — trades **25**, wins **12**, losses **13**, **PnL −67.40**
- **2025-08-06** — trades **38**, wins **25**, losses **13**, **PnL +174.33**
- **2025-08-07** — trades **15**, wins **7**, losses **8**, **PnL −7.17**
- **2025-08-12** — trades **15**, wins **8**, losses **7**, **PnL +23.35**
- **2025-08-13** — trades **17**, wins **10**, losses **7**, **PnL +3.98**
- **2025-08-14** — trades **3**, wins **0**, losses **3**, **PnL −61.69**

**Multi‑day total (5 sessions)**  
- Trades **95**, Wins **55**, Losses **40**, **Win rate 57.89%**, **Total PnL +134.26** (before adding the Aug‑14 range)

> Drag days: Aug‑05, Aug‑14. Strong day: Aug‑06.

---

## How to run — Single day
**Build → fetch → filter → backtest (B)**
```bash
python scripts/run_day_simple.py --date YYYY-MM-DD --scenarios B --refresh-samples --min-gap 10 --limit 30
```
**Summarize one day**
```bash
python scripts/summarize_pnl.py --date YYYY-MM-DD --scenarios B
```

---

## How to run — Multi‑day range (auto‑skip weekends & empty days)

### Fresh start (re‑run each trading day; overwrite summary CSV)
```bash
python scripts/run_range_and_summarize.py --start 2025-08-05 --end 2025-08-14 --scenarios B --min-gap 12 --max-price 8 --limit 25
```
Writes: `out/auto/range_summary_20250805_20250814_B.csv`

### Reuse existing per‑day results (don’t re‑run days)
```bash
python scripts/run_range_and_summarize.py --start 2025-08-05 --end 2025-08-14 --scenarios B --min-gap 12 --max-price 8 --limit 25 --resume
```

### Compare multiple scenarios across the same span
```bash
python scripts/run_range_and_summarize.py --start 2025-08-05 --end 2025-08-14 --scenarios A,B,C,D,E --min-gap 12 --max-price 8 --limit 25
```

### Summarize specific days into totals (already‑run days)
```bash
python scripts/summarize_multi.py --dates 2025-08-05,2025-08-06,2025-08-07,2025-08-12,2025-08-13,2025-08-14 --scenario B
```

> Notes  
> • Range runner defaults: **skip weekends**, **skip no‑gapper days**, **fresh re‑run**, **overwrite** CSV.  
> • Add `--append` to append to an existing CSV, or `--resume` to reuse day results without re‑running.  
> • Use `--min-gap`, `--max-price`, and `--limit` to control universe quality and size.

---

## Optional (when ready)

### Upgrade day runner to Top‑N by gap (no alphabetical fallback)
- Replace `scripts/run_day_simple.py` with the v1.2.3 version I provided.  
- Sanity check:
```bash
python scripts/run_day_simple.py --date 2025-08-14 --scenarios B --refresh-samples --min-gap 12 --max-price 8 --limit 25
python scripts/summarize_pnl.py --date 2025-08-14 --scenarios B
```

### Add opening RVOL gate (next)
- I’ll add `--min-rvol-open` (e.g., `1.5`) so only heavy‑volume open names trade.

---

## Git (optional checkpoint)
```bash
git add config/scenarios.json scripts/run_range_and_summarize.py
git commit -m "feat: B safe baseline; range runner fresh-start defaults"
git tag -a v0.5.6-B-baseline -m "Checkpoint before Top-N-by-gap + RVOL"
git push
git push origin v0.5.6-B-baseline
```
