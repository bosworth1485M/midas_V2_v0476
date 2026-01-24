COPILOT IMPLEMENTATION SPEC — v0.8.1.29.0
Fix empty-window MARGINAL_VWAP_WINDOW_REJECT at market open (i<3) to restore Cameron alignment

CRITICAL RULE: DO NOT RUN ANYTHING
- Do NOT run python, backtests, or any commands.
- Implementation only.

TARGET FILE (ONLY)
- src/midas_v2/engine/backtester.py

SCOPE (NON-NEGOTIABLE)
- One change only: prevent MARGINAL_VWAP_WINDOW_REJECT from rejecting when the window is empty (i<3).
- No refactors. No helpers. No moving blocks. No parameter tuning.
- Do not change DAY_GATE throttle, ASC_GREEN, VWAP_EXT, POST_DAMAGE locks, sizing, TP/SL, or any scenario params.
- Keep all existing behavior unchanged when i >= 3.

PROBLEM (EVIDENCE / CODE REALITY)
- The guard v0.8.1.11.0 MARGINAL_VWAP_WINDOW_REJECT builds:
  window = [i-1, i-2, i-3]
  and skips negative indices.
- For i in {0,1,2} (e.g. market open 09:30), all indices are <0 -> loop yields hits=0.
- Current logic treats hits<2 as a rejection and logs:
  MARGINAL_VWAP_WINDOW_REJECT ... ts=09:30 hits=0
- Dedupe key date+sym+reject-type hides later, meaningful rejects.

GOAL
- Treat i<3 (insufficient history / empty window) as “INSUFFICIENT WINDOW” and do NOT reject.
- This should restore Cameron-aligned behavior: insufficient data -> wait/unknown, not a hard suppressor.

PATCH INSTRUCTIONS (MINIMAL CHANGE)

1) Locate the v0.8.1.11.0 block that logs:
   "[WHY] v0.8.1.11.0 MARGINAL_VWAP_WINDOW_REJECT ... hits=..."
   It will be near where window=[i-1,i-2,i-3] is created and hits is counted.

2) Implement the i<3 bypass in the SAFEST STRUCTURE (preferred):
   - Wrap the EXISTING window/hits/reject logic with an `if i >= 3:` guard.
   - This avoids introducing any new `continue` in the bypass path.

   REQUIRED behavior:
   - If i < 3:
       - DO NOT emit the WARNING reject log for MARGINAL_VWAP_WINDOW_REJECT
       - DO NOT add the dedupe reject_key for this reject
       - DO NOT increment telemetry counters for this gate block
       - Do NOT `continue` (the bypass must allow the rest of the bar evaluation to proceed normally)
       - Simply skip this gate and keep evaluating other entry logic for this bar

   - If i >= 3:
       - Preserve the existing behavior EXACTLY, including:
         - computing hits over window {i-1,i-2,i-3}
         - rejecting when hits < 2
         - logging the existing WARNING message
         - adding the existing reject_key
         - incrementing telemetry for this gate block
         - continuing (rejecting) for that bar only

3) Optional breadcrumb (non-blocking, low-noise):
   - You MAY add a single INFO or DEBUG line for the i<3 case, but only if deduped per symbol/day, e.g.:
     "[WHY] v0.8.1.29.0 MARGINAL_VWAP_WINDOW_INSUFFICIENT symbol=XYZ ts=09:30 i=0"
   - If you add this, dedupe with early_reject_logged using a distinct key:
     f"{date_str}:{sym}:MARGINAL_VWAP_WINDOW_INSUFFICIENT"
   - DO NOT log this as WARNING.

4) Telemetry correctness:
   - Ensure telemetry["count_marginal_vwap_gate_blocks"] (or equivalent) is NOT incremented for i<3.
   - Keep telemetry behavior unchanged for i>=3.

5) Preserve existing behavior:
   - When i >= 3, keep the exact current logic and thresholds, including hits<2 rejection and warning log.
   - Do NOT change the dedupe key for the reject in this version (observability-only changes are not the goal here).

VERSION TAGGING (REQUIRED)
- Any new/modified lines must include inline comments:
  - # v0.8.1.29.0 (ALIGNMENT)
  - # v0.8.1.29.0 (SAFETY)
  - # v0.8.1.29.0 (OBSERVABILITY)

STOP CONDITIONS
- If you are about to modify any file other than backtester.py, STOP.
- If you are about to refactor or extract helpers, STOP.
- If you are about to run any code/tests, STOP.

POST-PATCH SELF-CHECK (NO RUNS)
- Confirm the new i<3 bypass is local to the MARGINAL_VWAP_WINDOW_REJECT block.
- Confirm other guards are untouched.
- Confirm the code still rejects for hits<2 when i>=3.
- Confirm the bypass does not skip the rest of the bar evaluation (no bypass-path `continue`).

VALIDATION PLAN (DO NOT RUN; DOCUMENT ONLY)
- Sanity: 2025-11-18 -> 2025-11-22 (Scenario B)
- Hostile: 2025-12-02 -> 2025-12-06
- Good: 2025-08-05 -> 2025-08-15
- Older: 2025-07-14 -> 2025-07-18
Success: increased August engagement without reintroducing known loss clusters; TWCS confirms intended failure class removed.
