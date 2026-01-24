BEGIN COPILOT SPEC — Midas_V2 v0.8.1.3.1 Day Gate Enhancement: Require ≥1 close_gt_vwap qualifier (toggleable)

VERSION PURPOSE (one sentence)
Reduce “false PASS but losing day” cases (e.g., 2025-08-08) by requiring that at least one day-gate qualifying symbol qualifies via the existing close_gt_vwap branch, while keeping v0.8.1.3.0 behavior unchanged when this toggle is OFF.

ABSOLUTE SCOPE RULES (do not violate)
- Allowed file edits ONLY:
  1) src/midas_v2/engine/backtester.py
  2) config/scenarios.json
- Forbidden: any other file changes, refactors, formatting-only rewrites, SL/TP changes, entry/exit changes, sizing changes, catalysts, microstructure/TWCS changes, new scripts, multi-knob tuning.

CONFIG CHANGE (Scenario B ONLY; add exactly ONE new field; default OFF)
In config/scenarios.json, inside:
  top-level key "B" → object "params" (NOT B_backup, NOT B_safe),
add exactly one new boolean field:

  "require_day_gate_close_gt_vwap": false

Placement requirement:
- Insert it directly alongside existing day-gate fields (near require_day_follow_through / day_follow_through_*), e.g. immediately after:
  "day_follow_through_min_symbols": 2
or immediately before the day-follow-through block.
- Do NOT change any existing values.
- Do NOT touch other scenarios.

REFERENCE: Current B params includes the day-gate fields:
  "require_day_follow_through": true
  "day_follow_through_minutes": 20
  "day_follow_through_min_symbols": 2
(and has vwap_extension_gate / vwap_extension_max_pct already).

BEHAVIOR CHANGE (ONLY when toggle is ON)
Precondition: existing day gate already computes, without needing any new evaluation:
- follow_through_count = number of qualifying symbols
- per-symbol pass_rule label (e.g., "close_gt_vwap" or "green_body")
- existing decision: fail if follow_through_count < day_follow_through_min_symbols

New rule when require_day_gate_close_gt_vwap == true:
- Count close_gt_vwap_count = number of qualifying symbols whose pass_rule == the EXISTING token used for the above-VWAP branch.

IMPORTANT TOKEN SAFETY:
- Do NOT invent new strings.
- Use the exact pass_rule token already produced by current code for the above-VWAP branch.
- Expected token per docs: "close_gt_vwap"
- If code already uses a different token, use THAT exact existing token; do not rename it.

Final decision logic:
1) If follow_through_count < day_follow_through_min_symbols:
     existing behavior (FAIL) unchanged.
2) Else (the day would otherwise PASS):
     If close_gt_vwap_count == 0:
         Force day_gate_failed = True
         Emit failure reason: no_close_gt_vwap_qualifier
     Else:
         existing behavior (PASS) unchanged.

CRITICAL: Do NOT re-evaluate per-symbol qualification.
Use ONLY already-determined pass_rule values.
This must not alter how symbols qualify — only the final PASS/FAIL decision.

LOGGING (MANDATORY; minimal; do not reorder existing logs)
After the per-symbol qualification logs and before final PASS/FAIL decision, emit exactly one line:
  DAY_GATE: RULE_COUNTS total=<n> close_gt_vwap=<m> green_body=<k>

If the new rule forces failure, emit exactly:
  DAY_GATE: FAILED reason=no_close_gt_vwap_qualifier

Do not add per-bar logs.
Do not add extra per-symbol logs.
Do not remove or reorder existing DAY_GATE logs.

INLINE VERSION TAGGING (MANDATORY)
All new/modified lines must include:  # v0.8.1.3.1

VALIDATION (MANDATORY — follow 2-step workflow)
Step 1 (Sanity; must pass before Step 2):
- Run 2025-08-06, 2025-08-07, 2025-08-08 with toggle OFF (baseline) and toggle ON (new rule).
- Goals:
  - Aug-06: still PASS and trades occur
  - Aug-07: still FAIL / stand down
  - Aug-08: improved — ideally FAIL day; otherwise fewer trades or reduced loss
Command (your normal runner):
  python scripts\run_range_and_summarize.py --start 2025-08-06 --end 2025-08-08 --scenario B

Step 2 (Range; only if Step 1 behaves logically):
  python scripts\run_range_and_summarize.py --start 2025-08-01 --end 2025-08-31 --scenario B
Compare toggle OFF vs ON: total PnL, worst day, # stand-down days, trades/day.

FINAL INSTRUCTION
Implement the smallest possible diff adding exactly one Scenario B toggle and enforcing the “≥1 close_gt_vwap qualifier” rule when enabled, with required logs, and change nothing else.

END COPILOT SPEC — Midas_V2 v0.8.1.3.1 Day Gate Enhancement: Require ≥1 close_gt_vwap qualifier (toggleable)
