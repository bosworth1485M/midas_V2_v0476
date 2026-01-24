BEGIN COPILOT SPEC (FINAL — LOCKED)
Midas_V2 v0.8.1.13.0
Blocked-trade tiny JSON snapshot (diagnostics-only)
DO NOT RUN ANYTHING. DO NOT CHANGE BEHAVIOR.

====================================================================
GOAL (EXACT)
====================================================================
When the system BLOCKS a trade due to the post-damage VWAP reclaim continuation guard,
write a tiny JSON file explaining why it was blocked.

This version is observability only:
- Must not change which trades happen.
- Must not change PnL, results CSVs, TWCS, or existing logs.
- Must not add new guards or alter guard thresholds.

====================================================================
HARD RULES (NON-NEGOTIABLE)
====================================================================
1) Do not run any commands. Do not run tests. Do not execute scripts.
2) One file only may be edited:
   - src/midas_v2/engine/backtester.py
3) No refactors. No helper modules. No new imports at file top.
4) Best-effort only: JSON write must be wrapped in try/except so failures never affect trading logic.
5) No new log lines. Do not alter existing log strings or levels.
6) Do not change control flow other than inserting a best-effort write immediately before an
   already-existing continue.

====================================================================
WHAT COUNTS AS “BLOCKED” IN THIS VERSION
====================================================================
ONLY this block, ONLY this reason, ONLY this guard:

- Existing log anchor line:
  "[WHY] v0.8.1.12.0 POST_DAMAGE_CONTINUATION_BLOCK ..."

- The block occurs when:
  green_above_vwap_count < 2

- It currently does:
  - logs once (via early_reject_logged)
  - then continue

v0.8.1.13.0 adds:
  write a JSON snapshot best-effort, then proceeds with the exact same continue.

DO NOT add JSON snapshots for any other reject reasons in this version.

====================================================================
EXACT INSERTION POINT (CODE REALITY — DO NOT MOVE)
====================================================================
In run_backtest() inside the main bar loop, find:

- Comment anchor:
  "# v0.8.1.12.0: Post-Damage VWAP Reclaim Continuation Guard"

- Specifically the rejection condition:

    if green_above_vwap_count < 2:
        reject_key = f"{date_str}:{sym}:POST_DAMAGE_CONTINUATION_FAIL"
        if reject_key not in early_reject_logged:
            candidate_ts = bar.ts if hasattr(bar, 'ts') else f"bar_{i}"
            log.warning(
                f"[WHY] v0.8.1.12.0 POST_DAMAGE_CONTINUATION_BLOCK symbol={sym} ts={candidate_ts} "
                f"count={green_above_vwap_count} window=i-1,i-2,i-3 recovery_passed=True recent_structural_damage=True"
            )
            early_reject_logged.add(reject_key)
        continue

Insert the JSON write inside the:
    if reject_key not in early_reject_logged:
block.

Placement requirement:
- Prefer inserting AFTER early_reject_logged.add(reject_key) so the latch is set even if file I/O fails,
  and still before the existing continue.
- Do NOT change the log string.
- Do NOT change the continue behavior.

====================================================================
OUTPUT LOCATION (MUST USE out_dir; DO NOT HARDCODE)
====================================================================
Do NOT hardcode "out/YYYYMMDD/B/...".

Use the already-existing variable out_dir (created earlier via os.makedirs(out_dir, exist_ok=True)
and used for results CSV).

Create:
- blocked_dir = os.path.join(out_dir, "blocked_candidates")
- os.makedirs(blocked_dir, exist_ok=True) (inside try/except)

File name format (exact):
- POST_DAMAGE_CONTINUATION_BLOCK_{SYMBOL}_{TS}.json

Where:
- SYMBOL = sym
- TS = candidate_ts with ":" removed and any non-filename-safe chars replaced with "_"
  Example: "10:14" -> "1014"

====================================================================
JSON CONTENT (TINY + DETERMINISTIC)
====================================================================
Write a JSON object with only small scalar fields.
NO arrays of bars. NO TWCS payloads. NO indicator windows.

REQUIRED keys (exact):
- version: "v0.8.1.13.0"
- reason: "POST_DAMAGE_CONTINUATION_BLOCK"
- symbol: sym
- date: date_str
- ts: candidate_ts
- i: i
- count: green_above_vwap_count
- window: "i-1,i-2,i-3"
- recent_structural_damage: True
- recovery_passed: True
- scenario: (scenario_name or scn)
- day_class: day_class

OPTIONAL keys (ONLY if trivially available in-scope at that exact location; DO NOT compute):
- auto_struct_damage: auto_enabled
- reject_reclaim_effective: reject_reclaim_after_damage_effective

If an optional var is not in scope, omit it (do not compute it, do not add new data plumbing).

Serialization requirements:
- Use a local import: "import json" inside the try block (do not add top-level imports).
- Write deterministic formatting:
  json.dump(payload, f, indent=2, sort_keys=True)
- Use encoding="utf-8".

====================================================================
ERROR HANDLING (MUST BE SILENT + NON-BLOCKING)
====================================================================
Wrap the entire JSON write in:

    try:
        ...
    except Exception:
        pass

No print. No log. No re-raise.

====================================================================
BEHAVIOR PRESERVATION CHECKLIST (COPILOT MUST SELF-VERIFY)
====================================================================
Before finishing, verify by inspection that:
1) The existing continue remains and still executes exactly as before.
2) No new continue/break/return was added.
3) No existing logging strings were changed.
4) No other reject reasons produce JSON.
5) Only one file changed.
6) No top-level imports were added.

====================================================================
FILES ALLOWED TO CHANGE (ONLY)
====================================================================
- src/midas_v2/engine/backtester.py

No changes to:
- config/scenarios.json
- any scripts
- any TWCS code
- any docs

====================================================================
DO NOT RUN ANYTHING
====================================================================
After edits, stop. Do not execute:
- python ...
- range runner
- unit tests
- linters

END COPILOT SPEC (FINAL — LOCKED)
