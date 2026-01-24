BEGIN COPILOT SPEC (FINAL — LOCKED)
Midas_V2 v0.8.1.7.1 — Execution Correctness Hotfix (TP outcomes must never lose money)

GOAL (EXACT)
Fix an execution/accounting correctness bug where trades labeled outcome="TP" can have negative pnl (impossible).
After this change, TP outcomes must never lose money, and SL outcomes must never make money.
This is a correctness hotfix. It must not change strategy logic, signals, filters, or day gating.

WHY (EVIDENCE / SYMPTOMS)
We have observed “impossible days” where Win% is 100% but totalPnL < 0, implying TP-labeled outcomes with negative pnl.
Known-bad examples include days/symbols like:
- 2025-04-01 ICCT
- 2025-04-07 JNVR / NWTG
- 2025-08-20 NBY
- 2025-08-29 MOVE
- 2025-09-10 WLDS
Root cause is suspected to be post-entry expansion confirmation: TP/SL can be computed at signal-time, but entry is set at confirm-time (entry = bar.c). If TP/SL are not rebased to the new entry price, it can create tp < entry, producing “TP but negative pnl”.

NON-GOALS (DO NOT DO)
- Do NOT change strategy rules, indicators, gates, regime switches, or scenario behavior.
- Do NOT change the results CSV schema (must remain symbol,outcome,pnl).
- Do NOT add new helper functions.
- Do NOT refactor control flow.
- Do NOT re-select bars, re-run signals, or change bar streams.
- Do NOT modify other files.
- Do NOT clamp pnl, flip pnl sign, or “massage” pnl to satisfy invariants.
- Do NOT add any code that runs scripts, runners, or shell commands (validation is human-run only).

FILES ALLOWED TO CHANGE (ONLY)
- src/midas_v2/engine/backtester.py

FILES NOT ALLOWED TO CHANGE
- Anything else (no config changes, no strategy changes, no scripts changes)

------------------------------------------------------------
CHANGE 1 (REQUIRED): Rebase TP/SL at confirm-time entry creation
------------------------------------------------------------

PLACEMENT ANCHORS (MANDATORY — DO NOT GUESS)
In backtester.py, locate the pending-entry confirmation path that emits the existing log:
- POST_EXP: CONFIRMED
and later emits:
- POST_EXP: POSITION_SET

In that same block you will see the sequence:
- entry = bar.c
- then currently tp/sl are taken from pending_entry (tp = pending_entry["tp"], sl = pending_entry["sl"])
- then the position dict is created and the POST_EXP: POSITION_SET log is emitted

EXACT INSERTION POINT (MANDATORY)
Insert the rebase code:
- immediately AFTER the line: entry = bar.c
- immediately BEFORE the line: tp = pending_entry["tp"] (and before sl = pending_entry["sl"])

REQUIRED BEHAVIOR
At the insertion point:
1) Read the old values (signal-time values):
   old_tp = pending_entry["tp"]
   old_sl = pending_entry["sl"]

2) Recompute targets from confirm-time entry:
   new_tp, new_sl = strat.targets(entry)

3) Use the new values for the position that is about to be created:
   tp = new_tp
   sl = new_sl

4) Emit a WHY audit line ONCE per confirmed entry creation:
   - Must include the tag: TP_SL_REBASE
   - Must include: symbol, entry, old_tp, old_sl, new_tp, new_sl
   - Include version tag in the log line: v0.8.1.7.1

5) Proceed to create the position dict exactly as before (same keys, same structure), using entry/tp/sl as set above, and keep the existing POST_EXP: POSITION_SET log.

IMPORTANT CONSTRAINTS
- Do not mutate pending_entry other than reading old_tp/old_sl.
- Do not add new fields to pending_entry.
- Do not change any logic outside this confirm-time creation path.

------------------------------------------------------------
CHANGE 2 (REQUIRED): Enforce outcome ↔ pnl invariants at close
------------------------------------------------------------

PLACEMENT ANCHORS (MANDATORY — DO NOT GUESS)
In backtester.py, locate the close logic branches that look like:

TP branch:
- if pos_bar.h >= tp:
    pnl = (tp - entry) * qty
    trades.append((sym, "TP", pnl))

SL branch:
- elif pos_bar.l <= sl:
    pnl = (sl - entry) * qty
    trades.append((sym, "SL", pnl))

EXACT INSERTION POINTS (MANDATORY)
A) TP branch invariant:
Insert immediately AFTER:
  pnl = (tp - entry) * qty
and immediately BEFORE:
  trades.append((sym, "TP", pnl))

If pnl < 0:
- Emit a loud WHY log line with tag: OUTCOME_PNL_MISMATCH
  Include: symbol, entry, tp, sl, qty, pnl
  Include version tag: v0.8.1.7.1
- Append:
  trades.append((sym, "ERR_TP_NEG_PNL", pnl))
