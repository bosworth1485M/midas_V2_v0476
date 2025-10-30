# Postmortem & How‑To — Env, Prev‑Trading‑Day, Regression (v0.3.9)

**Date:** 2025-09-08  
**Scope:** What broke, how we fixed it (without changing working logic), how we verified August, and the Git commands we used to save the checkpoint — plus what to do next.

---

## 1) Symptoms (what you saw)
- Running `run_day_simple.py` or `topgappers.py` started failing with **HTTP 401 Unauthorized** from Polygon.
- `prev_trading_day_polygon.py` also failed (it calls Polygon), which blocked the entire day run at the very first step.
- Previously, the same flows **worked** (we had successful runs for 2025‑08‑05 and 2025‑09‑02 earlier).

---

## 2) Root Cause (what changed)
- Your `.env` key was **valid** (we proved a **200** via a header auth call), but our scripts still used the older `?apiKey=...` **query‑string** style in places.
- Query‑string auth is **fragile** when a key has stray quotes/whitespace or when a stale machine env var shadows the project `.env`.
- We briefly swapped the prev‑day helper’s logic to “any 200 is a trading day,” which was **wrong** on holidays (e.g. Labor Day 2025‑09‑01 returns 200 with empty results).

> Takeaway: the problem was **auth style**, not your strategy code.

---

## 3) Fixes (minimal, logic‑safe)
### 3.1 Scripts that talk to Polygon
- **`scripts/topgappers.py`** — **fixed**  
  - Load `ROOT/.env` with `override=True` (project `.env` wins).  
  - **Sanitize** key: `strip()` + remove accidental `'` / `"` quotes.  
  - Use HTTP **`Authorization: Bearer <key>`** header (no `?apiKey=`).  
  - Continue to call `prev_trading_day_polygon.py` for prev‑trading‑day resolution.

- **`scripts/prev_trading_day_polygon.py`** — **fixed with logic intact**  
  - Keep the **original logic**: walk backward until **`resultsCount > 0`** (skip weekends/holidays).  
  - Only change: **header auth** + sanitized key (no query param).  
  - Verified: `2025-09-02 → 2025-08-29` (Labor Day 09‑01 skipped).

- **`scripts/fetch_minutes_polygon.py`** — **fixed**  
  - Same **header auth** + sanitized key; logic unchanged.  
  - Verified: wrote 62+ minute files for 2025‑08‑05 with `--session rth`.

### 3.2 What we **didn’t** change
- No scenario logic was altered (A–E unchanged).  
- No new scripts were introduced.  
- We kept your runners the same (day/range/analyzers).

---

## 4) Re‑verification steps we ran (August D)
1) **Single day sanity** (D):  
   ```bat
   python scripts\run_day_simple.py --date 2025-08-05 --scenario D
   python scripts\view_results.py --date 2025-08-05 --scenario D --preview 20 --top 5
   ```
   Result: 10 trades, **4 TP (40%)**, TotalPnL **−88.27**, same symbols as before.

2) **Month range** (D):  
   ```bat
   python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario D
   python scripts\show_latest_range.py --root out\auto --scenario D
   python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250805_20250831_D.csv
   ```
   Summary: **79 trades**, **50/29 W/L**, **WR 63.29%**, **PnL +167.57** (matches our baseline).

> These numbers match what we recalled from earlier runs, so the environment is now stable.

---

## 5) Save this checkpoint in GitHub (commands we used)
> Branch: `restore/v0.3.6` • Prior tag: `v0.3.8-2025-09-07-envfix`

1) Save the analyzer output alongside the CSV:  
```bat
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250805_20250831_D.csv > "Docs\versions\6. documents for v0.3.9\AUGUST_D_range_analysis.txt"
```

2) Stage and commit docs + summary:  
```bat
git add out\auto\range_summary_20250805_20250831_D.csv "Docs\versions\6. documents for v0.3.9\AUGUST_D_range_analysis.txt"
git commit -m "Aug D baseline: WR 63.29% (+167.57). Add range summary CSV + analysis note."
git push
```

3) Tag the baseline for easy restore:  
```bat
git tag -a v0.3.9-baseline-augD -m "August D baseline: WR 63.29% PnL +167.57"
git push --tags
```

> Restore later: `git checkout -b restore/v0.3.9-augD v0.3.9-baseline-augD`

---

## 6) What’s next (simple, one‑at‑a‑time)
### 6.1 September validation (A–E), existing runners only
```bat
# D (anchor)
python scripts\run_range_and_summarize.py --start 2025-09-01 --end 2025-09-30 --scenario D
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250901_20250930_D.csv

# E (dip)
python scripts\run_range_and_summarize.py --start 2025-09-01 --end 2025-09-30 --scenario E
python scripts\analyze_range_explained.py --csv out\auto\range_summary_20250901_20250930_E.csv
```

### 6.2 (After A–E pass) Hygiene + opening RVOL gate (A/B runs)
- Hygiene: exclude warrants/units/leveraged ETFs in the universe.  
- Opening RVOL gate: first 10–15m vs prior day ≥ **1.5**.

### 6.3 (Then) Router dry‑run → enable
- One position per symbol; precedence **D → E → B → A → C**; shared risk budget.  
- Dry‑run first (logs only), then enable if clean.

### 6.4 (Later) Risk‑based sizing (documented)
- Fixed $R per trade (e.g., $50), strict caps.  
- Turn on only after September baseline is stable.

---

## 7) One‑line sanity checks (optional)
**Prove `.env` key works (header + sanitize, read‑only):**  
```bat
$k = (Get-Content .\.env | ? {$_ -match '^POLYGON_API_KEY='} | Select-Object -First 1) -replace '^POLYGON_API_KEY=',''; $k=$k.Trim().Trim('"').Trim("'"); (Invoke-WebRequest -Uri 'https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/2025-08-05?adjusted=true' -Headers @{Authorization="Bearer $k"; 'User-Agent'='midas_v2/1.0'} -TimeoutSec 30).StatusCode
```

**Confirm no lingering `?apiKey=` in live scripts:**  
```bat
Select-String -Path .\scripts\*.py -Pattern "?apiKey=" -SimpleMatch
```

---

## 8) Final note
We intentionally **did not** alter any scenario logic. The only changes were: `.env` loading with `override=True`, key **sanitization**, and switching to **Authorization header** in the three Polygon callers. The prev‑trading‑day logic remains the same and now correctly skips holidays again.
