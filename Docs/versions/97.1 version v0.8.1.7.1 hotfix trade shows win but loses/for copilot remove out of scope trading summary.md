BEGIN COPILOT SPEC (FINAL — LOCKED)
Midas_V2 v0.8.1.7.1 — Cleanup: Remove out-of-scope trade summary printing added by Copilot

GOAL (EXACT)
Remove ONLY the out-of-scope “Build and print a SimpleTradeSummary …” blocks that were added inside backtester.py
during the v0.8.1.7.1 hotfix implementation.

This cleanup must NOT change any trading logic, entry/exit logic, TP/SL logic, TP_SL_REBASE logic, or the ERR_* invariant logic.
It must ONLY delete the extra printing/summary feature code.

FILES ALLOWED TO CHANGE (ONLY)
- src/midas_v2/engine/backtester.py

NON-GOALS / DO NOT DO
- Do NOT change any existing logic besides deleting the summary-print blocks.
- Do NOT modify TP_SL_REBASE.
- Do NOT modify the TP/SL invariant enforcement (ERR_TP_NEG_PNL / ERR_SL_POS_PNL).
- Do NOT add new helper functions or refactor.
- Do NOT change logging except removing logs that belong to the deleted summary feature.

WHAT TO REMOVE (MANDATORY)
In backtester.py, locate the TP close branch that contains:
- the existing close condition: if pos_bar.h >= tp:
- and after the trades.append(...) line, there is a comment or section starting with:
  "Build and print a SimpleTradeSummary" (or equivalent)
Delete that entire block, from that comment header through the end of the summary/printing code,
stopping immediately before normal control flow resumes.

Also locate the SL close branch (elif pos_bar.l <= sl:) and remove the analogous summary/printing block
(if present) that was added by Copilot.

WHAT MUST REMAIN (MANDATORY)
- The TP_SL_REBASE audit code in the POST_EXP confirmed entry path must remain unchanged.
- The TP invariant block that converts TP with negative pnl into ERR_TP_NEG_PNL must remain unchanged.
- The SL invariant block that converts SL with positive pnl into ERR_SL_POS_PNL must remain unchanged.
- Existing position lifecycle logs (POST_EXP: CONFIRMED, POST_EXP: POSITION_SET, etc.) must remain unchanged.

FINAL CHECK (MANDATORY)
After deletion, re-read the modified TP and SL close branches and confirm:
- The only code after trades.append(...) is the original pre-existing control flow (no new printing/summary code).
- No syntax errors.

END COPILOT SPEC (FINAL — LOCKED)
