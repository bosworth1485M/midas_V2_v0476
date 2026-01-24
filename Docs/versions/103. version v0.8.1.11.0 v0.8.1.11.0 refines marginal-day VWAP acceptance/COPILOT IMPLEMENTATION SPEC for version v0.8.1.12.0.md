# COPILOT IMPLEMENTATION SPEC (FINAL — LOCKED)
# Midas_V2 v0.8.1.12.0
# Post-Damage VWAP Reclaim Continuation Guard
#
# IMPORTANT (USER WORKFLOW):
# - Generate code changes ONLY via Copilot (no manual edits).
# - Add inline comments with "v0.8.1.12.0" next to any new/modified code.

------------------------------------------------------------
GOAL (EXACT)
------------------------------------------------------------
Block a proven dominant loss class:
Late VWAP reclaims that occur AFTER structural damage but lack continuation strength,
leading to immediate SL (e.g., CYRX 2025-08-06, CNEY 2025-05-07 TWCS).

This version introduces ONE new guard only:
Post-Damage VWAP Reclaim Continuation Guard.

This must:
- Reduce post-damage weak reclaim entries (single-candle reclaims).
- Preserve all existing correct behavior otherwise.
- Be fully A/B testable using the same month ranges already used (Aug/Oct/Nov 2025).

------------------------------------------------------------
FILES ALLOWED TO CHANGE (ONLY)
------------------------------------------------------------
- src/midas_v2/engine/backtester.py

NO other files.
NO config changes.
NO new helpers.
NO new imports.
NO refactors.
NO moving blocks.

------------------------------------------------------------
NON-NEGOTIABLE CONSTRAINTS
------------------------------------------------------------
1) Do NOT change any existing guards:
   - marginal VWAP window gate (v0.8.1.11.0)
   - confirm-bar stop violation guard
   - structural damage guard (v0.8.1.4.0) thresholds
   - VWAP extension gate
   - post-entry expansion gate
   - day-gate logic / marginal-day override / caps
2) Do NOT change entry/exit logic, TP/SL, sizing, risk, position management.
3) Do NOT add indicators or change StrategyParams.
4) The change must be deterministic and local.
5) Use existing log-once latch `early_reject_logged` for rejection logging.

------------------------------------------------------------
CODE REALITY (IMPORTANT — DO NOT RE-IMPLEMENT)
------------------------------------------------------------
In src/midas_v2/engine/backtester.py:
- Entries occur inside a combined entry condition block:
  `if (not effective_day_gate_failed) and position is None and pending_entry is None and strat.should_enter(bars, i) and risk.allow_new_trade():`

- Inside that entry block, the Structural Damage Guard (v0.8.1.4.0) already:
  - Detects `recent_structural_damage` in a lookback window.
  - Logs "STRUCT_DAMAGE ... detected/PASSED/BLOCKED".
  - Computes an incremental VWAP map locally (typical-price method).

v0.8.1.12.0 must NOT change the structural damage guard logic.
It must add a NEW continuation requirement ONLY when structural damage is detected.

------------------------------------------------------------
NEW GUARD (v0.8.1.12.0) — EXACT RULE
------------------------------------------------------------
NAME:
Post-Damage VWAP Reclaim Continuation Guard

WHEN IT APPLIES:
- Only inside the combined entry block (same bar i evaluation),
- Only after structural damage detection has been evaluated,
- Only if structural damage WAS DETECTED (recent_structural_damage == True),
- Only if the structural damage guard would otherwise PASS (i.e., we are not blocked by it),
- Only when entry would otherwise proceed.

RULE (LOCKED):
Compute VWAP for each bar using the existing incremental typical-price method.
Then count how many of the last 3 COMPLETED bars before the entry bar satisfy:

- green: close > open
- above VWAP: close > vwap_at_that_bar

Bars to test: [i-1, i-2, i-3] (skip any idx < 0)

PASS condition:
`green_above_vwap_count >= 2`

If count < 2:
- BLOCK this entry attempt (skip this bar’s entry attempt).
- This is a DELAY/QUALITY filter: it forces continuation evidence after damage.

IMPORTANT:
- Do NOT include the current entry bar `i` in the count.
  The purpose is to prevent “single reclaim candle” entries after damage.

