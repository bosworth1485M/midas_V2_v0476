BEGIN COPILOT SPEC (v0.8.1.34.0) — DAY_GATE CONSEQUENCE → SOFT THROTTLE (SCENARIO B ONLY)

GOAL / HYPOTHESIS
- v0.8.1.34.0 tests whether December 2025 zero-trade days are caused by DAY_GATE consequence (hard block), not VWAP logic.
- Implement ONE behavior change: convert DAY_GATE hard block into a soft throttle for Scenario B only.
- DO NOT touch: VWAP logic, CONFIRM_BAR, post-damage logic, sizing model, risk manager, strategy signals, refactors.

FILES TO EDIT
- src/midas_v2/engine/backtester.py (only)

STRICT SCOPE RULES
- Only modify behavior for Scenario B when require_day_follow_through == True.
- Day-gate evaluation (prepass) and day_class classification must remain unchanged.
- No new indicators, no new guards, no refactors.
- Keep ASCII-only logs.
- Add inline comments that include version "v0.8.1.34.0" near any changed/added lines.

CURRENT STATE (DO NOT RE-LITIGATE)
- v0.8.1.33.0 relaxed MARGINAL_VWAP gate 2-of-3 → 1-of-3 and is accepted.
- Aug 05–07 (Scenario B) participation restored (esp Aug 06).
- Dec 02–05 (Scenario B) remains zero trades; not caused by marginal VWAP.
- The remaining suppression is likely upstream: DAY_GATE and/or CONFIRM_BAR.
- This version chooses DAY_GATE consequence only.

IMPLEMENTATION DETAILS

1) DO NOT CHANGE DAY_GATE PREPASS OR CLASSIFICATION
- Leave the existing DAY_GATE prepass logic intact:
  - require_day_follow_through
  - day_follow_through_minutes / min_symbols
  - close_gt_vwap_count, green_body_count
  - day_gate_failed determination
- Leave day_class computation intact:
  - is_hostile_day := (DAY_GATE on and close_gt_vwap_count == 0)
  - is_marginal_day := (DAY_GATE on and close_gt_vwap_count == 1)
  - is_healthy_day := (DAY_GATE on and close_gt_vwap_count >= 2)
  - day_class string assignment

2) NEW BEHAVIOR: FOR SCENARIO B ONLY, DAY_GATE MUST NEVER HARD-BLOCK ENTRIES
- Introduce/confirm the notion that for Scenario B, when DAY_GATE is enabled, the consequence becomes throttle-based, not binary gate failure.
- In other words: for Scenario B, if require_day_follow_through is True, then effective_day_gate_failed must be False once throttle state is computed.
- IMPORTANT: This must not affect non-B scenarios.

3) THROTTLE POLICY (SCENARIO B ONLY)
Use existing throttle variables already present (do not invent new structure):
- throttle_enabled (bool)
- throttle_class ("healthy"|"marginal"|"hostile"|"off")
- throttle_risk_factor (float)
- throttle_max_trades (int)
- throttle_reason (str)
- throttle_logged (bool latch)

Set values ONCE per day for Scenario B when require_day_follow_through is True:

- If day_class == "healthy":
  - throttle_enabled = False
  - throttle_class = "healthy"
  - throttle_risk_factor = 1.0
  - throttle_max_trades = 999999
  - effective_day_gate_failed = False

- If day_class == "marginal":
  - throttle_enabled = True
  - throttle_class = "marginal"
  - throttle_risk_factor = 0.75
  - throttle_max_trades = 2
  - effective_day_gate_failed = False

- If day_class == "hostile":
  - throttle_enabled = True
  - throttle_class = "hostile"
  - throttle_risk_factor = 0.50
  - throttle_max_trades = 1
  - effective_day_gate_failed = False

If day_class is unexpected:
- Fail closed by preserving old behavior for Scenario B (do not change other scenarios).
- Log a single warning and do not spam.

4) ENSURE EXISTING "DAY_GATE_FAILED" EARLY_REJECT DOES NOT FIRE FOR SCENARIO B THROTTLE DAYS
- There is a block that logs EARLY_REJECT reason=DAY_GATE_FAILED when effective_day_gate_failed is True.
- Ensure that under Scenario B + DAY_GATE enabled + throttle state computed (marginal/hostile/healthy), effective_day_gate_failed is False and this log does not appear.
- Non-B scenarios keep existing behavior.

5) APPLY THROTTLE ENFORCEMENT AT ENTRY TIME (SCENARIO B ONLY)
- Before allowing any entry attempt to create a position (or pending entry), enforce:
  - If throttle_enabled and throttle_class in {"marginal","hostile"}:
    - If day_trade_count >= throttle_max_trades:
      - Log once per symbol/day: "[WHY] v0.8.1.34.0 DAY_THROTTLE_MAX_TRADES_BLOCK ..."
      - continue (skip entry attempt)

- Sizing scaling:
  - The code already computes risk_usd and then computes risk_usd_effective = risk_usd * throttle_risk_factor for Scenario B throttle.
  - Keep that behavior, but ensure it is always applied whenever throttle_enabled is True for Scenario B.
  - Do NOT change the sizing model; only scale via throttle_risk_factor.

6) OBSERVABILITY (REQUIRED, ONCE PER DAY)
- Emit exactly one summary log line per day/run for Scenario B when DAY_GATE is enabled:
  - "DAY_GATE_THROTTLE v0.8.1.34.0: scenario=B enabled=<bool> class=<...> risk_factor=<...> max_trades=<...> reason=<...>"
- Do not add per-bar logs.

7) VERSION TAGGING
- Any new/modified lines must include a nearby comment "v0.8.1.34.0".
- Do not edit historical version comments unless necessary for correctness.

VALIDATION (DO NOT RUN IN COPILOT)
- After patch is applied, user will run these ranges (Scenario B):
  - Sanity cluster: 2025-08-05 → 2025-08-07
    Expected: participation at least as good as v0.8.1.33.0; no regression.
  - Protection cluster: 2025-12-02 → 2025-12-05
    Expected: no longer persistent zero-trade days; losses must remain controlled.
- Any loss must be reviewed via TWCS immediately.

STOP CONDITIONS
- If non-B scenarios change behavior: revert.
- If VWAP/post-damage/confirm logic changed: revert.
- If logging becomes noisy: revert.

END COPILOT SPEC (v0.8.1.34.0)
