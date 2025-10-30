# Diagnostic Commands — Midas_V2 (2025-09-29)

This note collects the exact one‑liners we used and the outputs we saw while validating **Scenario B (news‑only, Top‑4, band 10–40, RVOL≥1.8, gate=15)**, plus the diagnostics we ran to explain zero‑trade days. Everything below is copy‑paste ready.

---

## Baseline summary (Scenario B — winner profile)
- **news-first**, **require-news**, **news-min-score 2**
- **Top-4**, **gap band 10–40%** (enforced), **min-rvol-open 1.8**
- **gate-minutes 15**
- Filters: **--deny-negative --exclude-china**
- Compare label used: **B_primary_top4_rvol18_g15**

---

## A) Baseline runner (one-liner per day)

Change `YYYY-MM-DD` to the date:
```powershell
python scripts\run_catalyst_flow.py --date YYYY-MM-DD --scenario B --news-first --require-news --news-min-score 2 --top 4 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 1.8 --gate-minutes 15 --deny-negative --exclude-china --print-news --compare --compare-label B_primary_top4_rvol18_g15
```

### Example invocations we ran
```powershell
python scripts\run_catalyst_flow.py --date 2025-08-08 --scenario B --news-first --require-news --news-min-score 2 --top 4 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 1.8 --gate-minutes 15 --deny-negative --exclude-china
python scripts\run_catalyst_flow.py --date 2025-08-11 --scenario B --news-first --require-news --news-min-score 2 --top 4 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 1.8 --gate-minutes 15 --deny-negative --exclude-china --print-news
python scripts\run_catalyst_flow.py --date 2025-08-12 --scenario B --news-first --require-news --news-min-score 2 --top 4 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 1.8 --gate-minutes 15 --deny-negative --exclude-china --print-news
python scripts\run_catalyst_flow.py --date 2025-08-13 --scenario B --news-first --require-news --news-min-score 2 --top 4 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 1.8 --gate-minutes 15 --deny-negative --exclude-china --print-news
python scripts\run_catalyst_flow.py --date 2025-08-14 --scenario B --news-first --require-news --news-min-score 2 --top 4 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 1.8 --gate-minutes 15 --deny-negative --exclude-china --print-news
```

> We later added `--compare --compare-label B_primary_top4_rvol18_g15` to all new runs, and sometimes `--no-rebuild` to speed re-runs.

### Results we saw (per‑day snippets)
- **2025‑08‑08** → `Used=1, TP=0, SL=1, Win%=0.00, PnL=−50.18` (ARLO only after filters)
- **2025‑08‑11** → `Used=1, TP=1, SL=0, Win%=100.00, PnL=+15.64`
- **2025‑08‑12** → `Used=0, PnL=0.00` (no score≥2 news among band‑qualified gappers)
- **2025‑08‑13** → `Used=0, PnL=0.00` (no score≥2 news among band‑qualified gappers)
- **2025‑08‑14** → `Used=1, TP=1, SL=0, Win%=100.00, PnL=+6.48`

(Additional per‑day outcomes are reflected in the Analyzer snapshot below.)

---

## B) Analyzer — roll up results for the compare label

**One‑liner:**
```powershell
python scripts\analyze_compare_label.py --label B_primary_top4_rvol18_g15 --csv out\compare_B_primary_top4_rvol18_g15.csv
```

