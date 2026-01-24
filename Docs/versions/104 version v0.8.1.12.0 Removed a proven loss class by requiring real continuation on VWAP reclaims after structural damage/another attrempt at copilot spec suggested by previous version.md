# COPILOT IMPLEMENTATION SPEC (FINAL — CORRECTED & LOCKED)
## Midas_V2 v0.8.1.12.0
### Post-Damage VWAP Reclaim Continuation Guard

IMPORTANT (USER WORKFLOW):
- Generate code changes ONLY via Copilot (no manual edits).
- Add inline comments with "v0.8.1.12.0" next to any new/modified code.

------------------------------------------------------------
GOAL (EXACT)
------------------------------------------------------------
Block a proven dominant loss class:
Late VWAP reclaims that occur AFTER structural damage but lack continuation strength,
leading to immediate SL (e.g., CYRX 2025-08-06, CNEY 2025-05-07 TWCS).

This version introduces ONE new guard only:
Post-Damage VWAP Reclaim Continuation Guard.

This must:
- Block single-candle VWAP reclaim entries after structural damage.
- Preserve all existing correct behavior otherwise.
- Be fully A/B testable using the same ranges already used (Aug / Oct / Nov 2025).

------------------------------------------------------------
FILES ALLOWED TO CHANGE (ONLY)
------------------------------------------------------------
- src/midas_v2/engine/backtester.py

NO other files.  
NO config changes.  
NO new imports.  
NO refactors.  
NO new helpers.

------------------------------------------------------------
NON-NEGOTIABLE CONSTRAINTS
------------------------------------------------------------
Do NOT change any existing guards:
- marginal VWAP window gate (v0.8.1.11.0)
- confirm-bar stop violation guard
- structural damage guard (v0.8.1.4.0) thresholds
- VWAP extension gate
- post-entry expansion gate
- day-gate logic / marginal-day override / caps

Do NOT change StrategyParams, risk, sizing, TP/SL logic, or exits.

Must be deterministic and local.

Use existing log-once latch `early_reject_logged` for rejection logging.

------------------------------------------------------------
CODE REALITY (IMPORTANT — DO NOT RE-IMPLEMENT)
------------------------------------------------------------
In `src/midas_v2/engine/backtester.py`:

The combined entry condition is:

if (not effective_day_gate_failed) and position is None and pending_entry is None
and strat.should_enter(bars, i) and risk.allow_new_trade():

scss
Copy code

Inside that block, the existing Structural Damage Guard runs ONLY when:
reject_reclaim_after_damage_effective == True

markdown
Copy code

That block:
- detects `recent_structural_damage` in lookback [i-8, i-1]
- computes a local `vwap_map` (incremental typical price) for indices 0..i
- checks `recovery_passed` for bars [i-1, i]
- logs either:
  - `STRUCT_DAMAGE ... BLOCKED ...`
  - or `STRUCT_DAMAGE ... PASSED ... reason=accepted_above_vwap`

v0.8.1.12.0 must NOT change any of that logic.

------------------------------------------------------------
NEW GUARD (v0.8.1.12.0) — EXACT RULE
------------------------------------------------------------
NAME:
Post-Damage VWAP Reclaim Continuation Guard

WHEN IT APPLIES (EXACT):
Only inside the combined entry block, ONLY in the branch where ALL are true:
- `reject_reclaim_after_damage_effective == True`
- `recent_structural_damage == True`
- `recovery_passed == True`
- `blocked == False` (i.e., structural damage guard did NOT block)

If `reject_reclaim_after_damage_effective == False`, this guard does NOT run.

------------------------------------------------------------
RULE (LOCKED)
------------------------------------------------------------
Using the SAME `vwap_map` already computed inside the structural-damage block
(do not refactor, do not move, do not rebuild elsewhere):

Count how many of the last 3 COMPLETED bars BEFORE the entry bar satisfy:
- green: `close > open`
- above VWAP: `close > vwap_map[j]`

Bars to test: `[i-1, i-2, i-3]`
- Skip any index < 0
- Treat missing or None VWAP as FAIL

