BEGIN COPILOT SPEC — Midas_V2 v0.8.1.3.1 Day Gate Enhancement: Require ≥1 close_gt_vwap qualifier (toggleable)

VERSION PURPOSE (one sentence)
Reduce “false PASS but losing day” cases (e.g., 2025-08-08) by requiring that at least one of the day-gate qualifying symbols qualifies via the existing close_gt_vwap branch (i.e., above VWAP within cap and liquidity), while keeping the existing day-gate behavior unchanged when the new toggle is OFF.

ABSOLUTE SCOPE RULES
- Allowed: modify ONLY these files:
  1) src/midas_v2/engine/backtester.py
  2) config/scenarios.json
- Forbidden: any other file changes, SL/TP changes, entry logic changes, sizing changes, refactors, new scripts, catalysts, microstructure logic.

NEW CONFIG (Scenario B ONLY; default OFF)
In config/scenarios.json under Scenario B params, add exactly:
"require_day_gate_close_gt_vwap": false

Rules:
- Add only this one new field.
- Do not change any existing Scenario B fields.
- Do not touch other scenarios.

BEHAVIOR (only when toggle is ON)
Existing day gate already computes:
- total qualifying symbols (follow_through_count)
- pass_rule per symbol ("close_gt_vwap" or "green_body")
- and sets day_gate_failed if follow_through_count < day_follow_through_min_symbols

Add ONE additional rule, evaluated only if require_day_gate_close_gt_vwap == true:
- Track close_gt_vwap_count = number of qualifying symbols whose pass_rule == "close_gt_vwap"
- If follow_through_count >= day_follow_through_min_symbols BUT close_gt_vwap_count == 0:
    Force day_gate_failed = True
    Log: DAY_GATE: FAILED reason=no_close_gt_vwap_qualifier

IMPORTANT: Do not re-evaluate symbols. Use the already-determined pass_rule.
This must not alter how symbols qualify; it only affects the final PASS/FAIL decision.

LOGGING (MANDATORY)
After the per-symbol logs and before the final PASS/FAIL decision, emit exactly one line:
DAY_GATE: RULE_COUNTS total=<n> close_gt_vwap=<m> green_body=<k>

If the new rule forces failure, emit:
DAY_GATE: FAILED reason=no_close_gt_vwap_qualifier

Do not remove or reorder existing DAY_GATE logs.
Do not add per-bar logs.

INLINE VERSION TAGGING
All new/modified lines must include: # v0.8.1.3.1

VALIDATION (MANDATORY — follow 2-step workflow)
Step 1 (sanity, must pass before Step 2):
- Run: 2025-08-06, 2025-08-07, 2025-08-08 with toggle OFF (baseline) and toggle ON (new rule)
- Goal: keep Aug-06 PASS, keep Aug-07 FAIL, improve Aug-08 (ideally FAIL or reduced damage)

Step 2 (range, only if Step 1 passes):
- Run: 2025-08-01 → 2025-08-31 with toggle OFF vs ON and compare totals (PnL, worst day, # stand-down days)

Suggested commands:
python scripts\run_range_and_summarize.py --start 2025-08-06 --end 2025-08-08 --scenario B
python scripts\run_range_and_summarize.py --start 2025-08-01 --end 2025-08-31 --scenario B

FINAL INSTRUCTION
Implement the smallest possible diff to add the single toggle and enforce the “≥1 close_gt_vwap qualifier” rule when enabled, with the required logs, and change nothing else.

END COPILOT SPEC — Midas_V2 v0.8.1.3.1 Day Gate Enhancement: Require ≥1 close_gt_vwap qualifier (toggleable)
