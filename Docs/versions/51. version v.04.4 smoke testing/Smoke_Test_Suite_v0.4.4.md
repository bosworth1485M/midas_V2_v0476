# Smoke Test Suite — Midas_V2 v0.4.4
## Purpose
These smoke tests confirm that key strategy gates, filters, and risk modules are functioning correctly before each major version release.

---

## ✅ Completed Tests
| Test | Status | Result |
|------|---------|---------|
| MACD Rise Gate | ✅ | Previously confirmed — setting `macd_rise_bars` to 10 produced 0 trades. |
| Green-Streak Gate | ✅ | Confirmed — setting `rise_bars` to 10 produced 0 trades (Aug 2025). |

---

## 🔬 Upcoming Smoke Tests (v0.4.4)
Each test uses the August 2025 range by default (`2025-08-05 → 2025-08-31`). Expect **0 trades** when each gate is exaggerated.

### 1️⃣ VWAP Slope Gate Test
**Goal:** Ensure VWAP slope filtering is active.
```
python -c "import json;p='config\\scenarios.json';d=json.load(open(p));d['B']['params']['vwap_slope_bps']=999;json.dump(d,open(p,'w'),indent=2)"
python scripts\run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B --top 3 --enforce-band --band-min 10 --band-max 40
```
Expected: `Trades=0`

### 2️⃣ EMA Slope Gate Test
**Goal:** Verify EMA slope confirm logic.
```
python -c "import json;p='config\\scenarios.json';d=json.load(open(p));d['B']['params']['ema_slope_bps']=999;d['B']['params']['ema_confirm']=True;json.dump(d,open(p,'w'),indent=2)"
```
Expected: `Trades=0`

### 3️⃣ Gate-Minutes Test
**Goal:** Check entry gate timer.
```
python -c "import json;p='config\\scenarios.json';d=json.load(open(p));d['B']['params']['gate_minutes']=999;json.dump(d,open(p,'w'),indent=2)"
```
Expected: `Trades=0`

### 4️⃣ Price Band Test
**Goal:** Validate price filter.
```
python -c "import json;p='config\\scenarios.json';d=json.load(open(p));d['B']['params'].update({'min_price':100,'max_price':200});json.dump(d,open(p,'w'),indent=2)"
```
Expected: `Trades=0`

### 5️⃣ Gap Percentage Test
**Goal:** Verify gap filters.
```
python -c "import json;p='config\\scenarios.json';d=json.load(open(p));d['B']['params']['min_gap_pct']=200;json.dump(d,open(p,'w'),indent=2)"
```
Expected: `Trades=0`

### 6️⃣ Pre-Market Volume Test
**Goal:** Confirm pre-market volume cutoff.
```
python -c "import json;p='config\\scenarios.json';d=json.load(open(p));d['B']['params']['min_pm_vol']=99999999;json.dump(d,open(p,'w'),indent=2)"
```
Expected: `Trades=0`

### 7️⃣ RVOL Gate Test
**Goal:** Validate relative-volume gate.
```
python -c "import json;p='config\\scenarios.json';d=json.load(open(p));d['B']['params']['min_rvol_open']=99.9;json.dump(d,open(p,'w'),indent=2)"
```
Expected: `Trades=0`

### 8️⃣ Stop-Loss Sanity Test
**Goal:** Confirm SL enforcement.
```
python -c "import json;p='config\\scenarios.json';d=json.load(open(p));d['B']['params'].update({'sl_pct':0.01,'tp_pct':999});json.dump(d,open(p,'w'),indent=2)"
```
Expected: Either instant stop-outs or 0 trades.

### 9️⃣ Catalyst Hard-Filter Test
**Goal:** Verify `--require-news` flag and score threshold.
```
python scripts\run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B --news-first --require-news --news-min-score 999 --top 3
```
Expected: `Trades=0`

### 🔟 Adaptive Sizing Zero-Risk Test
**Goal:** Ensure division-by-zero safety.
```
python -c "import json;p='config\\scenarios.json';d=json.load(open(p));d['B']['params']['sizing']['base_risk_usd']=0;json.dump(d,open(p,'w'),indent=2)"
```
Expected: `Trades=0` or safe warning.

---

## 🧩 Post-Test Cleanup
Always restore defaults after smoke tests:
```
python -c "import json;p='config\\scenarios.json';d=json.load(open(p));d['B']['params'].update({'rise_bars':3,'macd_rise_bars':2,'gate_minutes':15,'min_price':1,'max_price':20,'min_gap_pct':10,'min_pm_vol':30000,'min_rvol_open':2.0,'tp_pct':2.0,'sl_pct':2.5});json.dump(d,open(p,'w'),indent=2);print('Smoke defaults restored.')"
```

---

## 🧠 Notes
- Each test should yield 0 trades unless the filter being tested is malfunctioning.
- Run `show_latest_range.py` after each to confirm.
- Document results in `Docs\Smoke_Test_Log_v0.4.4.md` before proceeding to long-range runs.

---

**Next Step:** Execute these smoke tests sequentially for v0.4.4 before enabling S/R Lite and Finnhub integration.
