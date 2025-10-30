# Scenario B – Profitability Roadmap

## ✅ What We Did Today

### Adaptive Sizing Added
- Built **B_profit_v2_sized** profile:
  - TP = 2.0%, SL = 2.0%
  - Partial 60% at +1.0%, then move stop to BE
  - Time stop = 2 minutes
  - Adaptive sizing fields:
    - `per_trade_risk=50`
    - `daily_max_loss=1000`
    - `max_trades_per_symbol=1`

### Profile Workflow
- Profiles live in `config/`:
  - `scenarios_B_profit_v1.json`
  - `scenarios_B_profit_v2_sized.json`
- Run via:
  ```
  python scripts\run_catalyst_flow.py --date YYYY-MM-DD --profile B_profit_v2 --profile-v2-path config\scenarios_B_profit_v2_sized.json --news-first --require-news --news-min-score 2 --deny-negative --exclude-china --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --compare
  ```

### Testing August
- Run V1 and V2 across August (weekday loop).
- Use analyzer (`analyze_august_profit_v2.py`) to total PnL, WR, TP/SL counts.
- Confirm if V2 beats V1 in profitability and drawdown.

### Notes
- **D/E scenarios**: situational, not consistently more profitable than B.
- **Score=3 catalysts**: your scorer never emits them → `--news-min-score 3` produces 0 trades with current code.

---

## 🚀 Next Version – How to Make B More Profitable

### A. Trade Management
- Trailing stop on runner portion (1m bar low or EMA9).
- Time stop adjustable: 2–3 minutes.

### B. Universe Filters
- **Top-N**: 3 → 2.
- **Gate**: 15 → 20 minutes.
- **Opening RVOL**: 2.0 → 2.2.
- **Catalyst strength**: news score ≥ 3 (after patching scorer).
- Continue: deny-negative, exclude-China, enforce band 10–40%.

### C. Guardrails
- Portfolio heat cap: ≤ 2 concurrent positions OR ≤ 3R total risk.
- First-loss throttle: halve R after first full loser of the day.
- Green-day lock: stop after +2R realized.

### D. Entry Quality
- Add reclaim-only entries (EMA/VWAP reclaim).
- MACD histogram rising hard-gate (rise_bars ≥ 2).
- Micro-pullback trigger near reclaim.

### E. Data Hygiene
- Premarket volume min (≥30k–50k).
- Auto-skip no-data/holiday days.

### F. Future Enhancement
- Tiered risk sizing (Kelly-lite):
  - A-grade catalyst (score ≥3 & RVOL ≥2.2): 1.5R
  - Normal (score=2 & RVOL ≥2.0): 1.0R
  - Marginal: 0.5R or skip

---

## 📌 Next Actions
1. Run August with **B_profit_v2_sized**.
2. Compare with V1.
3. If still negative → rerun with stricter filters (Top-2, gate=20, score ≥3, RVOL ≥2.2).
4. After locking B V2 + adaptive sizing, add guardrails + reclaim trigger + trailing stop in next version.
