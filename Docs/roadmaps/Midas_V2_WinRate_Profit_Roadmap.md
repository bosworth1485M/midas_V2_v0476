# Midas_V2 Roadmap — Driving Win Rate & Profitability

**Objective:** Push win rate beyond ~55% into the **60–65% range**, while maintaining **profitability** (~$500/day at ~60% WR).  

---

## 1. Market Hygiene (reduce bad symbols)
- ✅ Denylist active: drop .WS warrants, Chinese ADRs, known junk tickers.
- ✅ Negative-headline filter (e.g. loss narrows, cut guidance, downgrade).
- 🔜 Catalyst strict A-only by default (no fallback unless explicitly passed).
- 🔜 Catalyst SAFE default topn=2 (take only 2 best-scoring A-grade symbols).
- **Why this matters:** Stops us from wasting trades on low-quality names.

## 2. Entry Confirmations (filter weak setups)
- **Baseline (Scenario B):** EMA confirm, VWAP confirm, MACD line above signal, 3 rising green candles (rise_bars=3).
- **Next upgrade:** Add MACD histogram rising filter (macd_rise_bars=2–3).
- Combine with green candles streak → double confirm on both price & momentum.
- **Why this matters:** Together they catch only the strongest moves.

## 3. Volume Gating (confirm participation)
- ✅ Premarket volume min (30k baseline).
- ✅ Gate minutes (don’t trade until 10 minutes in).
- 🔜 Opening RVOL gate (min-rvol-open 1.5).
- **Why this matters:** High WR setups almost always coincide with unusual opening volume.

## 4. Trade Management (optimize risk/profit)
- ✅ TP=2.0% / SL=2.5% in Scenario B.
- 🔜 Dynamic risk sizing (future).
- 🔜 Multiple trades per symbol (future).
- **Why this matters:** Protects account while allowing more upside when odds are high.

## 5. Testing & Validation
- ✅ SAFE runners in place (simple & catalyst).
- ✅ Summaries now self-documenting.
- 🔜 Next sweep: Aug-05 to Aug-15 with Scenario B strict + RVOL + MACD slope.
- **Why this matters:** Goal = stable 60%+ WR across wide sample.

## 6. Implementation Plan
- **v0.3.21:** A-only catalysts, rise_bars=3, denylist, self-documenting summaries.
- **v0.3.22:** Catalyst SAFE default topn=2; Add macd_rise_bars param.
- **v0.3.23:** Bake in RVOL gate; sweep Aug-05 → Aug-31.
- **v0.3.24+:** Adaptive sizing, multiple trades per symbol.

## 7. Summary — Recipe for Higher Win Rate & Profit
- Trade fewer, higher-quality symbols (A-only, Top-2).
- Confirm momentum both ways: rising candles and rising MACD histogram.
- Confirm participation: opening RVOL ≥1.5.
- Manage risk tightly: TP/SL ~2.0/2.5, daily max loss $1000.
- Test across wide sample: hundreds of days needed to prove >60% WR.

---

### Next action
- Patch strategy.py to add macd_rise_bars param.
- Adjust catalyst SAFE runner to topn=2 default.
- Tag v0.3.22.
