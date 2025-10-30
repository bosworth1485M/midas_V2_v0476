# Midas_V2 – v0.3.21 Full Log

## 1. Runs & Comparisons

### Scenario B (Aug-05-2025)
```bash
python scripts/run_day_simple_SAFE.py --date 2025-08-05 --scenario B
```
- Result: No trades (TP=0, SL=0, Win%=0).

### Catalyst Universes (Aug-05, Aug-06, Aug-07)
- Enriched universes with:
```bash
python scripts/enrich_universe_catalyst.py --date 2025-08-05 --limit 50
```
- Ran catalyst day runner:
```bash
python scripts/run_day_catalyst.py --date 2025-08-05 --scenario B --universe data\universe_active.txt
```
- Compared outputs side-by-side with standard `run_day_simple.py`.

### Benchmarks (Recap)
- Scenario D strict (Aug 05→31): ~63% WR, +167.57 PnL.  
- Scenario E dip-reclaim (Aug 05→31): ~52% WR, +145.03 PnL.  
- Catalyst replay Aug-05:  
  - D: N=6, WR=33.3%, PnL −47.68.  
  - E: N=10, WR=50.0%, PnL +17.72.  

---

## 2. Clarifications & Decisions
- **topn=2** → cap universe to top 2 gappers after filters.  
- **rise_bars=3** → checks MACD histogram bars (3 consecutive rising).  
- **Successful project practices**:  
  - MACD line + histogram confirm.  
  - Rising green candles (2–3 in a row).  
  - Risk-perceived sizing (bet bigger on stronger setups).  
  - Multi-strategy router (A–E).  
  - 1-second candles for precision.  

---

## 3. Documentation & Roadmap
- Built **two-layer roadmap**:  
  - Tactical: push v0.3.21, baseline Scenario B, add rising candles + histogram checks, test RVOL gate.  
  - Strategic: risk-perceived sizing, router, 1-second candles, catalyst hygiene, multi-trade per ticker.  
- Generated docs:  
  - `Midas_V2_Roadmap_Full.md/.pdf`  
  - `Midas_V2_Catalyst_Log_v0.3.21.md/.pdf`  

---

## 4. Files Changed
- No core code changed today.  
- New docs added: roadmap + catalyst log.  

---

## 5. Next Steps
1. Push v0.3.21 with all docs.  
2. Run Scenario B across Aug 05→31 as baseline.  
3. Add rising green candle detection.  
4. Enforce MACD histogram `rise_bars=2–3`.  
5. Add Opening RVOL gate (≥1.5×).  
6. Prepare v0.3.22 with these upgrades.  
