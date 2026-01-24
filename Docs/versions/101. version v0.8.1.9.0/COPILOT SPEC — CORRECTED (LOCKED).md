COPILOT SPEC — CORRECTED (LOCKED)
Midas_V2 v0.8.1.9.0
Limited Marginal-Day Participation (1 Trade Max)
GOAL (EXACT)

Allow exactly one Scenario B trade on marginal DAY_GATE days
(close_gt_vwap_count == 1) even if DAY_GATE would otherwise fail,
while keeping:

hostile days (close_gt_vwap_count == 0) fully blocked

healthy days (close_gt_vwap_count >= 2) unchanged

This is a controlled probe, not a relaxation of DAY_GATE.

CRITICAL CODE REALITY (DO NOT IGNORE)

In backtester.py, trade entry is currently impossible when day_gate_failed == True, because the entry condition explicitly checks:

if not day_gate_failed and position is None and pending_entry is None ...


Therefore, marginal-day participation requires bypassing DAY_GATE enforcement at entry time, not changing DAY_GATE computation.

REQUIRED BEHAVIOR (MANDATORY)
Definitions (use existing variables only)

is_marginal_day = (close_gt_vwap_count == 1)

is_hostile_day = (close_gt_vwap_count == 0)

is_healthy_day = (close_gt_vwap_count >= 2)

No new indicators. No new counters beyond the trade cap.

CORE LOGIC CHANGE (MINIMAL, SINGLE LOCATION)
Introduce an effective gate flag (do NOT modify DAY_GATE itself):
effective_day_gate_failed = day_gate_failed

Override enforcement only under this condition:
if is_marginal_day and day_trade_count < 1:
    effective_day_gate_failed = False

Use effective_day_gate_failed in place of day_gate_failed for:

The early “DAY_GATE FAILED” rejection path

The combined trade entry condition

HARD CONSTRAINTS (DO NOT VIOLATE)

❌ Do NOT change how day_gate_failed is computed

❌ Do NOT modify DAY_GATE counters or thresholds

❌ Do NOT allow more than 1 completed trade per day

❌ Do NOT affect hostile days (close_gt_vwap_count == 0)

❌ Do NOT add helpers, refactors, or new config keys

TRADE CAP ENFORCEMENT

Track day_trade_count at day scope

Increment only when a trade is finalized (TP or SL)

Once day_trade_count >= 1:

All further entry attempts must be rejected

Log exactly once:

[WHY] MARGINAL_DAY_TRADE_CAP_REACHED

LOGGING (STRICT)

At DAY_GATE summary time, log once per day:

DAY_GATE v0.8.1.9.0 summary:
close_gt_vwap_count=<n>
classification=<hostile|marginal|healthy>
marginal_trade_cap=<1|n/a>


On first marginal-day entry:

[INFO] v0.8.1.9.0 MARGINAL_DAY_ENTRY_ALLOWED trade_index=1

FILES ALLOWED TO CHANGE (ONLY)

src/midas_v2/engine/backtester.py

VALIDATION EXPECTATION (OUT OF SCOPE FOR CODE)

This feature will be validated only via wide-range A/B testing using
run_range_and_summarize.py with outputs written to log files.

END OF SPEC (LOCKED)