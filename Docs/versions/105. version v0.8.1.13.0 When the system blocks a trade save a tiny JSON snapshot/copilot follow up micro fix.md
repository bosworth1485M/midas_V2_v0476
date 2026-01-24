BEGIN COPILOT SPEC (FINAL — LOCKED)
Midas_V2 v0.8.1.13.0 (micro-fix)
Fix blocked-trade JSON snapshot: scenario field must never be None
DO NOT RUN ANYTHING. DO NOT CHANGE BEHAVIOR.

====================================================================
GOAL (EXACT)
====================================================================
In the existing v0.8.1.13.0 blocked-trade JSON snapshot payload for
POST_DAMAGE_CONTINUATION_BLOCK, change the "scenario" field so it is
always populated with the effective scenario identifier.

Currently it writes:
    "scenario": scenario_name

Change it to:
    "scenario": (scenario_name or scn)

This is a diagnostics-only correctness fix. It must not alter trade logic.

====================================================================
HARD RULES (NON-NEGOTIABLE)
====================================================================
1) Do not run any commands. Do not run tests. Do not execute scripts.
2) One file only may be edited:
   - src/midas_v2/engine/backtester.py
3) Make the smallest possible change (single-field edit).
4) Do not modify any existing log strings or log levels.
5) Do not change control flow (no new continue/break/return).
6) Do not add imports, helpers, or refactors.

====================================================================
EXACT CHANGE (ONLY)
====================================================================
In src/midas_v2/engine/backtester.py, locate the v0.8.1.13.0 block:

    # v0.8.1.13.0: Write blocked-trade JSON snapshot (best-effort, diagnostics-only)
    try:
        import json
        ...
        payload = {
            ...
            "scenario": scenario_name,
            ...
        }
        ...

Replace ONLY this one line in the payload dict:

FROM:
    "scenario": scenario_name,  # v0.8.1.13.0

TO:
    "scenario": (scenario_name or scn),  # v0.8.1.13.0

Do not change any other keys, ordering, formatting, or comments.
Keep the version comment on the line.

====================================================================
BEHAVIOR PRESERVATION CHECKLIST (COPILOT MUST SELF-VERIFY)
====================================================================
- Existing continue remains exactly as-is.
- No trade entry/exit behavior changed.
- No log strings changed.
- Only one file changed.
- No new imports at top of file.
- scenario is now always non-None when scn is available.

====================================================================
FILES ALLOWED TO CHANGE (ONLY)
====================================================================
- src/midas_v2/engine/backtester.py

====================================================================
DO NOT RUN ANYTHING
====================================================================
After edits, stop. Do not execute python, range runner, or any tests.

END COPILOT SPEC (FINAL — LOCKED)
