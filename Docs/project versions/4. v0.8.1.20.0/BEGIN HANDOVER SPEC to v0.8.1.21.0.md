BEGIN HANDOVER SPEC — v0.8.1.21.0

VERSION CONTEXT
- Previous version closed: v0.8.1.20.0
- v0.8.1.20.0 delivered: Trade Card is now ASCII-only, truthful, and diagnostic (no trading logic changes).
- v0.8.1.19.0 guard context (carried forward): POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD helps in trap-heavy regimes (Dec) but shows opportunity cost in trend-friendly regimes (Oct/Nov). Guard remains ON by default.

WHAT WAS PROVEN / VERIFIED IN v0.8.1.20.0
1) Trade Card completeness and truthfulness
- Entry/Exit cards now include accurate:
  - Position & risk (risk_usd, risk/share, qty)
  - Day PnL before trade (realized day-to-date, before entry)
  - Day/regime context (healthy/marginal + day gate summary)
  - Guard status (truthful booleans, no hardcoded values)
  - Post-damage diagnostics (last_damage_ts, minutes_since_damage_at_entry, per-symbol block counters)
  - Exit diagnostics (exit reason, bar-level evidence, R-multiple)
  - Hold time in minutes + bars
  - Data quality flags (dup_ts count, pos_mgmt_mismatch only when real, missing 1s CSV)
- Accounting consistency validated: trade-card PnLs reconcile to day totals and range totals; winrate matches outcomes.

KEY INSIGHT CARRIED INTO NEXT VERSION
- With the new Trade Card, late-structure / post-damage behavior is visible without TWCS.
- We can now decide whether the v0.8.1.19.0 post-damage guard should be regime-gated based on measurable day signatures, instead of intuition.

v0.8.1.21.0 — SINGLE PURPOSE
- Add day-level regime measurement so we can make an evidence-based regime-gating decision (guard ON/OFF by regime) in a later version.
- IMPORTANT: v0.8.1.21.0 is measurement-only (evaluation/observability), not strategy/behavior change.

IN SCOPE (v0.8.1.21.0)
- Observability-only addition:
  - Print one end-of-day REGIME_SUMMARY block per day (scenario B) aggregating already-available telemetry, such as:
    - universe size
    - trades executed, TP/SL counts, winrate
    - realized day PnL
    - total block counts (struct_damage, post_damage_weak_reclaim, vwap_ext, marginal_vwap_gate)
    - minutes_since_damage_at_entry distribution for executed trades (count/min/median/max)
    - data quality totals (dup_ts_total, pos_mgmt_mismatch_symbols, missing_1s_symbols)

OUT OF SCOPE (v0.8.1.21.0)
- No regime gating logic yet (no turning guards on/off conditionally)
- No changes to POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD thresholds or behavior
- No new guards
- No strategy logic changes
- No capital/account simulation
- No optimization / parameter sweeps

HYPOTHESIS FOR v0.8.1.21.0 (ONE SENTENCE)
- Trap regimes (e.g., December) will show higher early structural-damage signatures and later minutes-since-damage entries than trend-friendly regimes (Oct/Nov), and this measurement can justify future regime gating.

VALIDATION PLAN (TWO-STEP + TIME-DIVERSE)
Step 1 (sanity, small set)
- Run a small representative set:
  - Dec trap cluster (include 2025-12-04 and 2025-12-05 + 1–2 more days)
  - Oct or Nov trend cluster (3–5 days previously known to regress)
- Confirm REGIME_SUMMARY prints once per day and values reconcile with Trade Cards/day totals.

Step 2 (only if Step 1 passes)
- Run a broader range within each regime to see whether the signature separation holds.

EXIT CONDITION FOR v0.8.1.21.0
This version is complete when:
- REGIME_SUMMARY prints exactly once per day.
- Summary values reconcile with Trade Cards/day totals.
- We can conclude either:
  A) The signature clearly separates trap vs trend regimes (then v0.8.1.22.0 proposes ONE simple gating rule), or
  B) The signature does not separate (then do not gate; shift focus to the next loss class).

END HANDOVER SPEC — v0.8.1.21.0