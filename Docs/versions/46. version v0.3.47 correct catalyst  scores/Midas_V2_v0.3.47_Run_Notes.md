# Midas_V2 — v0.3.47 Run Notes (Profit Guard baseline)

**Date:** 2025-10-08 19:06  
**Working folder:** `C:\Users\boydp\Desktop\midas_V2_v044_working`  
**Scenario:** B (news-only, Profit Guard strict)  
**Current best profile (Aug 1–29, 2025):** `newsOnly + Top-2 + band 10–40 + RVOL 2.40 + score ≥ 3 + gate=20`  
**Headline results (over 21 days):** **WR 72.73%**, **Trades 11 (TP/SL 8/3)**, **PnL +20.98**

---

## 1) Exact commands we ran

### A. Scan run bundles (single label)
```powershell
python scripts\scan_run_bundles.py --scenario B --labels B_top2_score3_g20_rvol24_authFix --dedupe-latest --per-day
```

### B. Scan run bundles (compare two labels head-to-head)
```powershell
python scripts\scan_run_bundles.py --scenario B --labels B_top2_score3_g20_rvol24_authFix,B_top2_score3_g20_rvol22_authFix --dedupe-latest --per-day
```

### C. Scan run bundles (only days with ≥1 trade)
```powershell
python scripts\scan_run_bundles.py --scenario B --labels B_top2_score3_g20_rvol24_authFix --dedupe-latest --per-day --min-trades 1
```

### D. Show latest range CSV (per-day table for the most recent B run)
```powershell
python scripts\show_latest_range.py
```

**Observed file:** `out\auto_catalyst\range_summary_20250801_20250829_B.csv`

### E. (Optional) Validate comparison JSONs exist & have metrics
```powershell
python scripts\check_comparison_metrics.py
```

> Tip: If any line shows `MISSING`, it means that day’s `comparison_*.json` didn’t include metrics. Rerun that day with `--compare` (or use the fallback logic that reads summary text).

### F. (Reconstruct the range we’re analyzing — canonical one-liner)
```powershell
python scripts\run_catalyst_range_and_summarize.py --start 2025-08-01 --end 2025-08-29 --scenario B --news-first --require-news --news-min-score 3 --top 2 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.4 --gate-minutes 20 --deny-negative --exclude-china --compare --compare-label B_top2_score3_g20_rvol24_authFix
```

---

## 2) What the three analysis scripts do (plain-English)

### `show_latest_range.py`
- **Purpose:** Quick per-day table for the **most recent** range you ran (by timestamp), usually under `out\auto_catalyst\range_summary_YYYYMMDD_YYYYMMDD_<SCENARIO>.csv`.
- **What you see:** For each date: trades, wins/losses, win-rate %, PnL for the selected scenario. It’s a snapshot of the **range** run, not a specific label comparison.
- **When to use:** To sanity-check that your last range covered the dates you expect and produced outputs.

### `check_comparison_metrics.py`
- **Purpose:** Audits all `comparison_*.json` files emitted when you run with `--compare`. Each JSON should have `used`, `wr%`, `tp`, `sl`, `pnl`.
- **What you see:** One line per comparison file. `OK` means metrics are present; `MISSING` means the JSON lacked metrics (your runs may still be fine, and the **summary text** has the numbers).
- **When to use:** Before scanning/aggregating, to make sure your comparison bundles have the fields scanners expect.

### `scan_run_bundles.py`
- **Purpose:** Aggregates comparison bundles across many days and **summarizes by Label and Scenario**, computing WR, PnL, TP/SL, Trades, and Days.
- **Key flags:**
  - `--scenario B` → filter to Scenario B bundles.
  - `--labels A,B,...` → select specific labels (e.g., `B_top2_score3_g20_rvol24_authFix`).
  - `--dedupe-latest` → if multiple bundles exist for the same day/label, keep the **newest** only.
  - `--per-day` → prints a per-day breakdown (not just group totals).
  - `--min-trades 1` → only include days with at least one trade in the per-day section.
- **When to use:** To **rank** profiles/labels by WR/PnL across many days and pick winners.

---

## 3) Results we observed (copied from your console)

### 3.1 Top Groups by Label / Scenario (first run)
```
Scen=B | Label=B_top2_score3_g20_rvol24_authFix  newsOnly + Top-2 + band 10-40 + RVOL 2.40 + score >= 3   WR 72.73%  PnL 20.98  TP/SL 8/3  Trades 11  Days 21

Scenario=B  ... same profile ...   WR 72.73%  PnL 20.98  TP/SL 8/3  Trades 11  Days 21
```

