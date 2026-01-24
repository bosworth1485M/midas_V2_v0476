Handover Document — Midas_V2
From v0.8.1.17.0 → v0.8.1.18.0
Regime Participation Policy Test → Healthy-Day Failure Analysis
1. Purpose of This Handover

This document formally closes v0.8.1.17.0 and defines the constraints and focus for the next version.

Its goals are to:

Lock the conclusions of v0.8.1.17.0

Prevent re-testing of rejected hypotheses

Clearly identify the next problem space

Preserve scope discipline going into v0.8.1.18.0

This handover is authoritative within the Project.

2. What v0.8.1.17.0 Definitively Established
2.1 Hypothesis Tested (and Rejected)

Tested hypothesis:

Losses in Scenario B cluster because of over-participation on marginal days; reducing participation on marginal days will reduce December loss clustering.

Result: ❌ Rejected

2.2 Key Empirical Findings

Across December 2025 testing:

All loss clusters occurred on healthy days
(close_gt_vwap_cnt ≥ 2)

Marginal days either:

produced zero trades, or

did not show loss clustering

The tested policy (stop-after-1-loss on marginal days) never activated on dominant loss days

This conclusion was reached after:

A full Dec 2–6 stress run

A Dec 1–20 diagnostic scan

Multiple single-day classifications to isolate marginal vs healthy behavior

2.3 Policy Outcome

Policy A (stop-after-1-loss on marginal days) is:

correctly implemented

safe

observable

not relevant to December loss behavior

It must not be promoted.

3. Explicit Closures (Important)

The following avenues are closed and must not be revisited without explicit reopening:

❌ Marginal-day over-participation as the primary December loss driver

❌ Marginal-day stop-after-loss policies as a December fix

❌ Further searching for “the right marginal day” in December

Continuing to pursue these would constitute fishing, not research.

4. What Remains the Dominant Problem

v0.8.1.17.0 narrows the real issue to:

Healthy-day loss clustering

Specifically:

Days that pass DAY_GATE strongly

Appear structurally valid early

Yet still produce multiple losses later in the session

This reframes the problem from:

“When should we trade less?”
to:
“Why do healthy days still fail?”

5. Authorized Direction for v0.8.1.18.0

The next version should focus only on healthy-day failure mechanisms, for example:

Late-session degradation after early strength

Post-initial-impulse exhaustion

Healthy-day over-participation or over-confidence

Structural damage that occurs after early confirmation

Time-of-day sensitivity on healthy regimes

This is a diagnostic / hypothesis-forming space, not yet a solution space.

6. Scope Constraints Carried Forward

The following rules remain in force:

One hypothesis per version

Explicit exit condition defined up front

No silent behavior changes

No unintentional regressions

Intentional trade-offs require A/B justification

Known good regimes (e.g. August-style behavior) must be protected

Entry logic and guards remain untouched unless explicitly in scope

If results become harder to explain, treat that as a warning

7. Status Summary

v0.8.1.17.0: Closed

Outcome: Negative result, hypothesis rejected

Guards changed: None

Policies promoted: None

The version is complete and successful in its purpose.

8. Instruction to the Next Version

When starting v0.8.1.18.0, begin with:

A single hypothesis explaining healthy-day loss clustering

A clear definition of what constitutes a “healthy-day failure”

A narrow test plan before any policy or guard changes

Do not carry forward marginal-day assumptions.

End of Handover Document — v0.8.1.17.0