**Latest snapshot printed:**
```
Date       Used     WR%  TP  SL        PnL        RunId
-------------------------------------------------------
2025-08-01    0    0.00   0   0      +0.00   1759171914
2025-08-04    0    0.00   0   0      +0.00   1759171952
2025-08-05    3  100.00   3   0     +28.51   1759173683
2025-08-06    4   75.00   3   1     +51.26   1759071195
2025-08-07    4   50.00   2   2     -19.46   1759072112
2025-08-08    1    0.00   0   1     -50.18   1759171005
2025-08-11    1  100.00   1   0     +15.64   1759171031
2025-08-12    0    0.00   0   0      +0.00   1759171048
2025-08-13    0    0.00   0   0      +0.00   1759171071
2025-08-14    1  100.00   1   0      +6.48   1759171089
2025-08-15    0    0.00   0   0      +0.00   1759171227
2025-08-18    1  100.00   1   0      +7.31   1759171283
2025-08-19    0    0.00   0   0      +0.00   1759171315
2025-08-20    0    0.00   0   0      +0.00   1759171344
2025-08-21    1    0.00   0   1     -17.12   1759171532
2025-08-22    0    0.00   0   0      +0.00   1759171562
2025-08-25    0    0.00   0   0      +0.00   1759171597
2025-08-26    0    0.00   0   0      +0.00   1759171641
2025-08-27    0    0.00   0   0      +0.00   1759171674
2025-08-28    1  100.00   1   0      +5.36   1759171700
2025-08-29    0    0.00   0   0      +0.00   1759171734
2025-09-02    0    0.00   0   0      +0.00   1759172857
2025-09-03    2   50.00   1   1     -39.88   1759172950
2025-09-04    2  100.00   2   0     +23.69   1759172995
2025-09-05    0    0.00   0   0      +0.00   1759173027
2025-09-08    0    0.00   0   0      +0.00   1759173087
2025-09-09    0    0.00   0   0      +0.00   1759173125
2025-09-10    0    0.00   0   0      +0.00   1759173177
2025-09-11    0    0.00   0   0      +0.00   1759173225
2025-09-12    0    0.00   0   0      +0.00   1759173267
2025-09-15    0    0.00   0   0      +0.00   1759173307
2025-09-16    0    0.00   0   0      +0.00   1759173344
2025-09-17    0    0.00   0   0      +0.00   1759173379
2025-09-18    0    0.00   0   0      +0.00   1759173452
2025-09-19    0    0.00   0   0      +0.00   1759173492
2025-09-22    0    0.00   0   0      +0.00   1759173550
2025-09-23    0    0.00   0   0      +0.00   1759178782
2025-09-24    0    0.00   0   0      +0.00   1759178872
2025-09-25    0    0.00   0   0      +0.00   1759178901
2025-09-26    0    0.00   0   0      +0.00   1759178946
2025-09-29    0    0.00   0   0      +0.00   1759179011
-------------------------------------------------------
TOTAL        21   71.43  15   6     +11.61
```

> Earlier snapshot (before the re‑run of Aug‑05) showed **Used=17, WR 70.59%, PnL +47.11**.

---

## C) Zero‑trade diagnostics (Python‑only; no backtests)

**Script:** `scripts/diagnose_zero_trades.py` (reads existing files only)

**One‑liner we ran for September (weekdays only) with CSV + rollup:**
```powershell
python scripts\diagnose_zero_trades.py --start 2025-09-02 --end 2025-09-29 --weekday-only --csv out\diagnose_B_sep.csv --rollup
```

**Output we saw (weekdays):**
```
Date       NewsRaw NewsKept  InBand Used  Reason
------------------------------------------------
2025-09-02       0       20       0    0  NO_NEWS_SCORE_GE_2
2025-09-03       2       22       0    2  TRADED
2025-09-04       2       18       0    2  TRADED
2025-09-05       0       15       0    0  NO_NEWS_SCORE_GE_2
2025-09-08       0       28       0    0  NO_NEWS_SCORE_GE_2
2025-09-09       0       30       0    0  NO_NEWS_SCORE_GE_2
2025-09-10       1       42       0    0  NEWS_OUT_OF_BAND
2025-09-11       0       36       0    0  NO_NEWS_SCORE_GE_2
2025-09-12       1       41       0    1  TRADED
2025-09-15       0       42       0    0  NO_NEWS_SCORE_GE_2
2025-09-16       0       26       0    0  NO_NEWS_SCORE_GE_2
2025-09-17       1       20       0    1  TRADED
2025-09-18       1       25       0    1  TRADED
2025-09-19       0       26       0    0  NO_NEWS_SCORE_GE_2
2025-09-22       0       36       0    0  NO_NEWS_SCORE_GE_2
2025-09-23       2       28       0    0  NEWS_OUT_OF_BAND
2025-09-24       0       25       0    0  NO_NEWS_SCORE_GE_2
2025-09-25       0       16       0    0  NO_NEWS_SCORE_GE_2
2025-09-26       0       17       0    0  NO_NEWS_SCORE_GE_2
2025-09-29       0       44       0    0  NO_NEWS_SCORE_GE_2

Zero-trade reasons (weekday filter applied)
 13  NO_NEWS_SCORE_GE_2
  2  NEWS_OUT_OF_BAND
```

