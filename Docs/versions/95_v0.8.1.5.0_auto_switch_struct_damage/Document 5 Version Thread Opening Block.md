# Version Thread Opening Block — Midas_V2 v0.8.1.6.0
## Use this file at the start of the next session to restore exact context.

## 0) Current Status (One Screen Summary)
- Last locked / tagged version: v0.8.1.5.0 (successful)
- Current work target: v0.8.1.6.0 (planned; not implemented yet)
- Objective of v0.8.1.6.0: strengthen DAY_GATE so only days with early VWAP-accepted strength (close_gt_vwap) are tradable

---

## 1) What v0.8.1.5.0 Changed (Locked Truth)
v0.8.1.5.0 introduced a day-level auto-switch for the Structural Damage / Weak VWAP Reclaim Guard (v0.8.1.4.0).

- Base config remains: reject_reclaim_after_damage = false
- Auto-switch controls whether the guard is enabled per-day:
  - enable only if DAY_GATE passes AND close_gt_vwap_count >= 1
- Entry gating and guard logic were not changed; only guard activation timing changed.

Key outcome:
- The system now separates regimes correctly: the structural damage guard is applied only on “strong days” and not forced in hostile regimes.

---

## 2) Active Guard Inventory (Authoritative)
Refer to: Active Guards Ledger (authoritative)

Summary:
1) DAY_GATE — Always ON (regime filter)
2) VWAP Extension Gate — Always ON (location safety)
3) Structural Damage Guard — regime-dependent, controlled by v0.8.1.5.0 auto-switch
   - reject_reclaim_after_damage (base=false)
   - auto_struct_damage_from_day_gate (true)

---

## 3) Baseline Strategy Snapshot (Scenario B)
Scenario B (Gap-and-Go) uses:
- Polygon Top-gappers universe (Top-5) per day
- DAY_GATE: 20 min window, min_symbols=2 (current baseline)
- Opening RVOL gate: min_rvol_open=2.0, rvol_open_minutes=15
- Gate minutes: 20
- Entry confirms: green streak / body threshold + MACD rise
- VWAP extension gate: enabled, max_pct=1.5
- Structural damage guard: v0.8.1.4.0 (enabled per-day by v0.8.1.5.0 auto switch)
- Risk manager: per-trade risk around $35; daily_max_loss=1000; max_trades_per_symbol=1

---

## 4) Latest Results (Regime Evidence)
These month runs reflect the current baseline behavior (v0.8.1.5.0 active):

- May 2025: trades=37, WR=40.54%, PnL=-349.58
- July 2025: trades=39, WR=33.33%, PnL=-544.75
- August 2025: trades=40, WR=57.50%, PnL=+49.24
- September 2025: trades=27, WR=33.33%, PnL=-377.13

Interpretation:
- August is trend-friendly for Scenario B.
- May/July/September are hostile regimes (baseline participation loses money).
- v0.8.1.5.0 did NOT “fix” hostile months; it prevented regime-inappropriate guard forcing and revealed the true regime dependence.

---

## 5) Current Hypothesis (v0.8.1.6.0 — Locked Design)
Problem:
- Hostile months still lose money even when structural damage guard is not forced ON.
- Therefore the next fix must operate at day quality / day eligibility, not trade logic.

Hypothesis:
- If no early symbol shows VWAP-accepted strength (close_gt_vwap), the day is low expectancy and should not be traded.

Planned change (single change only):
- Strengthen DAY_GATE: require close_gt_vwap_count >= 1 for the day to PASS.
- Prevent “green_body-only” days from being tradable.

Implementation map:
- config/scenarios.json (Scenario B): set require_day_gate_close_gt_vwap=true
- engine/backtester.py: enforce this requirement in DAY_GATE decision (minimal logic), plus one config log line:
  DAY_GATE v0.8.1.6.0: CONFIG require_close_gt_vwap=<true/false>

---

## 6) Validation Workflow (Non-Negotiable)
Stage 1 — Sanity days:
- Run 2025-08-08 (expect DAY_GATE PASS, trades still occur)
- Find one prior green_body-only pass day (from logs) and verify it now FAILS (0 trades)

Stage 2 — Month ranges:
- Re-run May / July / August / September and compare vs v0.8.1.5.0

Success criteria:
- May/July/September: fewer losing days / reduced drawdown
- August: not
