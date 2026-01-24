Title:
Addendum — v0.8.1.24.0 Validation Results and Known Execution-Correctness Issue

1. Why this addendum exists

One short paragraph:

v0.8.1.24.0 strategy logic is validated and closed

Subsequent wide testing uncovered an existing execution-correctness bug

Bug does not invalidate the v0.8.1.24.0 strategy conclusions

Bug does contaminate some trade outcomes, so it must be fixed next

You can lift this sentence almost verbatim:

“This addendum documents additional validation results and a known execution-correctness issue discovered during wide A/B/C testing of v0.8.1.24.0. The issue is not caused by the new escape-hatch logic and is deferred to v0.8.1.25.0 as a single-change fix.”

2. Summary of completed testing (concise recap)

Bullet list is ideal:

Sanity days:

SLMT 2025-10-23 → restored by C, blocked by B, TP hit

BKYI 2025-10-27 → blocked by B and C

Familiar ranges:

2025-10-20 → 10-31

2025-11-03 → 11-07

Outcome:

Escape hatch is rare

No reintroduction of BKYI-class loss clusters

(You already have the detailed tables elsewhere; the addendum just points to them.)

3. Known issue discovered (very important section)

This should be explicit and factual:

Issue: POS_MGMT_MISMATCH due to duplicate minute timestamps

Root cause: evaluation uses raw bars, position management uses merged pos_bar_by_ts

Proof: NFE 2025-11-04 has two conflicting 15:05 rows

Impact: can flip TP/SL on affected trades

Scope: observed on SLMT 2025-10-23 and NFE 2025-11-04

Key sentence to include:

“This issue is an existing backtester correctness bug and not a regression introduced by v0.8.1.24.0.”

4. How to interpret v0.8.1.24.0 results

This protects you later:

Strategy behavior conclusions = valid

Individual PnL outcomes on contaminated days = provisional

No strategy tightening is justified based on contaminated trades

This aligns with your permanent “don’t optimize off contaminated evidence” rule.

5. Explicit handoff to v0.8.1.25.0

End the addendum with a clear baton pass:

“The next version, v0.8.1.25.0, is dedicated solely to fixing this execution-correctness issue by canonicalizing minute bars before evaluation and position management. No strategy changes are planned.”

That cleanly closes v0.8.1.24.0.