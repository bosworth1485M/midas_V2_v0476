Test Plan Addendum — v0.8.1.23.0 (A/B Validation)
Purpose

Validate the POST_DAMAGE_ENTRY_LOCKOUT (structure-first, same-day lockout) using strict A/B testing on identical datasets, ensuring loss reduction without suppressing legitimate winners.

A/B Definition

A (Baseline):
Commit 1e48efb — trusted memory-stick baseline (hostile-only reclaim logic, no lockout)

B (Candidate):
v0.8.1.23.0 — adds POST_DAMAGE_ENTRY_LOCKOUT (block all post-damage entries regardless of regime)

Only one behavioral change differentiates A and B.

Step 1 — Sanity Validation (Must Pass)

Run single-day ranges (still using the range runner for consistency):

2025-10-23 (SLMT winner day)

Expected (A & B): SLMT trade occurs and remains a TP

Guard must not trigger (no prior structural damage)

2025-10-27 (BKYI loss day)

Expected (A): BKYI entry occurs and loses

Expected (B): BKYI entry is blocked

Required evidence: [WHY] v0.8.1.23.0 POST_DAMAGE_ENTRY_LOCKOUT …

2025-12-05 (hostile December day)

Confirm guard triggers make sense

Ensure no crashes, infinite blocks, or unintended side effects

If any sanity check fails → stop and fix before range testing.

Step 2 — Primary Range Tests (Canonical)

These are the canonical time-diverse ranges already used in prior versions:

October (mixed regime)

2025-10-20 → 2025-10-31

December (hostile-heavy)

2025-12-02 → 2025-12-06

Run both ranges for A and B, capturing full logs and summaries.

Step 3 — Additional Confirmation Ranges (Recommended)

These reduce overfitting to the primary windows:

Adjacent October week

2025-10-13 → 2025-10-17
Purpose: confirm behavior outside the late-October pocket.

Different December week

2025-12-08 → 2025-12-12
Purpose: confirm December behavior is consistent, not week-specific.

Low trade counts are acceptable and informative.

Metrics to Compare (A vs B)

Primary:

Total PnL

Win rate

Number of trades

Number of same-bar / 0-bar losses

Secondary (diagnostic):

Count of POST_DAMAGE_ENTRY_LOCKOUT blocks

Distribution of blocked entries by day

TWCS confirmation for any blocked winners (if any)

Pass / Fail Criteria

Promote v0.8.1.23.0 if all are true:

BKYI-class failures are blocked in sanity tests

SLMT-class winners remain allowed

One of the following holds on ranges:

≥ +3pp win rate improvement, or

Net PnL improvement, or

Clear reduction in clustered losses / immediate SLs

Reject or refine if:

Legitimate winners are blocked, or

No measurable improvement is observed.

Version Exit Rule

Once the above tests are completed and evaluated:

Declare KEEP / REJECT / REFINE

Record outcome in:

PROJECT_STATUS.md

ACTIVE_GUARDS_LEDGER.md

Close v0.8.1.23.0 before starting any new hypothesis.

End of Test Plan Addendum