PASS condition:
green_above_vwap_count >= 2

markdown
Copy code

If count < 2:
- BLOCK this entry attempt (delay/quality filter)
- Use `continue` to skip this bar’s entry attempt

IMPORTANT:
- Do NOT include the current entry bar `i` in this count.
- This guard exists specifically to prevent “single reclaim candle” entries after damage.

------------------------------------------------------------
PLACEMENT (CRITICAL — EXACT ANCHOR)
------------------------------------------------------------
Edit ONLY `src/midas_v2/engine/backtester.py`.

Find the combined entry block shown above.

Inside it, locate the existing structural damage guard:

if reject_reclaim_after_damage_effective:
...
if recent_structural_damage:
...
if not recovery_passed:
blocked = True
log.info("... BLOCKED ...")
else:
log.info("... PASSED ... accepted_above_vwap")

markdown
Copy code

INSERT v0.8.1.12.0 guard HERE (exactly):

- Immediately AFTER the line that logs:
  `STRUCT_DAMAGE v0.8.1.4.0: PASSED ... reason=accepted_above_vwap`
- Immediately BEFORE the later code that does:
  `entry = bar.c`
  `tp, sl = strat.targets(entry)`

Do NOT move blocks.  
Do NOT reorder checks.

------------------------------------------------------------
BLOCKING BEHAVIOR + LOGGING (LOG-ONCE)
------------------------------------------------------------
If `green_above_vwap_count < 2`:

- Block this entry attempt using:
continue

sql
Copy code

- Log ONCE per symbol per day using existing `early_reject_logged`.

Use reject key:
reject_key = f"{date_str}:{sym}:POST_DAMAGE_CONTINUATION_FAIL"

pgsql
Copy code

Log as WARNING, single structured line:
[WHY] v0.8.1.12.0 POST_DAMAGE_CONTINUATION_BLOCK
symbol={sym} ts={candidate_ts} count={count} window=i-1,i-2,i-3

markdown
Copy code

IMPORTANT SAFETY RULE:
- **Do NOT reuse, modify, or overwrite the existing `blocked` variable**.
- This guard must be implemented as a pure “skip this bar’s entry attempt” via `continue`,
  not by mutating structural-damage state.

Do NOT add additional logs.  
Do NOT change any other reject keys.

------------------------------------------------------------
IMPLEMENTATION STEPS (DO EXACTLY)
------------------------------------------------------------
1) Open `src/midas_v2/engine/backtester.py`.
2) Find the combined entry condition block.
3) Find the existing structural damage guard inside it.
4) In the branch where:
   - structural damage is detected AND
   - recovery_passed is True,
   immediately after the existing "STRUCT_DAMAGE ... PASSED" log:
   - compute continuation count over `[i-1, i-2, i-3]` using `vwap_map`
   - qualify bar j if:
     `(bars[j].c > bars[j].o) and (vwap_map[j] is not None) and (bars[j].c > vwap_map[j])`
5) If count < 2:
   - log once using `early_reject_logged` and reject_key
   - `continue`
6) Otherwise, proceed unchanged to:
   `entry = bar.c`
   `tp, sl = strat.targets(entry)`

Add inline comments with `"v0.8.1.12.0"` adjacent to all new logic.

------------------------------------------------------------
VALIDATION PLAN (MANDATORY — A/B)
------------------------------------------------------------
Use the standard range runner and log to files.

Step 1 — Sanity:
- Verify CYRX-type and CNEY-type post-damage weak reclaims are blocked.
- Verify no regressions on clean entries.

Step 2 — Full-month A/B vs v0.8.1.11.0 baseline:
Run the exact same ranges already validated:
- 2025-08-01 → 2025-08-31
- 2025-10-01 → 2025-10-31
- 2025-11-01 → 2025-11-30

Success criteria (any ONE):
- ≥30% reduction in SL count, OR
- Meaningful PnL improvement, OR
- Clear removal of known failure trades with no regression on winners.

------------------------------------------------------------
END OF SPEC (LOCKED)