### 3.2 Head-to-head: RVOL 2.4 vs 2.2
```
B_top2_score3_g20_rvol24_authFix  WR 72.73%  PnL 20.98  TP/SL 8/3  Trades 11  Days 21
B_top2_score3_g20_rvol22_authFix  WR 60.00%  PnL  3.33  TP/SL 3/2  Trades  5  Days  3
```

### 3.3 With --min-trades 1 (per-day subset; 8 active days)
```
WR 72.73%  Trades 11  PnL 20.98  Days 8
Per-day:
2025-08-05  WR 100.00  PnL  15.96  TP/SL 1/0  Trades 1
2025-08-06  WR  50.00  PnL  11.16  TP/SL 1/1  Trades 2
2025-08-07  WR  50.00  PnL -23.79  TP/SL 1/1  Trades 2
2025-08-08  WR 100.00  PnL  23.69  TP/SL 2/0  Trades 2
2025-08-13  WR 100.00  PnL   1.87  TP/SL 1/0  Trades 1
2025-08-14  WR   0.00  PnL -14.95  TP/SL 0/1  Trades 1
2025-08-15  WR 100.00  PnL   2.39  TP/SL 1/0  Trades 1
2025-08-29  WR 100.00  PnL   4.65  TP/SL 1/0  Trades 1
```

### 3.4 `show_latest_range.py` output (range_summary_20250801_20250829_B.csv)
```
date       | label | trades | wins | losses | winrate_pct | pnl
2025-08-05 | B     | 1      | 1    | 0      | 100.0       | 15.96
2025-08-06 | B     | 2      | 1    | 1      | 50.0        | 11.16
2025-08-07 | B     | 2      | 1    | 1      | 50.0        | -23.79
2025-08-08 | B     | 2      | 2    | 0      | 100.0       | 23.69
2025-08-13 | B     | 1      | 1    | 0      | 100.0       | 1.87
2025-08-14 | B     | 1      | 0    | 1      | 0.0         | -14.95
2025-08-15 | B     | 1      | 1    | 0      | 100.0       | 2.39
2025-08-29 | B     | 1      | 1    | 0      | 100.0       | 4.65
(Other days in the range had 0 trades)
```

---

## 4) Next steps to **increase profit** (concrete, lowest-churn)

1. **Micro-tune entry gates (one change at a time):**
   - Raise RVOL gate to **2.6** (keep gate=20).  
     ```powershell
     python scripts\run_catalyst_range_and_summarize.py --start 2025-08-01 --end 2025-08-29 --scenario B --news-first --require-news --news-min-score 3 --top 2 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.6 --gate-minutes 20 --deny-negative --exclude-china --compare --compare-label B_top2_score3_g20_rvol26_authFix
     ```
   - Raise time gate to **25** (keep RVOL=2.4).  
     ```powershell
     python scripts\run_catalyst_range_and_summarize.py --start 2025-08-01 --end 2025-08-29 --scenario B --news-first --require-news --news-min-score 3 --top 2 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.4 --gate-minutes 25 --deny-negative --exclude-china --compare --compare-label B_top2_score3_g25_rvol24_authFix
     ```

2. **Lock profit-first baseline:** If either variant beats **WR 72.73% / PnL +20.98** on the same dates, tag it as the new **B Profit Guard**.

3. **Adaptive sizing (Kelly-lite with guardrails):**  
   - Tiered position size by catalyst score & opening RVOL.  
   - Per-trade risk caps; daily stop; drawdown throttle.  
   - Keep TP/SL=2.0/2.5 initially; revisit only after sizing proves stable.

4. **Universe hygiene (already strong—keep it):**
   - `--require-news --news-min-score 3` (lock this).
   - `--top 2` (stay selective unless market is hot).  
   - `--deny-negative --exclude-china` (keep).

5. **Signal confirms (stay conservative):**
   - EMA+VWAP confirms on; **MACD rise_bars=2**; green streak gates on B.  
   - Consider **gate=20–25** sweet spot; avoid the first 15 min noise.

---

## 5) Git tagging & push (v0.3.47)

> Run these from your repo root (not Dropbox). Substitute your commit message as needed.

```powershell
git add -A
git commit -m "v0.3.47: B Profit Guard baseline (Top-2, score>=3, RVOL=2.4, gate=20) + docs"
git tag v0.3.47
git push origin main
git push --tags
```

---

## 6) TL;DR

- Your **best B profile** right now (Aug 1–29): **WR 72.73%**, **PnL +20.98** with **Top-2, score≥3, RVOL 2.4, gate 20**.  
- Next: try **RVOL 2.6** and **gate 25** (separately), promote the winner, then implement **adaptive sizing**.
