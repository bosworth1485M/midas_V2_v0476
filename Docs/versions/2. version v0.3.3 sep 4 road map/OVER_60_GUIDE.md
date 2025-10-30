# Midas_V2 – Achieving Over 60% Win Rate

## Context
- **Project:** Midas_V2 (Ross Cameron–style small-cap backtester).
- **Goal:** Reach >60% win rate baseline in Scenario B.
- **Baseline Settings (Scenario B):**
  - Price: $1–20
  - Gap: 10–40%
  - TP=2.0%, SL=2.5%
  - MACD confirm ON
  - EMA+VWAP confirm
  - Gate = 10 minutes
  - Min premarket vol = 30k

---

## Lessons from Prior Projects
- **Multiple Trades per Ticker:** Earlier Cameron-style builds allowed >1 entry per symbol if setups repeated. This raised trade count *and* win rate.
- **1-Second Candles:** Switching from only 1-min bars to mixed 1-sec + 1-min improved precision (tighter pullback entries).
- **Strict Filters First:** We prioritized higher win % over more trades. Initial passes often had very few trades but >60% WR.
- **Adaptive Sizing (Later):** Higher odds setups risked more per trade (Kelly-lite). This boosted profitability once baseline WR was consistent.

---

## Roadmap to 60% WR
1. **Scenario B Stabilization**  
   - Run across multiple dates.  
   - Confirm WR hovers ~55–60% with current TP/SL = 2.0/2.5.  

2. **Dip-Reclaim Logic (Scenario E)**  
   - Enable EMA/VWAP dip reclaim with MACD confirmation.  
   - Adds safer entries after pullbacks → increased WR.  

3. **Strict Variant (Scenario D_strict)**  
   - Tighten gate to 5 minutes, keep SL at 2.5%.  
   - Designed to cut early chop and improve WR.  

4. **Multiple Trades per Symbol**  
   - Allow re-entry after fresh triggers.  
   - Boosts sample size while keeping setups consistent.  

5. **1-Second Candle Precision**  
   - Hybrid: entry logic on 1-sec, management on 1-min.  
   - Captures pullback → breakout with tighter stops.  

6. **Adaptive Sizing (Future)**  
   - Bet more on high-odds trades, cap risk per trade/day.  
   - Aim: improve profit without lowering WR.

---

## Why Not 60% Yet?
- Current Scenario B is safe but plain.  
- Missing: dip-reclaim + multiple trades + 1-sec precision.  
- These were critical in past >60% projects.  

---

## Expected Timeline
- **Weeks 1–2:** Stabilize Scenario B, confirm ~55% WR.  
- **Weeks 3–4:** Add dip-reclaim (Scenario E).  
- **Weeks 5–6:** Enable multiple trades per ticker.  
- **Week 7+:** Test 1-sec logic.  
- **Target:** >60% WR baseline by ~2 months.
