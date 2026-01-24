Handover Specification
Midas_V2 — v0.8.1.5.0
Day / Regime Switch for Structural Damage Guard
1. Context from Previous Version (v0.8.1.4.0)
What v0.8.1.4.0 Achieved

Implemented a Structural Damage / Weak VWAP Reclaim Guard

Successfully blocked the canonical failure:

SPRU — 2025-08-08 @ 11:14

Guard logic was validated via:

TWCS diagnosis

Single-day sanity (Aug-08)

Small cluster (Aug-06 → Aug-09)

Full August range (profitable)

July and September ranges (unprofitable)

Empirical Conclusion

The guard is correct but regime-dependent:

Month	Result with Guard ON
July 2025	–$600.60
August 2025	+$41.88
September 2025	–$377.13

Key insight:

The problem is no longer what the guard does, but when it should be enabled.

v0.8.1.4.0 is therefore frozen and treated as a conditional structural tool, not a permanent baseline.

2. Purpose of v0.8.1.5.0
Single, Narrow Objective

v0.8.1.5.0 introduces a DAY-LEVEL / REGIME-LEVEL SWITCH that decides whether the Structural Damage Guard should be enabled for the current trading day.

This version does not:

change the structural guard logic

tune thresholds

add new indicators

attempt to improve July or September directly

It answers one question only:

“Is today strong enough that rejecting weak VWAP reclaims improves expectancy?”

3. Core Hypothesis (Locked)

Enable reject_reclaim_after_damage only on days that show early follow-through strength; otherwise keep it OFF.

This hypothesis is derived directly from:

August vs July/September evidence

Existing DAY_GATE signals

TWCS structural interpretation

4. Allowed Inputs (Strictly Limited)

v0.8.1.5.0 must use existing signals only.

Primary Signal Source

DAY_GATE output, specifically:

whether the day passes or fails

how it passed (rule type)

No new indicators, data feeds, or calculations are allowed.

5. Recommended Decision Rule (Initial Proposal)
Structural Damage Guard AUTO-ENABLE rule:

Enable reject_reclaim_after_damage for the day if:

DAY_GATE passes, AND

At least one symbol passed DAY_GATE via:

close_gt_vwap

(not merely green_body)

Rationale:

Requires at least one symbol to be clearly strong above VWAP

Matches the original structural intuition behind v0.8.1.4.0

Uses already-logged information

Simple, explainable, testable

This rule is a starting hypothesis, not guaranteed to be final.

6. Operational Requirements (Non-Negotiable)
6.1 Default State

In scenarios.json:

"reject_reclaim_after_damage": false


v0.8.1.5.0 logic decides whether to override this at runtime per day

6.2 Runtime Transparency

The system must always log:

Manual flag state

Auto-decision result

Reason for the decision

Example:

STRUCT_DAMAGE v0.8.1.5.0: CONFIG base=false auto_enabled=true reason=day_gate_close_gt_vwap


This is critical for:

debugging

A/B testing

future TWCS interpretation

6.3 Reversibility

Manual override must remain possible

Auto-enable logic must be easy to disable for testing

No hidden state

7. Validation Plan (Mandatory)

v0.8.1.5.0 must follow the two-stage validation workflow.

Stage 1 — Sanity Checks

One August-like day → guard should auto-enable

One July or September-like day → guard should stay off

Confirm:

decision matches intuition

logs are correct

no crashes or silent behavior

Stage 2 — Range Validation

Run full ranges with auto-switch enabled:

July 2025

August 2025

September 2025

Expected outcomes:

July & September improve vs v0.8.1.4.0 ON

August remains close to v0.8.1.4.0 ON

Overall expectancy improves or stabilizes

8. Success Criteria

v0.8.1.5.0 is successful if:

Structural guard is enabled selectively

July/September drawdowns are materially reduced

August profitability is preserved

Behavior is explainable from logs alone

No new failure class is introduced

9. Explicit Non-Goals

This version must not:

invent a new structural pattern

add complexity beyond the day switch

tune thresholds inside the damage guard

optimize for a specific month

touch TWCS logic

10. Relationship to the Active Guards Ledger

After v0.8.1.5.0:

The Structural Damage Guard entry in the ledger will be updated to:

include auto-enable conditions

DAY_GATE and Structural Guard interaction will be documented explicitly

11. One-Sentence Summary for the Version Thread

v0.8.1.5.0 introduces a day-level regime switch that automatically enables the structural damage guard only on days with early follow-through strength, based on existing DAY_GATE evidence.

12. Next Action

Before starting implementation:

Confirm reject_reclaim_after_damage is OFF in scenarios.json

Tag and archive v0.8.1.4.0

Begin v0.8.1.5.0 with this spec as the sole scope