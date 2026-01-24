Handover Document
Midas_V2 — v0.8.1.12.0

Use this document to restore full context for v0.8.1.12.0 development.
This version follows a fully validated baseline (v0.8.1.11.0) and introduces one and only one new structural guard.

1. Project State at Handover
Current baseline version

v0.8.1.11.0 (tagged / ready to tag)

Scenario B only

Fully A/B validated against v0.8.1.10.0

Validation completed

Short sanity range

Full-month A/B:

August 2025

October 2025

November 2025

Results for A vs B were identical across all months

Conclusion: v0.8.1.11.0 is behavior-preserving, stable, and safe

This baseline is now trusted.

2. What v0.8.1.11.0 Achieved (Context You Must Know)

v0.8.1.11.0:

Fixed marginal-day VWAP hard suppression

Replaced it with selective VWAP delay

Preserved early junk filtering

Restored valid late continuations

Added high-quality observability logs

It did not improve profitability — by design.
It established correctness and clarity.

3. Why v0.8.1.12.0 Exists

After baseline stabilization, remaining losses were analyzed using TWCS.

Two representative SL trades were deeply inspected:

CYRX — 2025-08-06

CNEY — 2025-05-07

Both showed the same failure pattern, repeated across months:

Late VWAP reclaim after structural damage, with only a single reclaim candle and no continuation.

This pattern accounts for a large fraction of remaining SL trades.

These losses are:

not marginal-day junk

not early open noise

not execution bugs

not stop-placement errors

They are contextual structure errors.

4. Dominant Failure Class (Authoritative)
Failure definition

A trade should not exist when:

Structural damage occurred earlier in the session

Price later reclaims VWAP

Reclaim is technically valid (green, above VWAP)

But continuation strength is absent

Entry is based on one reclaim candle only

Price stalls or reverses immediately → SL

Cameron-style interpretation:

“One green candle after damage is not strength.”

This is now proven, not speculative.

5. Single Objective for v0.8.1.12.0

Strengthen VWAP reclaim continuation after structural damage.

This version must:

remove this loss class

preserve all other behavior

remain fully A/B testable

introduce exactly one new guard

6. Scope Rules (Non-Negotiable)

v0.8.1.12.0 must not:

change marginal-day logic

modify stops or targets

add new indicators

add catalysts

add Scenario D or E

add rocket-gap logic

loosen entry standards to “get more trades”

stack multiple guards

This is loss subtraction only.

7. The Guard to Implement (Conceptual, Locked)
Post-Damage VWAP Reclaim Continuation Guard

Conceptual rule:

If structural damage is present, then a VWAP reclaim must show real continuation, not just a single reclaim candle.

Recommended concrete rule (choose this one)

After structural damage, require at least 2 green closes above VWAP before entry.

Why this formulation:

Directly matches TWCS visuals

Deterministic and transparent

Does not rely on indicators

Cameron-consistent

Easy to A/B test

Explains CYRX, CNEY, BON, LOBO, etc.

⚠️ Do not combine with other formulations (green streak, MACD, etc.).
One rule only.

8. Where the Guard Applies

This guard applies only when all conditions are true:

Structural damage flag is true

Trade is a VWAP reclaim attempt

Trade is not an early open entry

Scenario is B

It must not apply to:

clean trend days without damage

early strong breakouts

future Scenario D/E logic

9. Validation Plan (Pre-Committed)

v0.8.1.12.0 must be validated exactly like prior versions.

Step 1 — Small sanity checks

Confirm CYRX- and CNEY-type trades are blocked

Confirm clean trades still occur

Step 2 — Full A/B month tests

Re-run exact same ranges already validated:

August 2025

October 2025

November 2025

Compare:

v0.8.1.11.0 (A)

v0.8.1.12.0 (B)

Success criteria (any one is sufficient)

≥30% reduction in SL trades

Meaningful PnL improvement

Clear removal of known failure trades with no regression

10. Expected Outcomes (Do Not Overpromise)

Expected:

Slightly fewer trades

Cleaner TWCS entries

Higher quality reclaims

Improved expectancy

Not required:

Immediate large profits

Elimination of no-trade days

High daily trade frequency

11. Status at Handover

Baseline is locked

Loss class is proven

Next guard is justified

Scope is tight

Risk is low

Reward is high

This is the correct moment to proceed.

12. Next Document to Write

After this handover, the next required artifact is:

v0.8.1.12.0_COPILOT_SPEC.md

That document should:

specify exact insertion point

specify exact bar logic

specify logging

forbid scope creep

include version tags in comments

End of Handover Document

Midas_V2 v0.8.1.12.0