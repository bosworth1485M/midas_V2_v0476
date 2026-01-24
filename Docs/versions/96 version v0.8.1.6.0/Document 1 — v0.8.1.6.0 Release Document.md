Document 1 — Release Document
Midas_V2 v0.8.1.6.0
DAY_GATE Enhancement: Require ≥1 close_gt_vwap Qualifier

Status: COMPLETE
Freeze Rule: Do not modify after tagging

1. Purpose of This Version

The purpose of v0.8.1.6.0 is to improve day-level trade eligibility quality by strengthening DAY_GATE so that a trading day is considered tradable only if at least one symbol demonstrates genuine VWAP-accepted strength early in the session.

This version exists because empirical testing showed:

Some days passed DAY_GATE based solely on green-body candles without true VWAP acceptance.

These “green-body-only” days often produced clusters of low-quality trades and contributed disproportionately to losses in hostile or mixed regimes.

Prior versions correctly filtered which days to trade, but did not sufficiently distinguish true acceptance from cosmetic strength.

The goal of v0.8.1.6.0 is not to improve every month, nor to address post-entry failures.
Its goal is narrowly defined:

Prevent days with no true VWAP acceptance from being traded at all.

2. What Changed (Behavioral Summary)
Before v0.8.1.6.0

DAY_GATE could pass if:

min_symbols were satisfied by any mix of:

green_body

close_gt_vwap

A day could pass DAY_GATE with:

close_gt_vwap_count = 0

green_body_count > 0

These days often looked “active” but lacked real institutional acceptance.

After v0.8.1.6.0

DAY_GATE passes only if:

all existing DAY_GATE conditions pass and

close_gt_vwap_count ≥ 1

Green-body-only days are now explicitly rejected.

This change:

reduces participation on marginal days

preserves strong days

moves regime filtering earlier in the pipeline

3. Final DAY_GATE Rule (v0.8.1.6.0)

A trading day is eligible only if:

Existing DAY_GATE logic passes (unchanged), and

At least one symbol passes DAY_GATE via the rule:

close_gt_vwap

Formally:

DAY_GATE_PASS =
    existing_day_gate_pass
    AND close_gt_vwap_count >= 1


If the condition fails:

DAY_GATE: FAILED reason=no_close_gt_vwap_qualifier


This decision is logged clearly and once per day.

4. Files Changed (Exact and Limited)
config/scenarios.json

Scenario B only

Change:

"require_day_gate_close_gt_vwap": true


No other scenarios modified.

No reformatting or reordering.

src/midas_v2/engine/backtester.py

Changes strictly limited to:

Reading the existing require_day_gate_close_gt_vwap flag

Enforcing the failure when close_gt_vwap_count == 0

Adding one observability log line:

DAY_GATE v0.8.1.6.0: CONFIG require_day_gate_close_gt_vwap=<true|false>


Explicit non-changes:

DAY_GATE scanning logic unchanged

Indicator logic unchanged

Entry logic unchanged

Structural damage guard unchanged

VWAP extension gate unchanged

Risk sizing unchanged

5. Tests Performed
5.1 Single-Day Sanity Tests

2025-05-08 (Representative Mixed Day)

close_gt_vwap_count = 1

DAY_GATE passed

Trades occurred

Behavior identical to baseline
Result: PASS (no regression)

5.2 Month-Level A/B Testing (OFF vs ON)
May 2025

OFF:

Trades: 37

PnL: −349.58

ON:

Trades: 33

PnL: −335.47

Finding:

One losing day (2025-05-13) removed

Net improvement without harming winners

July 2025

OFF:

Trades: 39

PnL: −544.75

ON:

Trades: 29

PnL: −447.00

Finding:

10 trades removed

~+97.75 PnL improvement

Remaining losses occur on days with true early acceptance

April 2025 (Out-of-Sample Confirmation)

Trades: 37

Win rate: 45.95%

PnL: −224.22

Finding:

Many zero-trade days (DAY_GATE working)

Losses clustered on tradable days

TWCS confirms losses are post-entry expansion failures, not DAY_GATE failures

6. TWCS Findings (Critical)

TWCS analysis across multiple months confirms:

Blocked Correctly by v0.8.1.6.0

Days with:

green-body activity

no VWAP-accepted closes

These days show:

choppy price

poor continuation

low expectancy

Not Addressed by This Version (By Design)

TWCS shows remaining losses are dominated by:

Valid acceptance

Valid entry

Failure to expand after entry

Examples:

WGRX — 2025-05-08

LHAI — 2025-07-25

ABVE — 2025-07-11

ARBB — 2025-04-15

These are post-entry expansion failures, not day-selection failures.

7. Findings and Interpretation

v0.8.1.6.0 successfully improves day selection quality

It removes an entire class of low-quality trading days

It does not attempt to solve post-entry failures

The remaining loss bucket is now clearly isolated and well-defined

This is the desired outcome of a disciplined version.

8. Final Conclusion

v0.8.1.6.0 is successful.

It:

improves DAY_GATE precision

reduces losses in hostile regimes

preserves strong days

clarifies the next problem to solve

It should be:

locked

tagged

treated as the new baseline for Scenario B

9. Explicit Next Step (Not Implemented Here)

The evidence from this release directly motivates the next version:

v0.8.1.7.0 — Post-Entry Expansion Confirmation

This version will target continuation failure after valid entries, which is now the dominant remaining failure class.

Please review and comment:

Any section you want tightened or expanded

Whether April should remain in this release or be referenced only in PROJECT_STATUS.md

Wording around “success” vs “partial success”

Once you approve, this can be frozen as Document 1 for v0.8.1.6.0.