------------------------------------------------------------
PLACEMENT (CRITICAL — EXACT ANCHOR)
------------------------------------------------------------
Edit ONLY src/midas_v2/engine/backtester.py.

Find the combined entry condition block:

`if (not effective_day_gate_failed) and position is None and pending_entry is None and strat.should_enter(bars, i) and risk.allow_new_trade():`

Inside that block:
1) The STRUCT_DAMAGE logic runs early.
2) Insert the v0.8.1.12.0 continuation guard:
   - Immediately AFTER the structural damage detection / pass logic is evaluated,
   - Immediately BEFORE the code assigns `entry = bar.c` and computes `tp, sl = strat.targets(entry)`.

Do NOT move blocks.
Do NOT create new functions.

------------------------------------------------------------
VWAP COMPUTATION FOR THIS GUARD (NO NEW METHODS)
------------------------------------------------------------
For the continuation check, compute VWAP using the SAME style already used in STRUCT_DAMAGE:

- typical = (h + l + c) / 3
- running_pv += typical * volume
- running_v += volume
- vwap_j = running_pv / running_v if running_v > 0 else None

Build a local `vwap_map` for indices 0..i-1 (completed bars only).
Do NOT rely on `bars[j].vwap` fields.

This vwap_map is local to the entry attempt and used only for the count.
Do not refactor or unify with other vwap_map blocks.

------------------------------------------------------------
BLOCKING BEHAVIOR + LOGGING (LOG-ONCE)
------------------------------------------------------------
If `green_above_vwap_count < 2`:

- Block this entry attempt for this bar i by using:
  `continue`
  (skip this bar’s entry attempt)

- Log ONCE per symbol per day using existing `early_reject_logged`.

Use reject key:
`reject_key = f"{date_str}:{sym}:POST_DAMAGE_CONTINUATION_FAIL"`

Log as WARNING, single line, structured:
`[WHY] v0.8.1.12.0 POST_DAMAGE_CONTINUATION_BLOCK symbol={sym} ts={candidate_ts} count={count} window=i-1,i-2,i-3`

Do NOT add additional logs.
Do NOT change any other reject keys.

------------------------------------------------------------
WHAT MUST NOT CHANGE
------------------------------------------------------------
- Structural damage detection thresholds and windows.
- Whether structural damage guard PASSES/BLOCKS on any given bar.
- Marginal VWAP window gate behavior and logging.
- The order of checks in the entry block.
- Pending entry (post-expansion gate) behavior.
- Any exit logic or TP/SL logic.
- Any sizing logic.

------------------------------------------------------------
IMPLEMENTATION STEPS (DO EXACTLY)
------------------------------------------------------------
1) Open src/midas_v2/engine/backtester.py
2) Find the combined entry condition block (see anchor above).
3) Identify the STRUCT_DAMAGE guard code inside that block.
4) After STRUCT_DAMAGE is evaluated (and only when damage was detected and not blocked),
   compute the continuation count over bars [i-1, i-2, i-3] using local vwap_map (0..i-1).
5) If count < 2:
   - log once using early_reject_logged and the reject_key specified
   - continue (skip entry attempt)
6) Otherwise, proceed unchanged to existing `entry = bar.c` and target computation.

Add inline comments with "v0.8.1.12.0" adjacent to new logic.

------------------------------------------------------------
VALIDATION PLAN (MANDATORY — A/B)
------------------------------------------------------------
Use the standard range runner and log to files.

Step 1 (sanity):
- Verify that CYRX-type and CNEY-type post-damage weak reclaims are blocked when they occur.
- Verify no regressions on clean entries.

Step 2 (full-month A/B vs v0.8.1.11.0 baseline):
Run the exact same ranges already used:
- 2025-08-01 → 2025-08-31
- 2025-10-01 → 2025-10-31
- 2025-11-01 → 2025-11-30

Success criteria (any ONE):
- ≥30% reduction in SL count, OR
- Meaningful PnL improvement, OR
- Clear removal of known failure trades with no regression on winners.

------------------------------------------------------------
END OF SPEC (LOCKED)
------------------------------------------------------------