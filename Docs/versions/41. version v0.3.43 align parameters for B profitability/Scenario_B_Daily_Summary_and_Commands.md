# Scenario B – Daily Summary & Commands

## ✅ What We Did Today

### 1. Adaptive Sizing
- Built `B_profit_v2_sized.json` profile with:
  - TP = 2.0%
  - SL = 2.0%
  - Partial 60% at +1.0%
  - Move stop to breakeven
  - Time stop = 2 minutes
  - Adaptive sizing fields: `per_trade_risk=50`, `daily_max_loss=1000`, `max_trades_per_symbol=1`

### 2. Profile Workflow
- Profiles are kept in `config/`:
  - `scenarios_B_profit_v1.json`
  - `scenarios_B_profit_v2_sized.json`
- We run via `--profile` to swap the right config in before backtesting.

### 3. Catalyst Score
- Confirmed `score=3` never appears in current enrich output (only 0/1/2).
- For now, baseline remains `--news-min-score 2`.
- Plan: patch scorer to emit 3 for A-grade catalysts later.

### 4. Next Steps
- Run August using `B_profit_v2_sized`.
- Compare against V1.
- If negative, rerun with stricter filters (Top-2, gate=20, score ≥3, RVOL ≥2.2).
- Add further enhancements in next version (guardrails, reclaim triggers, trailing stops).

---

## 🖥️ Commands We Used

### Run B V1 (sized)
```bash
python scripts\run_catalyst_flow.py --date 2025-08-05 --profile B_profit_v1 --profile-v1-path config\scenarios_B_profit_v1.json --profile-v2-path config\scenarios_B_profit_v2.json --news-first --require-news --news-min-score 2 --deny-negative --exclude-china --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --compare
```

### Run B V2 (sized, adaptive)
```bash
python scripts\run_catalyst_flow.py --date 2025-08-05 --profile B_profit_v2 --profile-v2-path config\scenarios_B_profit_v2_sized.json --news-first --require-news --news-min-score 2 --deny-negative --exclude-china --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --compare
```

### Analyze Results
```bash
python scripts\analyze_august_profit_v2.py --scenario B --label B_profit_v1 --by-day
python scripts\analyze_august_profit_v2.py --scenario B --label B_profit_v2 --by-day
```

### Strict Filter Run Example (profit push preset)
```bash
python scripts\run_catalyst_flow.py --date 2025-08-05 --profile B_profit_v2 --profile-v2-path config\scenarios_B_profit_v2_sized.json --news-first --require-news --news-min-score 3 --deny-negative --exclude-china --top 2 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.2 --gate-minutes 20 --compare
```

---

## 📌 To Do in Next Version
- Patch scorer to allow `score=3` for A-grade catalysts.
- Add reclaim-only triggers, MACD rise hard-gate, and micro-pullback entries.
- Add portfolio heat guard, first-loss throttle, green-day lock.
- Add optional trailing stop on runner.
