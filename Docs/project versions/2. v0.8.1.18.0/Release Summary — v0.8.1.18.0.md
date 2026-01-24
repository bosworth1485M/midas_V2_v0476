Release Summary — v0.8.1.18.0

Healthy-Day Loss Clustering Analysis (December 2025)

Purpose

Investigate whether December 2025 losses in Scenario B were driven by healthy-classified days (close_gt_vwap_cnt ≥ 2), rather than marginal-day participation, and identify the dominant failure mechanisms responsible for multi-loss days.

Scope

Scenario: B

Period: December 2025 (subset runs)

Method: Analysis-only

No strategy, guard, sizing, or parameter changes

What Was Done

Executed December backtests using the latest codebase for full observability.

Identified multi-loss days and confirmed their day classification.

Performed TWCS (Trade-With-Candle-Snapshots) analysis on all losing trades from healthy multi-loss days.

Reviewed the following TWCS in detail:

WHLR (2025-12-05) — loss

PLRZ (2025-12-04) — loss

JFBR (2025-12-05) — loss

PAVS (2025-12-05) — loss

Key Findings
1. Losses occur on healthy days

All reviewed December losses occurred on days classified as healthy by the day gate.

This rules out marginal-day participation as the primary driver of December losses.

2. Two distinct failure classes identified

Primary failure class (dominant):
Post-damage weak VWAP reclaims

Observed clearly in WHLR and PLRZ.

Pattern:

Intraday structural damage (hard red displacement / VWAP loss)

Subsequent VWAP reclaim that is technical but weak

Entry occurs late into the reclaim

Immediate or near-immediate continuation failure

This is a structural failure, not randomness.

Secondary failure class (non-dominant):
Momentum exhaustion at highs

Observed in JFBR and PAVS.

Pattern:

Clean momentum into entry

Entry taken late in the leg

Immediate stall or rejection

Distinct from post-damage reclaim failures.

3. Hypothesis outcome

The hypothesis for v0.8.1.18.0 is supported:

December loss clustering in Scenario B is driven primarily by failure mechanisms occurring on healthy-classified days.

Conclusion

December 2025 losses in Scenario B are not explained by marginal-day trading or weak day-level confirmation.
They are driven primarily by post-damage weak VWAP reclaims on otherwise healthy days, with a smaller secondary contribution from momentum exhaustion trades.

Outcome

v0.8.1.18.0 is closed.

A clear, evidence-backed primary loss class has been identified.

Findings are sufficient to justify a single, focused structural fix in the next version.

Next Version Direction

v0.8.1.19.0 will target only the primary failure class:

Reject weak VWAP reclaims that occur after structural damage on healthy days.

Momentum exhaustion is acknowledged but explicitly out of scope for the next version.