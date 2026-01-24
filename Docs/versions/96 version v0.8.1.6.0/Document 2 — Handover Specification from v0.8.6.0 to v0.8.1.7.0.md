Document 2 — Handover Specification (Revised, with Software Update Details)
Midas_V2 v0.8.1.7.0
Post-Entry Expansion Confirmation (Single Structural Fix)

Audience: Next version thread / Copilot
Status: DRAFT (awaiting approval)
Rule: One hypothesis, one fix, no scope creep

1. Context at Handover (Where We Are)

As of v0.8.1.6.0, the system has:

Strengthened DAY_GATE (requires ≥1 close_gt_vwap) filtering non-tradable days.

Structural Damage / Weak VWAP Reclaim Guard (regime-dependent via auto-switch).

VWAP Extension Gate enforcing location discipline.

TWCS across April/May/July 2025 shows the dominant remaining loss bucket is:

Valid entries that fail to show immediate post-entry expansion.

This is now isolated and repeatedly confirmed (WGRX, LHAI, ABVE, ARBB).

2. Problem Statement (TWCS-Proven)

Observed pattern (dominant):

Day passes (true early acceptance)

Entry is structurally valid (above VWAP, VWAP slope positive, green streak satisfied)

After entry, price stalls/overlaps and does not expand

Trade rolls over and stops out

Canonical examples: WGRX (2025-05-08), LHAI (2025-07-25), ABVE (2025-07-11), ARBB (2025-04-15)

3. Hypothesis for v0.8.1.7.0 (Locked)

If a trade does not demonstrate early expansion away from VWAP immediately after entry, it is low-expectancy and should be blocked.

This is a continuation confirmation hypothesis (structure), not indicator tuning.

4. Scope Rules (Non-Negotiable)

This version must:

Implement one structural rule only

Use existing minute-level data only

Be explainable in logs and TWCS

Be reversible and A/B testable

This version must NOT:

Modify DAY_GATE logic

Modify Structural Damage Guard logic

Modify VWAP Extension Gate logic

Tune MACD/green-streak/RVOL thresholds

Add new indicators or new data sources

Change sizing/TP/SL/exits

Add 1-second/microstructure gates

Combine multiple fixes

5. Desired Shape of the Fix (Design Choice)

This version uses ENTRY-TIME BLOCKING (not early exits).

If expansion confirmation fails → no entry

Trade management remains unchanged

Early-exit variants are explicitly deferred to later versions.

6. Configuration Design (What knobs we will add)
6.1 New Scenario B parameters (config/scenarios.json)

Add a single feature toggle plus minimal parameters:

post_entry_expansion_gate (bool, default false)

post_entry_expansion_minutes (int, default 2)

post_entry_expansion_min_bps (float, default 10)

Meaning:
Within the first N minutes after a would-be entry, price must expand by at least X bps above entry (or above a simple reference), otherwise the entry is blocked.

Important: These are starting defaults only; they are not “optimized” in this version. They are used for A/B testing.

7. Software Updates Required (Exact files + what changes)
7.1 config/scenarios.json

Scenario B only:

Add the new config keys listed above

Default state should be OFF (post_entry_expansion_gate=false) to preserve baseline and allow A/B

Rules:

Do not reformat JSON

Do not touch other scenarios

Keep changes minimal and local

7.2 src/midas_v2/strategy.py

This is the primary implementation file.

Additions required:

Extend StrategyParams to include the new config keys:

post_entry_expansion_gate

post_entry_expansion_minutes

post_entry_expansion_min_bps

Add a helper function, version-tagged, e.g.:

_post_entry_expansion_ok(...)

Behavior (high-level):

Called at the moment an entry would normally occur

Looks forward N minutes (existing minute bars already in memory / accessible)

Computes whether price expanded enough quickly:

expansion metric must be deterministic and simple

must fail closed if there are insufficient bars

Integration point:

The gate must be placed late in entry decision flow, after existing entry conditions pass (MACD/green streak/VWAP extension/struct-damage effective flag).

If gate fails → block entry with a clear reason.

Logging (mandatory):
Add WHY logs similar in style to existing guards:

POST_EXP: CHECK ...

POST_EXP: BLOCKED reason=no_expansion ...

POST_EXP: PASSED ...

Logs must include at minimum:

symbol

entry time

minutes window

required bps

observed bps (or observed high)

pass/fail reason

Rules:

Do not change existing gate logic

Do not re-order unrelated logic

Only insert the new gate and logs

7.3 src/midas_v2/engine/backtester.py

No behavioral changes required.

Permitted optional change:

Ensure scenario params are passed into StrategyParams unchanged (likely already true)

No changes to DAY_GATE, structural-damage routing, or risk manager

Default: do not modify unless the StrategyParams wiring requires it.

7.4 src/midas_v2/plotting/twcs_plotter.py

No required changes.

Rationale:

TWCS already renders:

entry/exit windows

VWAP context

slopes and indicator panel

Optional (only if needed later, not in v0.8.1.7.0):

Add a small “expansion metric” field to overlay box if it becomes part of diagnostics

This is deferred unless we cannot diagnose without it.

7.5 No runner script changes required

The following scripts should remain unchanged:

scripts/run_day_simple.py

scripts/run_range_and_summarize.py

scripts/topgappers.py

scripts/fetch_minutes_polygon.py

We will use existing workflows for A/B testing.

8. Validation Plan (Required)
Stage 1 — Sanity (TWCS-Anchored)

Days:

2025-04-15 (ARBB loser class)

2025-07-25 (LHAI loser class)

plus 1 known winner day in August

Expected:

Losers blocked for “no expansion”

Winners still pass

Logs clearly show pass/fail

Stage 2 — Small Cluster

April 2025:

reduce clustered losing days

preserve winner days

Stage 3 — Hostile Months

May / July 2025:

reduced trade count

reduced drawdowns

Stage 4 — Friendly Month

August 2025:

minimal impact on winners

no starvation

9. Success Criteria

Success if:

material reduction in stall/stop-out losers (TWCS-proven class)

winners preserved

logs + TWCS explain blocks unambiguously

no regressions in other guards

Failure is acceptable only if it conclusively disproves the hypothesis.

10. Handover Summary (One Sentence)

v0.8.1.7.0 adds a reversible post-entry expansion confirmation gate (minute bars only) to block the dominant “valid entry → no expansion → stop-out” failure class, without modifying DAY_GATE, structural-damage logic, or trade management.