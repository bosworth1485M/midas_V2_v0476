Handover Document — Transition to v0.8.1.23.0
Use this document at the start of the next version to restore full context.
Project Context (where we are)

This project is in the loss-subtraction phase of Midas_V2 development.
The focus is on removing structurally bad trades before adding sophistication.

The workflow standard is:

one structural change per version

explicit A/B testing (prior commit vs new commit)

TWCS-driven hypothesis validation

time-diverse testing (e.g., October vs December)

v0.8.1.22.0 — What was tested
Hypothesis

Restrict execution of POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD to hostile days only.

This was a regime-scoping test, not a new structural rule.

Code state clarification

The trusted backtester.py was restored from a memory-stick backup.

That file already contained the hostile-only logic.

The baseline commit was created:

Baseline: restore backtester.py from trusted memory stick
(commit: 1e48efb)


Verification confirmed the hostile-only guard was already present in HEAD.

Tests executed (exact commands)
December 2025 (hostile-heavy cluster)
python scripts\run_range_and_summarize.py --start 2025-12-02 --end 2025-12-06 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251202_20251206_v0.8.1.22.0.txt


Result

[B] trades=6, wins=1, losses=5, winrate=16.67%, totalPnL=-146.60

October 2025 (mixed / healthier cluster)
python scripts\run_range_and_summarize.py --start 2025-10-20 --end 2025-10-31 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251020_20251031_v0.8.1.22.0.txt


Result

[B] trades=7, wins=3, losses=4, winrate=42.86%, totalPnL=-56.18

Outcome of v0.8.1.22.0
Verdict

❌ Hypothesis rejected

Restricting the post-damage weak VWAP reclaim guard to hostile days did not:

improve December results

prevent October losses

address the dominant loss class

Losses continued to occur on healthy days.

TWCS Deep Dive (critical evidence)

To determine the true failure mode, we analyzed one loser and one winner using TWCS.

Losing trade (failure class)

BKYI — 2025-10-27 — Scenario B

Characteristics:

Day classified as healthy

Structural damage occurred before entry

failed push / rejection sequence

overlapping reclaim

Entry occurred after damage

Immediate same-bar stop loss

Conclusion:

This is a post-damage entry on a healthy day, and it should never be allowed.

Winning trade (control case)

SLMT — 2025-10-23 — Scenario B

Characteristics:

Day classified as healthy

No structural damage before entry

Entry earned via clean pullback → expansion

Trade hit TP cleanly (+27.78)

Conclusion:

Healthy-day winners do not rely on post-damage entries.

Core Insight (new and important)

Structural damage must override day regime.

This rule does not exist yet in the codebase.

All prior guards were:

regime-based (hostile / marginal)

VWAP-reclaim-based

or marginal-day conditional

None enforced:

“Once structure is broken, no more entries — even on healthy days.”

v0.8.1.23.0 — Chosen direction (Option 1)
Hypothesis

Blocking all post-damage entries (on any day) will reduce clustered losses without removing legitimate winners.

Rationale

Blocks BKYI-type failures

Preserves SLMT-type winners

Simple, explainable, and testable

Matches “loss subtraction first” discipline

Specification — What v0.8.1.23.0 must do
Behavior change (single change)

For each symbol/day:

Detect structural damage using the existing damage logic.

Once damage is detected:

set a per-symbol latch (damage_seen = True)

For the remainder of the day:

block all new entries for that symbol

regardless of day classification (healthy/marginal/hostile)

Explicit exclusions

No continuation exceptions

No VWAP reclaim logic

No regime checks

No parameter tuning

This is a strict lockout, by design.

Scope constraints (non-negotiable)

Modify only src/midas_v2/engine/backtester.py

No refactors

No new infrastructure

No DB, no website, no UI work

No changes to risk, sizing, TP/SL, or scenarios

Required logging (WHY-level)

When a trade is blocked due to this rule:

log once per symbol/day

include:

version tag: v0.8.1.23.0

reason: POST_DAMAGE_ENTRY_LOCKOUT

symbol

timestamp

day_class

damage timestamp / index

Purpose:

make A/B validation unambiguous

enable TWCS correlation

A/B Validation Plan (mandatory)
A

Current baseline commit: 1e48efb

B

New commit adding the post-damage entry lockout

Step 1 — Sanity set

Run and inspect:

2025-10-27 (BKYI loss day)

2025-10-23 (SLMT winner day)

one December hostile day

Confirm via logs and TWCS:

BKYI entry is blocked

SLMT trade still occurs

Step 2 — Range runs

Repeat:

Oct 20–31, 2025

Dec 2–6, 2025

Compare:

trade count

win rate

total PnL

number of blocked entries

Exit condition for v0.8.1.23.0

The version is complete when one of the following is true:

✅ Loss clustering is materially reduced without killing winners → keep rule

❌ Winners are blocked or no improvement → reject or refine

🔁 Partial improvement → document misses, plan v0.8.1.24.0 with one refinement

No further changes in this version.

Deferred items (explicitly parked)

Relational database

Website integration

Strong continuation exception

1s execution refinements

These are intentionally deferred until at least two structural fixes are validated.

End of handover document