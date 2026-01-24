Handover Document — v0.8.1.18.0 → v0.8.1.19.0
Context

Version v0.8.1.18.0 was an analysis-only investigation into December 2025 losses in Scenario B. Trades were executed normally, and conclusions were drawn using TWCS evidence, not metrics alone.

The version is now closed.

What Is Now Known (Do Not Re-Investigate)

December losses occur on healthy days

All reviewed losses occurred on days classified as healthy (close_gt_vwap_cnt ≥ 2).

Marginal-day participation is not the cause of December underperformance.

Two failure classes exist

Primary (dominant):
Post-damage weak VWAP reclaims

Structural damage → weak/late reclaim → entry → fast failure

Confirmed by TWCS: WHLR (12-05), PLRZ (12-04)

Secondary (non-dominant):
Momentum exhaustion at highs

Late-in-leg entries that immediately stall

Confirmed by TWCS: JFBR (12-05), PAVS (12-05)

Primary loss class is structural

Failures are not random.

Failures are visually obvious in TWCS.

This class is a valid target for loss subtraction.

What Is Explicitly Out of Scope Next

Momentum exhaustion fixes

Day-gate changes

Marginal-day logic

Sizing changes

Exit logic changes

Multi-idea experimentation

These must not be mixed into the next version.

Next Version Intent
Version

v0.8.1.19.0

Goal

Prevent entries that occur after intraday structural damage when the subsequent VWAP reclaim lacks real continuation strength — even on healthy days.

Targeted Failure Shape (must match TWCS)

Structural damage precedes entry

VWAP reclaim is:

late

overlapping

low momentum

lacking a fresh impulse candle

Entry occurs after this weak reclaim

Continuation fails quickly (≤ a few minutes)

Non-Goals

Do not block:

clean impulse reclaims

first strong push after damage

non-damage momentum trades

Exit Condition for v0.8.1.19.0

The next version may close when:

TWCS confirms that blocked trades match the WHLR / PLRZ failure shape, and

A small sanity run shows:

reduced healthy-day losses

no obvious collateral damage

Only after that should broader December testing occur.

Handover Summary (one sentence)

v0.8.1.19.0 will introduce a single, narrow guard to block weak VWAP reclaims that occur after structural damage on otherwise healthy days, targeting the primary December loss cluster identified in v0.8.1.18.0.