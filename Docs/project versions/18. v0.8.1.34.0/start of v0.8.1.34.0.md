Handover — Start of v0.8.1.34.0
Use this document to restore full context at the beginning of the next version.
Last completed version

v0.8.1.33.0 — Marginal VWAP Gate Relaxation

What was done in v0.8.1.33.0 (locked)

Relaxed MARGINAL_VWAP_GATE from 2-of-3 → 1-of-3 completed candles above VWAP.

Single behavior change only.

No new guards, no refactors, no sizing changes.

What was proven (do not re-litigate)
Good regime (Sanity cluster)

Dates tested:

2025-08-05

2025-08-06

2025-08-07
Scenario: B

Observed behavior:

Participation restored on 2025-08-06 (previously zero-trade under v0.8.1.32.0).

Losses were small and explainable.

Confirms marginal VWAP gate was a real participation bottleneck on good days.

Hostile regime (Protection cluster)

Dates tested:

2025-12-02

2025-12-03

2025-12-04

2025-12-05
(2025-12-06 skipped — weekend)
Scenario: B

Observed behavior:

Zero trades across all tested days.

No increase in losses, no unsafe entries.

Confirms marginal VWAP relaxation does not weaken hostile-day safety.

Conclusion for v0.8.1.33.0

Change is accepted and kept.

System now:

Trades selectively in good regimes

Remains flat in hostile regimes

Remaining December zero-trade days are not caused by marginal VWAP logic.

Current project state (important)

Participation suppression has moved earlier than VWAP logic.

Structural damage, VWAP reclaim, and extension gates remain intact and effective.

The system is behaving safely but is still over-throttled in hostile regimes.

Open problem carried forward

Despite v0.8.1.33.0:

December 2025 continues to show persistent zero-trade days.

Suppression likely originates from:

DAY_GATE behavior, and/or

CONFIRM_BAR strictness

This is an alignment issue, not a bug.

Next version scope (v0.8.1.34.0)

One hypothesis only. No stacking.

Candidate hypothesis (to be chosen explicitly at version start)

Participation suppression in December 2025 is caused by DAY_GATE and/or CONFIRM_BAR interaction, not VWAP logic.

Only one of the following may be adjusted:

DAY_GATE consequence or timing
or

CONFIRM_BAR strictness

Not both.

Explicit non-goals for v0.8.1.34.0

No VWAP logic changes

No post-damage logic changes

No new indicators

No sizing or risk changes

No refactors

Required validation pattern (must follow)
Sanity cluster (must show participation):

2025-08-05 → 2025-08-07 (Scenario B)

Protection cluster (must remain safe):

2025-12-02 → 2025-12-05 (Scenario B)

All losses must receive immediate TWCS review.

Alignment status

Work remains fully aligned with Cameron Alignment Plan

No update to the Alignment Plan is required

Continue strict one-change-per-version discipline

Start condition for v0.8.1.34.0

Before writing any code, state explicitly in the version thread:

“This version tests whether DAY_GATE or CONFIRM_BAR strictness is suppressing participation in December 2025, using Aug 05–07 as sanity and Dec 02–05 as protection.”