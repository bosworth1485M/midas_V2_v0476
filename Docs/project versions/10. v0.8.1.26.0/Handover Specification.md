Handover Specification
From v0.8.1.26.0 → Next Version (Cameron Alignment Execution)
1. Context Restoration (READ FIRST)

This handover follows v0.8.1.26.0, which was a strategic reset version.

No strategy logic was changed in v0.8.1.26.0.

Instead, this version formally established an authoritative strategy document:

Docs/0. strategy/CAMERON_ALIGNMENT_PLAN.md

This document is now the non-negotiable source of truth for:

Project intent

Definition of successful Cameron-style behavior

Scenario B’s intended role

The multi-version alignment roadmap

Any work in the next version must conform to that plan.
If a proposed change contradicts it, the plan must be revised first.

2. What Was Proven Before This Handover
2.1 Execution Correctness

Execution, data, and scenario wiring are correct

Scenario A executes trades normally

Scenario B can trade (e.g., October 2025)

There is no execution or backtester bug

2.2 Root Cause of Scenario B Under-Trading

Empirical testing (Oct–Dec 2025) proved that:

DAY_GATE frequently fails early follow-through checks

Failure triggers EARLY_REJECT(DAY_GATE_FAILED) at ~09:30

Entire trading days are shut down for Scenario B

This produces multi-week and multi-month zero-trade periods

This behavior is intentional, not accidental.

2.3 Strategic Conclusion

Current Scenario B behavior does not emulate successful Cameron projects

The issue is behavioral misalignment, not software failure

The misalignment is caused by DAY_GATE acting as a hard global kill switch

3. Authoritative Objective of the Next Version

Restore Scenario B behavior to emulate the most successful Cameron-style projects, without reintroducing known loss classes.

Per the Alignment Plan, this is done incrementally, starting with the root cause.

4. Scope of the Next Version (LOCKED)
4.1 Primary Change (ONE ONLY)

Convert DAY_GATE consequence for Scenario B from hard block → throttle.

This is an ALIGNMENT change.

What this means concretely:

DAY_GATE classification logic stays intact

Healthy / Marginal / Hostile

Follow-through detection

Telemetry and logging

Global early-reject must be removed for Scenario B

No EARLY_REJECT(DAY_GATE_FAILED) that shuts down the entire day

DAY_GATE outcome must instead:

Reduce participation and/or risk

Not silence trading entirely

The exact throttle mechanism (e.g., max trades, risk scaling) must be:

Explicit

Logged

Deterministic

Easy to A/B test

4.2 Explicit Non-Changes (Critical)

The following must not change in the next version:

MACD logic

RVOL thresholds

VWAP logic

rise_bars / candle structure

TP / SL

Position sizing model (except throttle effect if explicitly chosen)

Any other guards

If more than one conceptual lever is changed, the version is invalid.

5. Required Classification of the Change

The change must be explicitly labeled as:

ALIGNMENT — restoring Cameron-style participation behavior

If any safety trade-off exists, it must be stated explicitly.

6. Validation Plan (MANDATORY)
6.1 A/B Testing Structure

A = current behavior (hard DAY_GATE block)
B = throttled DAY_GATE (new behavior)

6.2 Test Sets
Sanity Cluster (must run first)

2025-11-18 → 2025-11-22

Previously produced 0 trades

Expected outcome:

B produces some trades

A remains at 0 trades

Protection Cluster (time-diverse)

Older 3–5 day window from a different regime

Purpose:

Detect reintroduction of known loss classes

Ensure no catastrophic degradation

6.3 Review Requirements

Immediate TWCS review of every losing trade

No aggregation-only conclusions

Structural failure modes must be documented

6.4 Success Criteria (any one)

≥ +3 percentage points win rate

≥ +0.2R expectancy

Profit Factor ≥ 1.2 with positive PnL delta

Or clear behavioral correction without loss clustering

7. Documentation Requirements

The next version must update:

PROJECT_STATUS.md

Record that DAY_GATE behavior was realigned

Reference CAMERON_ALIGNMENT_PLAN.md

ACTIVE_GUARDS_LEDGER.md

Update DAY_GATE entry:

Status from “UNDER ALIGNMENT REVIEW”

To “REALIGNED — THROTTLE MODE”

Version release notes

Explicitly state:

What changed

What did not change

Why this aligns with successful Cameron projects

8. Rules That Bind the Next Version

No silent strategy drift

No “temporary” changes without documentation

No additional alignment ideas bundled into this version

No skipping A/B validation

If results are ambiguous → stop and reassess

9. What Comes After This Version (DO NOT DO YET)

Per the Alignment Plan, future work is queued but not part of this handover:

Entry envelope realignment (v0.8.1.27.0)

Trade management (partials / BE) (v0.8.1.28.0)

These must not be pulled into the next version.

10. Final Instruction to the Next Version Thread

If confusion arises again, immediately reference:

Docs/0. strategy/CAMERON_ALIGNMENT_PLAN.md


Do not re-litigate whether Scenario B should be productive.
That decision is already locked.

End of Handover Specification