# Midas_V2 — v0.3.44 (working)  
**Theme:** catalyst *range* workflow + B tuning probes (Aug-05→Aug-07)

## 1) New script (added in v0.3.44)
### `scripts/run_catalyst_range_and_summarize.py`
**What it is:** a date-range runner for the *catalyst* flow that mirrors the old non-catalyst range behavior.

**What it does:**
- Iterates **start→end** (skips weekends by default) and prechecks the day via `topgappers.py --no-write` (so empty/holiday days can be skipped fast).
- For each trading day, it calls the **single-day** pipeline (`run_catalyst_flow.py`) with **exactly the same flags** you pass to the range runner (no behavioral drift).
- After each day, it finds the day’s `results_YYYY-MM-DD.csv` and appends a row to a **range summary CSV**:
  - Output: `out/auto_catalyst/range_summary_<START>_<END>_<LABEL>.csv`  
  - Columns: `date, label, trades, wins, losses, winrate_pct, pnl`
- Supports both **scenario** and the **profile-swap** flow (`--profile B_profit_v1|v2` with `--profile-keep` or custom `--profile-*_path`).
- For comparisons, passes through `--compare` / `--compare-label` so the day’s `_comparisons` bundle is written (JSON + TXT).
- All catalyst “knobs” are forwarded 1:1:  
  `--news-first --require-news --news-min-score --deny-negative --exclude-china --top --enforce-band --band-min --band-max --min-rvol-open --gate-minutes …`

**Why we built it:** we needed a **reliable range runner** for the news/catalyst flow with weekend/holiday hygiene, identical behavior to the one-day runner, and a simple CSV roll-up for side-by-side probes.

**Example usage (the ones we actually ran):**
```powershell
# Probe 1 – Top-4, RVOL 1.8, gate 15 (no deny)
python scripts/run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --require-news --news-min-score 2 --top 4 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 1.8 --gate-minutes 15 --compare --compare-label B_primary_top4_rvol18_g15

# Probe 2 – Top-4, RVOL 1.8, gate 15 with deny-negative
python scripts/run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --require-news --news-min-score 2 --deny-negative --top 4 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 1.8 --gate-minutes 15 --compare --compare-label B_top4_rvol18_g15_DENYNEG

# Probe 3 – Top-3, RVOL 2.0, gate 15 with deny-negative
python scripts/run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --require-news --news-min-score 2 --deny-negative --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --compare --compare-label B_top3_rvol20_g15_DENYNEG

# Probe 4 – Top-3, RVOL 2.0, gate 20 with deny-negative
python scripts/run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --require-news --news-min-score 2 --deny-negative --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 20 --compare --compare-label B_top3_rvol20_g20_DENYNEG
```

---

## 2) What we tested (Aug-05 → Aug-07, Scenario **B**)

### Probe A — **Top-4**, **RVOL 1.8**, **gate 15**, news≥2, band 10–40, *no deny-neg*
- **Totals:** 10 trades, **WR 40.00%**, **PnL −52.98**

### Probe B — **Top-4**, **RVOL 1.8**, **gate 15**, **deny-neg**
- **Totals:** 11 trades, **WR 45.45%**, **PnL −43.48**

### Probe C — **Top-3**, **RVOL 2.0**, **gate 15**, **deny-neg**
- **Totals:** 9 trades, **WR 55.56%**, **PnL −9.73**

### Probe D — **Top-3**, **RVOL 2.0**, **gate 20**, **deny-neg** ✅ *best of the set*
- **Totals:** **9 trades, WR 66.67%, PnL +79.38**

---

## 3) Interim conclusion (do **not** lock B yet)
- Best micro-profile for these 3 days: **news≥2, deny-neg, Top-3, RVOL 2.0, gate=20**  
- But we are **not locking B yet**; still need full-August/July sweeps and diagnostics.

---

## 4) Open issue — *“Never seen score=3 for news”*
- No `score=3` rows observed in catalyst CSVs. Possible causes: scoring logic capped, mapping collapsing values, or upstream data never yields 3.  
- Diagnostics needed: log max score per run; audit catalyst CSVs directly; verify scoring rubric.  

---

## 5) Tag notes
- **Added:** `run_catalyst_range_and_summarize.py`  
- **Probes executed:** A/B/C/D above.  
- **Best micro-result:** Probe D, WR 66.67%, PnL +79.38.  
- **Status:** B not locked. Need wider validation.  
- **Known issue:** no score=3 observed in catalyst news.

---

## 6) Next steps (towards v0.3.45)
- Run Aug-08→Aug-31 with Probe D profile.  
- Analyze losses with per-trade dump & gate sensitivity.  
- Investigate news scoring (why no 3s).  
