Document 2 — Handover Specification (Revised, Detailed)
Midas_V2 v0.8.1.6.0
Use this file at the start of the next version thread to restore context and implement safely.
1. Current Locked State (Do Not Change)
Locked version

v0.8.1.5.0 — Day-level auto-switch for Structural Damage Guard

This version is complete, validated, and must remain unchanged.

What is now known to be true

From multi-month testing:

Month	Trades	Win Rate	PnL	Interpretation
May 2025	37	40.54%	–349.58	Hostile / mixed
July 2025	39	33.33%	–544.75	Hostile
August 2025	40	57.50%	+49.24	Trend-friendly
September 2025	27	33.33%	–377.13	Hostile

Key facts that should not be re-argued:

Structural Damage Guard is correct but regime-dependent

v0.8.1.5.0 successfully makes it conditional

Remaining losses in May/July/September are baseline participation losses

The next fix must act before entries, not inside them

2. Why v0.8.1.6.0 Exists

After v0.8.1.5.0:

Bad months lose money even when the structural guard is mostly OFF

This means the issue is day quality, not entry structure

Current DAY_GATE allows days that:

barely pass via green_body

show no VWAP-accepted strength

still generate multiple losing trades

Therefore the next hypothesis must:

Reduce participation on low-quality days without touching trade logic or harming August.

3. Core Hypothesis (Locked)

If no symbol shows early VWAP acceptance (close_gt_vwap), the day is low-expectancy and should not be traded.

A day that passes DAY_GATE only via green_body is insufficient evidence of real momentum.

4. Exact Behavioral Change Proposed
Current DAY_GATE behavior

In engine/backtester.py, DAY_GATE can PASS when:

passed_symbols >= min_symbols

regardless of whether passes came from:

close_gt_vwap

or green_body

New behavior for v0.8.1.6.0

DAY_GATE may PASS only if:

Existing DAY_GATE conditions are satisfied
AND

close_gt_vwap_count >= 1

Effect:

Green-body-only days become non-tradable

Days with at least one VWAP-accepted symbol remain tradable

No other logic changes.

5. Files / Scripts Involved (Implementation Map)
5.1 config/scenarios.json

Scenario B only

Existing key already supported by code:

"require_day_gate_close_gt_vwap": false


v0.8.1.6.0 will set this to:

"require_day_gate_close_gt_vwap": true


No new keys introduced.
No other scenarios touched.
No formatting or ordering changes allowed.

5.2 src/midas_v2/engine/backtester.py

Important:
DAY_GATE already computes:

close_gt_vwap_count

green_body_count

And already supports the concept of require_day_gate_close_gt_vwap.

What may need to change

Ensure the require_day_gate_close_gt_vwap flag is:

correctly read from Scenario B params

actively enforced in the DAY_GATE PASS/FAIL decision

What must NOT change

DAY_GATE bar scanning logic

Thresholds (minutes, min_symbols)

Rule definitions (close_gt_vwap, green_body)

Logging formats for existing DAY_GATE lines

v0.8.1.5.0 auto-switch logic

Structural Damage Guard logic

Entry gating logic

5.3 Logging Requirements (Minimal, Explicit)

To make behavior obvious:

DAY_GATE logs must make it clear whether require_day_gate_close_gt_vwap is active

Preferred (minimal) approach:
Add one config log line near DAY_GATE start:

DAY_GATE v0.8.1.6.0: CONFIG require_close_gt_vwap=<true/false>


No other logging changes.

6. Validation Plan (Must Be Followed Exactly)
Stage 1 — Single-day sanity

2025-08-08

Expect DAY_GATE to PASS

Expect trades to still occur

Identify a historical “green-body-only” day (from logs in May/July)

Expect DAY_GATE to now FAIL

Expect zero trades

Stage 2 — Month ranges

Run Scenario B with v0.8.1.6.0:

May 2025

July 2025

August 2025

September 2025

Compare vs v0.8.1.5.0.

7. Success Criteria (Quantitative + Qualitative)

v0.8.1.6.0 is successful if:

May/July/September:

fewer losing trade days

materially smaller drawdowns

August:

remains profitable or close to baseline

Logs alone explain why days are skipped

No unintended suppression on strong days

8. Explicit Non-Goals

This version must not:

Tune indicators

Add new guards

Modify auto-switch logic

Change risk sizing or exits

Attempt to “fix” hostile regimes at trade level

9. One-Sentence Version Summary

v0.8.1.6.0 strengthens DAY_GATE by requiring at least one early VWAP-accepted symbol to trade the day, preventing green-body-only days from being tradable.

10. Status

v0.8.1.5.0 → locked

v0.8.1.6.0 → designed, not implemented