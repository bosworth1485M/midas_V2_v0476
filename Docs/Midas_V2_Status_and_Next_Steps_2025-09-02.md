# Midas_V2 — Status & Next Steps
_Date: 2025-09-02 (America/Chicago)_

---

## Where we are (quick snapshot)

**Code & runners**
- `scripts/run_day_simple.py` **v1.3.1** installed:
  - **Top‑N by gap** (no alphabetical fallback)
  - Optional **opening RVOL** gate (`--min-rvol-open`, default OFF)
  - Optional **green‑streak** gate (`--green-streak`, default OFF)
- `scripts/run_range_and_summarize.py` **v1.4** (fresh‑start defaults):
  - Skips **weekends** and **empty/no‑gapper** days by default
  - Overwrites range CSV by default; `--resume` and `--append` available
- Utility summarizers: `scripts/summarize_pnl.py`, `scripts/summarize_multi.py`

**Scenarios (current)**
- **B (baseline, “B_safe”)**:
  - `tp_pct=2.0`, `sl_pct=2.5`  
  - `macd_confirm=True`, `rise_bars=2`  
  - `gate_minutes=10`, `min_pm_vol=30000`  
  - `ema_confirm=True`, `vwap_confirm=True`
- **D (control)**: original “looser” preset (tp=2.0, sl=3.5, MACD off, gate=0, pm_vol=0)
- **A / C / E**: unchanged (E to be upgraded later to “E_dip”)

**Inputs & filters**
- Day runner builds **deterministic Top‑N by gap** via `topgappers.py --no-write`
- **RVOL** and **green‑streak** are **OFF** right now while we re‑baseline

---

## Results — recent highlights (Scenario B)

- **Aug 14** turned **positive** with Top‑N + RVOL 1.5 + TP/SL 2.0/2.0 → _9 trades, 55.56% WR, **+5.17** PnL_.  
- With stricter filters across several days, small-N variance made some days look poor. We’ll calibrate one dial at a time.

**Conclusion**: The system is stable; outcomes shifted because **inputs & gates changed together**. We’ll rebalance **one dial at a time**.

---

## Recommended path (no rollback, one small step at a time)

1) **Baseline without RVOL** (Top‑N only) — confirm B_safe on one or two days.  
2) **Add green‑streak** gate (price‑action): 2 consecutive green 1‑min candles, body ≥ **0.20%**, optional rising volume.  
3) **Reintroduce RVOL** gently (`--min-rvol-open 1.3`) once baseline steadies.  
4) Tag the working state; then optionally explore **2.0/2.0** and **tiered sizing** later.

---

## One‑liners (pure Python)

### A) Set B to **B_safe**
```bash
python -c "import json, pathlib; p=pathlib.Path('config/scenarios.json'); d=json.loads(p.read_text('utf-8')); b=d['B']['params']; b.update({'tp_pct':2.0,'sl_pct':2.5,'macd_confirm':True,'rise_bars':2,'gate_minutes':10,'min_pm_vol':30000,'ema_confirm':True,'vwap_confirm':True}); p.write_text(json.dumps(d,indent=2),'utf-8'); print('OK: B reset to B_safe')"
```

### B) Run a single day (Top‑N only; **no RVOL**, **no green**)
```bash
python scripts/run_day_simple.py --date YYYY-MM-DD --scenarios B --refresh-samples --min-gap 10 --max-price 10 --limit 40
python scripts/summarize_pnl.py --date YYYY-MM-DD --scenarios B
```

### C) Run day with **green‑streak** (no RVOL)
```bash
python scripts/run_day_simple.py --date YYYY-MM-DD --scenarios B --refresh-samples --min-gap 10 --max-price 10 --limit 40 --green-streak 2 --min-green-body-bp 20 --green-with-volume
python scripts/summarize_pnl.py --date YYYY-MM-DD --scenarios B
```

### D) Run day with **RVOL** (after baseline steady)
```bash
python scripts/run_day_simple.py --date YYYY-MM-DD --scenarios B --refresh-samples --min-gap 10 --max-price 10 --limit 40 --min-rvol-open 1.3 --rvol-minutes 15
python scripts/summarize_pnl.py --date YYYY-MM-DD --scenarios B
```

### E) Small range (fresh start; skips weekends/empty by default)
```bash
python scripts/run_range_and_summarize.py --start 2025-08-05 --end 2025-08-14 --scenarios B --min-gap 10 --max-price 10 --limit 40
```

---

## Next session — concrete plan

1) **Baseline recheck (Top‑N only)**: run **Aug 06** and **Aug 14** with B; confirm PnL/WR.  
2) **Enable green‑streak** (2 candles, ≥0.20% body, rising volume) on the same days; compare.  
3) If both improve, run a **3–5 day mini‑range** with the green‑streak setting.  
4) Reintroduce **RVOL** at **1.3** and repeat the mini‑range.  
5) If the mini‑range clears **~58–60% WR** and is net positive → **tag baseline**.  
6) (Optional) Upgrade **E** to **E_dip** (dip + MACD rising + VWAP reclaim, TP/SL 2.0/2.5).  
7) (Optional) Add **light tiered sizing** (risk 1.5× on A+ setups) with guardrails.

---

**End of document.**
