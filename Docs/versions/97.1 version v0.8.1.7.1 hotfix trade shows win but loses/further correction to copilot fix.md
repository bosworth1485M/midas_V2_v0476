BEGIN COPILOT SPEC (FINAL — LOCKED)
Midas_V2 v0.8.1.7.1 — Final Cleanup + Consistency Patch
(1) Remove out-of-scope SimpleTradeSummary/context helpers if unused
(2) Ensure TWCS outcome_label matches the exact outcome written to results CSV (TP/SL/ERR_*)

GOAL (EXACT)
This is a surgical follow-up to the v0.8.1.7.1 execution correctness hotfix.

Make ONLY these two improvements in backtester.py:
1) Remove scope-creep code that is not used by the runtime (SimpleTradeSummary formatter + gapmap context loader), IF AND ONLY IF it is unused.
2) Ensure TWCS snapshot metadata uses the SAME outcome string that is appended to trades/results (including ERR_TP_NEG_PNL / ERR_SL_POS_PNL).

This patch must NOT change:
- entry/exit logic
- TP/SL computation logic (including TP_SL_REBASE)
- pnl computation
- strategy logic
- results CSV schema (symbol,outcome,pnl)

FILES ALLOWED TO CHANGE (ONLY)
- src/midas_v2/engine/backtester.py

NON-GOALS / DO NOT DO
- Do NOT modify strategy.py or any other file.
- Do NOT add new helper functions.
- Do NOT refactor control flow.
- Do NOT change CSV schema.
- Do NOT clamp/flip pnl.
- Do NOT add any runner/CLI code or commands.

============================================================
PART A — TWCS OUTCOME CONSISTENCY (REQUIRED)
============================================================

PROBLEM
In the TP/SL close branches, the code can append an ERR_* outcome to trades/results,
but the TWCS exit snapshot still uses outcome_label="TP" or outcome_label="SL".
This creates CSV vs TWCS mismatch.

REQUIRED FIX (MINIMAL)
In BOTH TP and SL close branches, compute ONE variable named `outcome` that matches what is appended to trades,
and then use that same `outcome` for TWCS meta outcome_label.

MANDATORY PLACEMENT ANCHORS (DO NOT GUESS)
In backtester.py, find the close logic branches:

TP branch anchor:
- if pos_bar.h >= tp:
- pnl = (tp - entry) * qty
- existing invariant check sets ERR_TP_NEG_PNL vs TP
- trades.append((sym, "...", pnl))
- then later TWCS exit snapshot block sets:
  outcome_label = "TP"

SL branch anchor:
- elif pos_bar.l <= sl:
- pnl = (sl - entry) * qty
- existing invariant check sets ERR_SL_POS_PNL vs SL
- trades.append((sym, "...", pnl))
- then later TWCS exit snapshot block sets:
  outcome_label = "SL"

EXACT CHANGE FOR TP BRANCH
Replace the existing “if pnl < 0 … append ERR_TP_NEG_PNL else append TP” structure with this exact pattern:

1) Compute `outcome`:
   outcome = "ERR_TP_NEG_PNL" if pnl < 0 else "TP"

2) If outcome is ERR_TP_NEG_PNL, keep the existing loud WHY log OUTCOME_PNL_MISMATCH exactly as-is
   (same fields, same message style, keep v0.8.1.7.1 tag).
   IMPORTANT: Do not change pnl, do not change entry/tp/sl.

3) Append exactly once:
   trades.append((sym, outcome, pnl))

4) In the TWCS exit snapshot block in this TP branch:
   Replace:
     outcome_label = "TP"
   With:
     outcome_label = outcome

EXACT CHANGE FOR SL BRANCH
Do the analogous change:

1) outcome = "ERR_SL_POS_PNL" if pnl > 0 else "SL"

2) If outcome is ERR_SL_POS_PNL, keep the existing loud WHY log OUTCOME_PNL_MISMATCH exactly as-is.

3) trades.append((sym, outcome, pnl)) exactly once.

4) In the TWCS exit snapshot block in this SL branch:
   Replace:
     outcome_label = "SL"
   With:
     outcome_label = outcome

MANDATORY CHECK
After edits, ensure:
- trades.append happens exactly once per TP close and once per SL close
- TWCS outcome_label is always the same string as the appended outcome

============================================================
PART B — REMOVE SCOPE-CREEP HELPERS IF UNUSED (CONDITIONAL)
============================================================

PROBLEM
The file currently contains large blocks:
- SimpleTradeSummary dataclass
- format_simple_trade_calcs(...)
- _load_symbol_context_from_gapmap(...) and related ranking/context helpers
These are out-of-scope for an execution correctness hotfix and should not ship in v0.8.1.7.1 unless used.

RULE (MANDATORY)
Delete these blocks ONLY IF they are UNUSED by backtester.py runtime after the removal of the previous summary-print feature.
“Unused” means there are no references to the symbol names anywhere in backtester.py besides their own definitions.

REQUIRED PROCEDURE (DO NOT GUESS)
1) Search within backtester.py for references to each of these identifiers:
   - SimpleTradeSummary
   - format_simple_trade_calcs
   - _load_symbol_context_from_gapmap

2) If an identifier is referenced ONLY at its own definition (no other references), it is unused.

3) If unused, delete the entire definition block(s):
   - Delete the SimpleTradeSummary dataclass definition
   - Delete the entire format_simple_trade_calcs function
   - Delete the entire _load_symbol_context_from_gapmap function (and any helper functions that are only used by it)
   - Remove any now-unused imports caused by those deletions (but do not touch unrelated imports)

4) If ANY of these identifiers is referenced outside its definition, do NOT delete it.

IMPORTANT
- Do not delete TWCS code.
- Do not delete TP_SL_REBASE logic.
- Do not delete invariant enforcement logic.
- Do not refactor.

============================================================
FINAL CHECKS (MANDATORY)
============================================================
1) backtester.py has no syntax errors.
2) TP/SL hotfix logic remains unchanged:
   - TP_SL_REBASE block remains intact
   - ERR_TP_NEG_PNL / ERR_SL_POS_PNL invariant enforcement remains intact
3) TWCS meta outcome_label matches the appended trades outcome (TP/SL/ERR_*).
4) No behavior changes besides (a) TWCS label alignment and (b) removal of truly-unused helper code.

END COPILOT SPEC (FINAL — LOCKED)