**Optional “what‑if” (no re‑runs): widen the band to 60 and see counts**
```powershell
python scripts\diagnose_zero_trades.py --start 2025-09-02 --end 2025-09-29 --weekday-only --band-max 60 --rollup --csv out\diagnose_B_sep_band60.csv
```

---

## D) Quick interpretation checklist
- Long 0‑trade sequences are expected with the strict baseline: **require‑news + score≥2 + band 10–40 + RVOL≥1.8 + gate=15 + filters**.
- September diagnostics confirm most zero days were **`NO_NEWS_SCORE_GE_2`**, with a couple **`NEWS_OUT_OF_BAND`** (rocket‑gap days).
- Keep running the **same baseline** across months; use the Analyzer to track **Used/WR/PnL** and the Diagnostic to explain zeros.

---

## E) **Lock B** Checklist (Provisional + Wilson)

### 1) Provisional lock — when to freeze B
Check these **four** conditions:
- **Trades:** ≥ **50** total (not days)
- **Win‑rate:** ≥ **60%** overall
- **PnL:** total **> 0**
- **Stability:** no more than **1–2 bad clusters** (e.g., no more than 3 straight SLs twice)

**Tagging (one‑liners):**
```powershell
git add out\compare_B_primary_top4_rvol18_g15.csv
git commit -m "Lock B (provisional): WR ≥60%, PnL>0 over 50+ trades"
git tag -a v0.3.xx-B_locked_provisional -m "Scenario B provisional lock"
git push
git push --tags
```

### 2) Wilson 95% (why and how we glance‑check)
- We use the **Wilson score 95% CI** for the win‑rate because it’s reliable with small samples and stays within 0–100%.
- Interpretation: if you repeated the process many times, **95%** of intervals built this way would contain the true win‑rate. The **lower bound** is the conservative “what you can reasonably count on” with current evidence.
- **Rules of thumb:**
  - 60% over **50** trades → **LB ≈ 46%**
  - 60% over **100** trades → **LB ≈ 50%**
  - 65% over **200** trades → **LB ≈ 58%**

**Current example:** 15 wins / 21 trades = **71.43%** → Wilson 95% CI ≈ **[50.04%, 86.19%]**.

**Quick check (edit `wins`/`n` as needed):**
```powershell
python -c "import math; wins=15; n=21; z=1.96; p=wins/n; den=1+z*z/n; c=(p+z*z/(2*n))/den; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den; print(f'WR={p*100:.2f}%  95% CI=[{(c-h)*100:.2f}%, {(c+h)*100:.2f}%]')"
```

### 3) Hard lock — the “true baseline” bar
- **Trades:** ≥ **150–200** across **2–3 months** (include hot + cold regimes)
- **Win‑rate:** ≥ **60%** and **Wilson lower bound ≥ ~55%**
- **PnL:** total **> 0**, **drawdown** within plan (e.g., < daily cap × 3 consecutive days)

**Tagging (one‑liners):**
```powershell
git commit -m "Lock B (hard): WR ≥60%, LB≥55% (Wilson), PnL>0 over 200+ trades, multi‑month"
git tag -a v0.3.yy-B_locked -m "Scenario B hard lock"
git push
git push --tags
```

---

### Appendix — Handy single‑day macro (optional, same flow)
```powershell
$d='YYYY-MM-DD'; python scripts\run_catalyst_flow.py --date $d --scenario B --news-first --require-news --news-min-score 2 --top 4 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 1.8 --gate-minutes 15 --deny-negative --exclude-china --print-news --compare --compare-label B_primary_top4_rvol18_g15 ; python scripts\analyze_compare_label.py --label B_primary_top4_rvol18_g15 --csv out\compare_B_primary_top4_rvol18_g15.csv ; python scripts\diagnose_zero_trades.py --dates $d
```