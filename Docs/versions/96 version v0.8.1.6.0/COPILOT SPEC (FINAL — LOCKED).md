# COPILOT SPEC (FINAL — LOCKED)
# Midas_V2 v0.8.1.6.0
# DAY_GATE: Require ≥1 close_gt_vwap qualifier (Scenario B)

GOAL (EXACT)
Make Scenario B trade only on days where DAY_GATE has at least one early symbol qualifying via:
- rule = close_gt_vwap
i.e., close_gt_vwap_count >= 1.

This filters out green-body-only “fake strength” days and reduces losses in hostile regimes, without harming August.

------------------------------------------------------------
IMPORTANT (CODE REALITY — DO NOT RE-IMPLEMENT)
------------------------------------------------------------
The core enforcement already exists in src/midas_v2/engine/backtester.py:

- Scenario param: require_day_gate_close_gt_vwap
- Existing enforcement (already implemented):
  when enabled and close_gt_vwap_count == 0, DAY_GATE forces:
    - day_gate_failed = True
    - logs: DAY_GATE: FAILED reason=no_close_gt_vwap_qualifier
- Entry gating already blocks trading via (not day_gate_failed)

Therefore v0.8.1.6.0 is primarily config standardization, plus an optional single observability log line.

------------------------------------------------------------
FILES ALLOWED TO CHANGE (ONLY)
------------------------------------------------------------
1) config/scenarios.json
2) src/midas_v2/engine/backtester.py (OPTIONAL: add ONE config log line only)

NO OTHER FILES.

------------------------------------------------------------
CHANGE 1 (REQUIRED): config/scenarios.json
------------------------------------------------------------
Scenario B params ONLY:

Set:
  "require_day_gate_close_gt_vwap": true

Rules:
- Do not reformat JSON.
- Do not touch other scenarios/keys/ordering/whitespace.

------------------------------------------------------------
CHANGE 2 (OPTIONAL): backtester.py (observability only)
------------------------------------------------------------
Do NOT change DAY_GATE logic. It already enforces the requirement when the flag is true.

Optional: Add ONE version-tagged config log line near the existing DAY_GATE “CHECK” log, once per day run:

  DAY_GATE v0.8.1.6.0: CONFIG require_day_gate_close_gt_vwap=<true/false>

Rules:
- Do not modify existing DAY_GATE log formats.
- Do not move existing DAY_GATE logs.
- Do not duplicate existing DAY_GATE logs.
- Only add this single new line.
- Do not change thresholds or computations.
- Do not change the existing failure log:
  DAY_GATE: FAILED reason=no_close_gt_vwap_qualifier
  (this already exists and is acceptable)

------------------------------------------------------------
FORBIDDEN CHANGES
------------------------------------------------------------
Copilot must NOT:
- change how close_gt_vwap_count / green_body_count are computed
- change DAY_GATE minutes, min_symbols, liquidity floor, VWAP cap, or bar scanning
- change entry gating logic (the (not day_gate_failed) check remains)
- change v0.8.1.5.0 structural-damage auto-switch logic
- change v0.8.1.4.0 structural damage guard logic
- change VWAP extension gate logic
- change sizing/TP/SL/risk
- refactor unrelated code or reformat files

------------------------------------------------------------
VALIDATION (USER WILL RUN)
------------------------------------------------------------
Stage 1:
- Run 2025-08-08 (expect DAY_GATE PASS; trades may occur)
- Find a day where close_gt_vwap_count=0 but green_body_count>0
  expect DAY_GATE FAIL via reason=no_close_gt_vwap_qualifier

Stage 2:
- Run month ranges May / July / August / September and compare to v0.8.1.5.0 baseline.

END COPILOT SPEC — v0.8.1.6.0
