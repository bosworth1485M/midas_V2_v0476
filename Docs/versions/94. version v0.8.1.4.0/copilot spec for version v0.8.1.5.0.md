# COPILOT SPEC
# Midas_V2 v0.8.1.5.0
# Day / Regime Switch for Structural Damage Guard (reject_reclaim_after_damage)

GOAL (EXACT)
Implement a DAY-LEVEL auto-switch that decides whether the Structural Damage Guard
(reject_reclaim_after_damage) should be ENABLED for the current trading day.

This version does NOT change the structural-damage guard logic (v0.8.1.4.0).
It only changes WHEN the guard is active.

The auto-switch must use ONLY existing signals from DAY_GATE (no new indicators).

------------------------------------------------------------
FILES ALLOWED TO CHANGE (ONLY)
------------------------------------------------------------
1) src/midas_v2/engine/backtester.py
2) config/scenarios.json  (optional: add new switch key; do NOT touch unrelated keys)

NO OTHER FILES.

------------------------------------------------------------
BASELINE / CONFIG RULES
------------------------------------------------------------
- The existing config key remains:
  reject_reclaim_after_damage (Scenario B params)

- For v0.8.1.5.0 we introduce an auto-switch mode with manual override.

Manual override behavior (MUST IMPLEMENT):
- If reject_reclaim_after_damage is explicitly True in scenarios.json:
    -> FORCE ENABLE (do not auto-disable)
- If reject_reclaim_after_damage is explicitly False in scenarios.json:
    -> AUTO-MODE controls whether it becomes enabled for the day
       (i.e., base=False allows auto-enable)
- If the key is missing:
    -> treat as False (base=False)

Optional new config key (recommended for clean A/B):
- add in Scenario B params:
    "auto_struct_damage_from_day_gate": true

If this key is missing, default it to True.

Interpretation:
- auto_struct_damage_from_day_gate controls whether AUTO-MODE is active when base=False.

------------------------------------------------------------
AUTO DECISION RULE (LOCKED FOR THIS VERSION)
------------------------------------------------------------
Compute day-level signal from DAY_GATE results:

AUTO-ENABLE struct damage guard for the day ONLY IF:
1) DAY_GATE passes for the day
AND
2) At least one symbol passed DAY_GATE via "close_gt_vwap"
   (i.e., close_gt_vwap count >= 1)

If DAY_GATE fails OR close_gt_vwap count == 0:
- AUTO-ENABLE = False

This rule is intentionally minimal and based on existing DAY_GATE evidence.

------------------------------------------------------------
WHERE TO IMPLEMENT (CRITICAL)
------------------------------------------------------------
In backtester.py inside run_backtest(), in the area where DAY_GATE is computed:

- Capture (and retain) DAY_GATE outcomes that are already available:
  - day_gate_failed (bool)
  - rule counts for DAY_GATE: close_gt_vwap and green_body
    (these appear in logs; use the same variables if they exist or add them minimally)

- Compute a per-day boolean:
  struct_damage_auto_enabled

- Compute the final effective enable state:
  reject_reclaim_after_damage_effective

- Ensure the entry guard (v0.8.1.4.0) uses reject_reclaim_after_damage_effective
  (NOT the raw scenario_params value) so behavior truly becomes day-dependent.

------------------------------------------------------------
LOGGING REQUIREMENTS (MUST)
------------------------------------------------------------
At the start of the day (once per symbol/day run, not per bar),
log a single line showing:

- base config value (base)
- whether auto mode is enabled
- the auto decision
- the final effective value
- the reason

Exact format (must match, version-tagged):
STRUCT_DAMAGE v0.8.1.5.0: CONFIG base=<true/false> auto_mode=<true/false> day_gate_pass=<true/false> close_gt_vwap_cnt=<int> auto_enabled=<true/false> effective=<true/false> reason=<string>

Reason strings (choose exactly one):
- "manual_true_forced"
- "auto_enabled_day_gate_close_gt_vwap"
- "auto_disabled_day_gate_failed"
- "auto_disabled_no_close_gt_vwap"
- "auto_mode_off"

Also ensure existing v0.8.1.4.0 logs remain unchanged when the guard runs:
STRUCT_DAMAGE v0.8.1.4.0: detected ...
STRUCT_DAMAGE v0.8.1.4.0: BLOCKED ...
STRUCT_DAMAGE v0.8.1.4.0: PASSED ...

Do not change those strings.

------------------------------------------------------------
IMPLEMENTATION DETAILS (SAFE MINIMUM)
------------------------------------------------------------

1) scenarios.json change (recommended):
- In Scenario B params, add:
  "auto_struct_damage_from_day_gate": true

Do not change any other keys or formatting.

2) backtester.py changes:
- Read:
  base_reject = bool(scenario_params.get("reject_reclaim_after_damage", False))
  auto_mode = bool(scenario_params.get("auto_struct_damage_from_day_gate", True))

- DAY_GATE signals:
  day_gate_pass = (not day_gate_failed)

  close_gt_vwap_cnt must reflect the DAY_GATE rule counts.
  Use existing vars if present.
  If not present, minimally add counters where DAY_GATE counts are logged.

- Compute auto_enabled:
  if auto_mode and (not base_reject):
      if not day_gate_pass:
          auto_enabled = False
          reason = "auto_disabled_day_gate_failed"
      elif close_gt_vwap_cnt >= 1:
          auto_enabled = True
          reason = "auto_enabled_day_gate_close_gt_vwap"
      else:
          auto_enabled = False
          reason = "auto_disabled_no_close_gt_vwap"
  else:
      auto_enabled = False
      reason = "manual_true_forced" if base_reject else "auto_mode_off"

- Compute effective:
  if base_reject:
      effective = True
      reason = "manual_true_forced"
  else:
      effective = auto_enabled

- Log the CONFIG line exactly once per day-run after DAY_GATE is known.

- Wire effective into the entry logic:
  replace any use of reject_reclaim_after_damage with reject_reclaim_after_damage_effective

3) Reversibility:
- Manual: set reject_reclaim_after_damage=true to force ON for the day (no auto).
- Manual baseline: set reject_reclaim_after_damage=false and auto_struct_damage_from_day_gate=true to test auto.
- Disable auto entirely: set auto_struct_damage_from_day_gate=false and reject_reclaim_after_damage=false.

------------------------------------------------------------
FORBIDDEN CHANGES
------------------------------------------------------------
Copilot must NOT:
- change the v0.8.1.4.0 structural damage guard logic/thresholds
- add new indicators, new data sources, or new timeframes
- modify stops/targets/sizing/risk
- refactor unrelated code
- create new scripts
- change log formats for DAY_GATE or VWAP_EXT (only add the new CONFIG line)

------------------------------------------------------------
VALIDATION (USER WILL RUN; COPILOT MUST NOT)
------------------------------------------------------------
User will validate:
Stage 1:
- One August-like day should show effective=true (auto enabled)
- One July or September-like day should show effective=false (auto disabled)
Stage 2:
- Full month ranges:
  July 2025, August 2025, September 2025
Expect:
- July & September improve vs always-on v0.8.1.4.0
- August remains close to v0.8.1.4.0 always-on results

END COPILOT SPEC — v0.8.1.5.0
