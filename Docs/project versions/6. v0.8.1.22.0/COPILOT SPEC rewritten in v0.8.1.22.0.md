COPILOT IMPLEMENTATION SPEC for v0.8.1.22.0
Title: Restrict execution of POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD to hostile days only

GOAL (single behavior change)
- The guard named POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD / POST_DAMAGE_WEAK_VWAP_RECLAIM_BLOCK must execute ONLY on hostile days.
- On healthy days and marginal days, this guard must not run at all (no checks, no block, no logs).
- Do NOT change the guard’s internal logic (damage detection, reclaim detection, thresholds, counting, or existing [WHY] logs) beyond the minimal outer day gating needed to make it hostile-only.

SCOPE / SAFETY RULES
- Modify ONE FILE ONLY:
  src/midas_v2/engine/backtester.py
- No refactors, no helper functions, no new imports, no moving blocks around.
- Deterministic, minimal diff.
- Keep all existing log message text exactly the same (including the [WHY] line), except where you must change the “enabled” status computation to match the new hostile-only behavior.

WHY THIS SPEC EXISTS (important correctness constraint)
- In this codebase, the guard is currently gated by `is_healthy_day` in its outer `if` condition.
- Therefore: DO NOT wrap the block with `if day_class == "hostile":` while leaving `is_healthy_day` in place, because that would make the guard never run.
- The correct change is to REPLACE the outer day gate from healthy-only to hostile-only.

IMPLEMENTATION INSTRUCTIONS (exact edits)

1) Find the guard block (landmark)
Locate the section with a comment like:
  "Post-Damage Weak VWAP Reclaim Guard (Healthy Days)"
and/or the [WHY] log text containing:
  "POST_DAMAGE_WEAK_VWAP_RECLAIM_BLOCK"

You should see an outer condition shaped like:
  if (scenario_name or scn) == "B" and is_healthy_day and <other conditions>:
      <guard internals...>
      log warning "[WHY] ... POST_DAMAGE_WEAK_VWAP_RECLAIM_BLOCK ..."

2) Change ONLY the outer day gate for the guard
REPLACE `and is_healthy_day` in that guard’s outer `if` condition with hostile-only gating:

Use ONE of these (prefer the first if available exactly as-is in the file):
- `and (day_class == "hostile")`
OR
- `and is_hostile_day`

Do not add additional day logic. Do not change any other clauses in that `if` statement.

Result:
- Guard executes only when day_class is hostile (or is_hostile_day is true) and all the existing internal guard conditions are met.
- Guard does not execute on healthy/marginal days.

3) Keep guard internals identical
Inside the guard block:
- Do NOT change damage detection, reclaim detection, continuation counting, thresholds, or any variable names.
- Do NOT change the existing [WHY] log line content.
- Do NOT change the early_reject_logged behavior.
- Do NOT change any other guards.

4) Update the “enabled” status used for Trade Card / telemetry (must match behavior)
In backtester.py there are one or more places where the code sets a variable like:
  post_damage_weak_reclaim_guard_enabled_val = bool((scenario_name or scn) == "B" and is_healthy_day)

REPLACE the `is_healthy_day` part there with the same hostile-only gating you used in step (2):
- `and (day_class == "hostile")` OR `and is_hostile_day`

This is not a new feature—this is required so the UI/telemetry does not incorrectly claim the guard is enabled on healthy days after you’ve made it hostile-only.

5) Version tagging
- Add or update a short inline comment near the modified lines indicating v0.8.1.22.0, e.g.:
  `# v0.8.1.22.0 hostile-only`
Keep it minimal and on the same line or immediately adjacent.

ACCEPTANCE CHECKLIST (must satisfy all)
- The guard block’s outer condition no longer references `is_healthy_day`.
- The guard block is gated by hostile-only (`day_class == "hostile"` or `is_hostile_day`).
- Guard internals are unchanged.
- The “enabled” status computation for this guard matches hostile-only gating.
- No other logic changes anywhere else in the file.

After Copilot finishes (YOU run these, not Copilot)
Step A — verify the patch (one command)
git diff -- src/midas_v2/engine/backtester.py

Step B — run Dec range (one command)
python scripts\run_range_and_summarize.py --start 2025-12-02 --end 2025-12-06 --scenario B 2>&1 | Tee-Object -FilePath out\auto\B_runlog_20251202_20251206_v0.8.1.22.0.txt

Step C — run Oct range (one command)
python scripts\run_range_and_summarize.py --start 2025-10-20 --end 2025-10-31 --scenario B 2>&1 | Tee-Object -FilePath out\auto\B_runlog_20251020_20251031_v0.8.1.22.0.txt
END COPILOT IMPLEMENTATION SPEC