- Do NOT append the original TP outcome in this case.

Otherwise (pnl >= 0), keep the existing TP append exactly as-is.

B) SL branch invariant:
Insert immediately AFTER:
  pnl = (sl - entry) * qty
and immediately BEFORE:
  trades.append((sym, "SL", pnl))

If pnl > 0:
- Emit a loud WHY log line with tag: OUTCOME_PNL_MISMATCH
  Include: symbol, entry, tp, sl, qty, pnl
  Include version tag: v0.8.1.7.1
- Append:
  trades.append((sym, "ERR_SL_POS_PNL", pnl))
- Do NOT append the original SL outcome in this case.

Otherwise (pnl <= 0), keep the existing SL append exactly as-is.

DO NOT “FIX” PNL (MANDATORY)
- Do not clamp pnl to 0
- Do not flip pnl sign
- Do not rewrite entry/tp/sl here
- Only relabel outcome to ERR_* and log loudly

OUTPUT / CSV SCHEMA (MANDATORY)
- Keep results CSV schema unchanged: symbol,outcome,pnl
- Do not add columns. ERR_* must appear only in outcome field.

------------------------------------------------------------
LOGGING REQUIREMENTS (MANDATORY)
------------------------------------------------------------
- Add logs using the existing logging style in backtester.py.
- Every new log line must include version tag “v0.8.1.7.1”.
- TP_SL_REBASE log must be [WHY] style and should be emitted only at confirmed entry creation.
- OUTCOME_PNL_MISMATCH log must be [WHY] style and emitted only when invariants are violated.

------------------------------------------------------------
ACCEPTANCE CRITERIA (MANDATORY)
------------------------------------------------------------
1) After change, there must be ZERO occurrences where:
   outcome == "TP" and pnl < 0
2) After change, there must be ZERO occurrences where:
   outcome == "SL" and pnl > 0
3) If any mismatch exists, it must be labeled ERR_* and logged with OUTCOME_PNL_MISMATCH (pnl must remain unchanged).
4) Confirm TP_SL_REBASE appears for confirmed entries in post-expansion mode and shows old vs new tp/sl.

------------------------------------------------------------
VALIDATION COMMANDS (HUMAN-RUN ONLY — COPILOT MUST NOT EXECUTE)
------------------------------------------------------------
IMPORTANT:
- The following commands are for the HUMAN to copy/paste in PowerShell after the patch.
- Copilot must NOT add code to run these commands or invoke shells/runners.

A) Re-run a known-bad day (example)
python scripts\run_range_and_summarize.py --start 2025-04-07 --end 2025-04-07 --scenario B | Tee-Object -FilePath .\out\20250407\B\runlog_2025-04-07_B_v0.8.1.7.1.txt

B) Confirm rebase/invariant logs exist (if triggered)
Select-String -Path .\out\20250407\B\runlog_2025-04-07_B_v0.8.1.7.1.txt -Pattern "TP_SL_REBASE|OUTCOME_PNL_MISMATCH|POST_EXP: CONFIRMED|POST_EXP: POSITION_SET|pnl="

C) Scan all result CSVs for illegal TP negative pnl
python -c "import glob,csv; bad=[]; [bad.append((f,r.get('symbol'),r.get('pnl'),r.get('outcome'))) for f in glob.glob('out/2025*/B/results_2025-*.csv') for r in csv.DictReader(open(f,newline='')) if r.get('outcome')=='TP' and float(r.get('pnl') or 0)<0]; print('TP_but_negative_pnl=',len(bad)); print('\n'.join(map(str,bad[:50])))"

D) Scan all result CSVs for illegal SL positive pnl
python -c "import glob,csv; bad=[]; [bad.append((f,r.get('symbol'),r.get('pnl'),r.get('outcome'))) for f in glob.glob('out/2025*/B/results_2025-*.csv') for r in csv.DictReader(open(f,newline='')) if r.get('outcome')=='SL' and float(r.get('pnl') or 0)>0]; print('SL_but_positive_pnl=',len(bad)); print('\n'.join(map(str,bad[:50])))"

E) Optional: list ERR outcomes (should be 0 after the rebase fix is correct)
python -c "import glob,csv; errs=[]; [errs.append((f,r.get('symbol'),r.get('outcome'),r.get('pnl'))) for f in glob.glob('out/2025*/B/results_2025-*.csv') for r in csv.DictReader(open(f,newline='')) if (r.get('outcome') or '').startswith('ERR_')]; print('ERR_outcomes=',len(errs)); print('\n'.join(map(str,errs[:50])))"

DONE WHEN
- TP_but_negative_pnl == 0
- SL_but_positive_pnl == 0
- No “impossible days” remain where Win% indicates all wins but totalPnL is negative

END COPILOT SPEC (FINAL — LOCKED)
