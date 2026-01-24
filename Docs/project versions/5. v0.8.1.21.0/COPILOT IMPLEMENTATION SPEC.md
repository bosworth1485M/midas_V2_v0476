COPILOT IMPLEMENTATION SPEC — Midas_V2 v0.8.1.22.0

Edit ONLY: src/midas_v2/engine/backtester.py
Single behavior change only. No refactors. No parameter changes. No new telemetry. No new files.
DO NOT run anything. Do not propose or execute any commands.

GOAL
Prevent POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD logic from executing on healthy days.
Allow it to execute unchanged only on hostile days.

CURRENT BEHAVIOR (reference)
POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD logic can execute whenever a post-damage reclaim candidate is evaluated,
regardless of day_class. Healthy day classification does not bypass this guard.

DESIRED BEHAVIOR (exact)
- If day_class == "hostile": POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD logic executes exactly as it does today.
- If day_class != "hostile": POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD logic does not execute at all.
  (Other guards and strategy logic remain unchanged.)

IMPLEMENTATION INSTRUCTIONS
1) Locate day_class
   - Find where day_class is computed for the day within the per-day backtest flow.
   - You must use the existing day_class variable; do not create a new classification system.

2) Locate the guard block
   - Find the complete block that implements POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD and blocks trades.
   - This block includes the [WHY] log line that contains:
     POST_DAMAGE_WEAK_VWAP_RECLAIM_BLOCK
   - Do not change any internal conditions, thresholds, variables, or log contents in this block.

3) Add the regime-level execution gate (single change)
   - Wrap the ENTIRE guard block with:

     if day_class == "hostile":  # v0.8.1.22.0
         <existing POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD block, unchanged>

   - The wrapper must include every line of the guard logic (all checks + all block/log paths).
   - Do NOT partially gate sub-conditions.
   - Do NOT add an else branch.
   - Do NOT change indentation except as required to nest the block.

4) Tagging requirement
   - All new or modified lines must include inline comment: # v0.8.1.22.0
   - Do not add v0.8.1.22.0 tags to unchanged lines.

PROHIBITED CHANGES (must not do)
- No changes to guard internals (definitions, thresholds, damage detection, reclaim detection, conditions)
- No changes to any other guard (DAY_GATE, STRUCT_DAMAGE, VWAP_EXT, CONFIRM_BAR_GUARD, MARGINAL_VWAP_GATE, etc.)
- No changes to sizing, risk, TP/SL, max trades per symbol, logging format, or output files
- No refactors, helper functions, or moving code between functions
- Do not modify REGIME_SUMMARY telemetry from v0.8.1.21.0

SELF-CHECK BEFORE RETURNING PATCH
- Search the updated file and confirm:
  - POST_DAMAGE_WEAK_VWAP_RECLAIM_BLOCK appears only inside the new `if day_class == "hostile"` wrapper.
  - There is exactly one wrapper for this guard block.
  - The guard block’s internal logic is unchanged apart from indentation.
  - No other code blocks were moved or modified.

DELIVERABLE
Return only the updated contents of src/midas_v2/engine/backtester.py.
Do not run anything. Do not include any commands.