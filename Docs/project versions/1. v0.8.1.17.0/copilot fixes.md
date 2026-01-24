# ============================================================
# COPILOT PATCH SPEC (FINAL — LOCKED)
# Midas_V2 v0.8.1.17.0
# Fix observability mismatches after Policy A implementation
# ============================================================

GOAL (EXACT)
Apply TWO small fixes to improve correctness/clarity of logs after the new
marginal stop-after-1-loss policy was implemented.

These fixes must NOT change trading behavior, entries, exits, sizing, TP/SL,
DAY_GATE evaluation, VWAP/MACD logic, or any guard thresholds.
They are purely observability / logging hygiene fixes.

FILES ALLOWED TO CHANGE (ONLY)
- src/midas_v2/engine/backtester.py

NO OTHER FILES.
NO REFACTORS.
NO NEW HELPERS / MODULES.

------------------------------------------------------------
FIX #1 — Separate latch for v0.8.1.17.0 eligibility log
------------------------------------------------------------

PROBLEM
The code currently reuses an existing boolean latch (marginal_eligible_logged)
for both:
- v0.8.1.9.0 MARGINAL_DAY_ELIGIBLE
and
- v0.8.1.17.0 MARGINAL_STOP_AFTER_1_LOSS_ELIGIBLE

This can cause one message to suppress the other and makes logs unreliable.

REQUIREMENT
Introduce a NEW, separate boolean latch used ONLY for:
- v0.8.1.17.0 MARGINAL_STOP_AFTER_1_LOSS_ELIGIBLE

IMPLEMENTATION
A) Where day-scoped variables are initialized (near day_trade_count reset and other latches),
add:

    marginal_stop1loss_eligible_logged = False  # v0.8.1.17.0

B) In the branch where policy A is enabled (marginal_stop1loss_enabled True) and
sl_seen is False and you emit:

    "[INFO] v0.8.1.17.0 MARGINAL_STOP_AFTER_1_LOSS_ELIGIBLE ..."

Change it so it uses ONLY the new latch:
- if not marginal_stop1loss_eligible_logged: log(...)
- then set marginal_stop1loss_eligible_logged = True

Do NOT modify the existing marginal_eligible_logged behavior for v0.8.1.9.0.

------------------------------------------------------------
FIX #2 — Prevent misleading DAY_GATE_FAILED logs after stop triggers
------------------------------------------------------------

PROBLEM
After the stop-after-1-loss triggers on a marginal day, subsequent entries are blocked.
But the code can still emit generic:

    EARLY_REJECT reason=DAY_GATE_FAILED ...

for symbols after the stop triggers, which is misleading because the true reason is
MARGINAL_STOP_AFTER_1_LOSS_BLOCK.

REQUIREMENT
When the policy A stop is active (marginal day + policy enabled + marginal_sl_seen True),
do NOT emit DAY_GATE_FAILED EARLY_REJECT logs for that symbol, because it obscures the true cause.

IMPLEMENTATION
Locate the block that logs DAY_GATE_FAILED, which typically looks like:

    if effective_day_gate_failed and position is None and pending_entry is None:
        ... log EARLY_REJECT reason=DAY_GATE_FAILED ...

Add a very small guard at the top of that block:

    if is_marginal_day and marginal_stop1loss_enabled and marginal_sl_seen:
        # v0.8.1.17.0: stop-after-loss is the controlling reason; avoid misleading DAY_GATE_FAILED logs
        pass_or_continue_without_logging

Exact behavior:
- Entry must remain blocked (no behavior change).
- We are ONLY preventing the DAY_GATE_FAILED log from being emitted in this condition.
- Do NOT affect hostile days or healthy days.
- Do NOT affect marginal days before the stop triggers.

You may implement this as:
- return/continue before the DAY_GATE_FAILED log statement, OR
- wrap the DAY_GATE_FAILED log statement in an if-not condition.

But do not restructure the control flow beyond what is needed.

------------------------------------------------------------
ACCEPTANCE CHECKS (MANDATORY)
------------------------------------------------------------

1) When policy A is enabled and marginal day is eligible before any SL:
- v0.8.1.17.0 MARGINAL_STOP_AFTER_1_LOSS_ELIGIBLE logs once per day (not suppressed by other latches)

2) After the first SL on a marginal day triggers the stop:
- subsequent blocked entries log MARGINAL_STOP_AFTER_1_LOSS_BLOCK (log-once per symbol/day as already implemented)
- DAY_GATE_FAILED logs do NOT appear for those subsequent blocked attempts

3) Baseline behavior unchanged when policy is disabled.

END SPEC