# Midas_V2 Roadmap: Tactical & Strategic

## Tactical Roadmap (Next 1–2 Versions)
- Current version: **v0.3.21** (about to push).
- Tested Scenario B on 2025‑08‑05 → no trades taken.
- Scenario D strict earlier: ~63% WR, +167.57 PnL.
- Scenario E dip‑reclaim: ~52% WR, +145.03 PnL.
- Catalyst logic in place but still rough (A‑grade ≥2 best).
- **Immediate steps:**
  1. Push v0.3.21 to GitHub.
  2. Run Scenario B for Aug 5–31 baseline.
  3. Add rising green candle detection.
  4. Enforce MACD histogram rise_bars=2–3.
  5. Test with Opening RVOL gate (≥1.5×).
  6. Prepare v0.3.22 with these upgrades.

## Strategic Roadmap (Future 1–3 Months)
### 1. Adaptive Risk‑Perceived Sizing
- Bet more when odds are better:
  - A‑grade catalysts, strong MACD/EMA/VWAP alignment, clean Top‑N.
- Guardrails:
  - Per‑trade cap (e.g., 2% of equity).
  - Daily loss cap ($1k).
  - Drawdown throttles.
- Goal: scale to ~$500/day profit with controlled risk.

### 2. Multi‑Strategy Integration
- Build a **Scenario Router** that merges A–E:
  - Prioritize strongest setups (D strict > E dip).
  - Allow one trade per ticker per strategy, but risk‑split across.
- Later: multiple trades per ticker when setups repeat (scalp + reclaim).

### 3. Precision & Timeframes
- Progression:
  - Start: 1‑minute entries.
  - Upgrade: 1‑second candles for tighter fills & better WR.
  - Allow mixing 1m charts (trend confirm) with 1s charts (entry).

### 4. Catalyst & Universe Hygiene
- Always prefer A‑grade (score ≥2).
- B‑grade only to fill Top‑N if list is too small.
- Exclude weak/unreliable tickers (e.g., Chinese ADRs).
- Keep raw top‑gappers separate from catalyst universes for testing.

### 5. Profitability Milestone Targets
- Win Rate goal: ≥60%.
- Average TP/SL: 2.0 / 2.5%.
- Trade count: 4–5 per day.
- Daily profit: ~$500 baseline.
- Monthly stretch target: $50k with adaptive sizing & router.

---

## Summary
- **Short‑term**: push v0.3.21, baseline Scenario B, add rising green bars + histogram checks, then move to v0.3.21.  
- **Long‑term**: adaptive risk‑sizing, scenario router, 1‑second entries, catalyst hygiene, and multi‑trade per ticker.  
- This two‑layer roadmap ensures we don’t lose sight of the **future vision** while keeping tomorrow’s work clear.  
