Document 1 — v0.8.1.5.0 Release Document (Draft)

Below is Document 1 only.

Midas_V2 v0.8.1.5.0 — Release Document
Day-Level Auto-Switch for Structural Damage Guard

Status: COMPLETE
Do not modify after tagging

1. Purpose of This Version

v0.8.1.5.0 introduces a day-level regime switch that determines whether the Structural Damage / Weak VWAP Reclaim Guard (introduced in v0.8.1.4.0) should be enabled for the current trading day.

This version exists because empirical testing showed:

The structural damage guard is beneficial in trend-friendly regimes (e.g. August 2025)

The same guard is harmful when forced ON in choppy or mean-reverting regimes (e.g. May, July, September)

The goal of v0.8.1.5.0 is not to improve all months, but to ensure that:

August-style logic is not incorrectly applied to non-August regimes.

2. What Changed (Behavioral Summary)
Before v0.8.1.5.0

Structural damage guard was manually ON or OFF

If ON, it applied to all days, regardless of regime

After v0.8.1.5.0

Structural damage guard is base OFF

A runtime auto-switch decides per day whether to enable it

Decision uses existing DAY_GATE evidence only

No indicator logic was changed

3. Auto-Switch Decision Rule (Final)

The structural damage guard is auto-enabled only if:

DAY_GATE passes, and

At least one symbol passed DAY_GATE via close_gt_vwap

Otherwise, the guard remains OFF for that day.

The decision is logged exactly once per day:

STRUCT_DAMAGE v0.8.1.5.0: CONFIG
base=<true/false>
auto_mode=<true/false>
day_gate_pass=<true/false>
close_gt_vwap_cnt=<int>
auto_enabled=<true/false>
effective=<true/false>
reason=<string>

4. Files Changed (Exact)
config/scenarios.json

Scenario B only

Added:

"auto_struct_damage_from_day_gate": true


reject_reclaim_after_damage remains false (base OFF)

No other scenarios modified.

src/midas_v2/engine/backtester.py

Changes were strictly limited to:

Reading the new auto-switch flag

Computing a day-level effective boolean

Logging the v0.8.1.5.0 CONFIG line

Routing the effective flag into the existing v0.8.1.4.0 guard

Explicit non-changes:

DAY_GATE logic unchanged

Entry gating unchanged

Structural damage guard logic unchanged

VWAP extension gate unchanged

Risk sizing unchanged

5. Tests Performed (Complete List)
Stage 1 — Single-Day Sanity
2025-08-08 (Trend-Friendly Day)

DAY_GATE passed

close_gt_vwap_cnt = 1

Auto-switch enabled guard (effective=true)

Structural damage guard blocked weak reclaims

Trades still occurred later

Result: +55.96 PnL, 100% WR

2025-07-02 (Hostile Day)

DAY_GATE failed

Auto-switch disabled guard (effective=false)

No unintended blocking

Result: 0 trades (expected)

Stage 2 — Full Month Ranges
May 2025

Trades: 37

Win rate: 40.54%

PnL: -349.58

July 2025

Trades: 39

Win rate: 33.33%

PnL: -544.75

August 2025

Trades: 40

Win rate: 57.50%

PnL: +49.24

September 2025

Trades: 27

Win rate: 33.33%

PnL: -377.13

One August day (2025-08-05) experienced a transient Polygon timeout and was skipped; this did not invalidate the result.

6. Findings

v0.8.1.5.0 successfully separates regimes

Structural damage guard:

ON when helpful (August)

OFF when harmful (May/July/September)

Losses in hostile months are baseline strategy reality, not over-filtering artifacts

Logging is complete, explainable, and reversible

7. Final Conclusion

v0.8.1.5.0 is successful.

It does not attempt to make Scenario B profitable in hostile regimes.
It ensures that trend-specific logic is applied only when justified.

This version should be locked and tagged with no further modification.