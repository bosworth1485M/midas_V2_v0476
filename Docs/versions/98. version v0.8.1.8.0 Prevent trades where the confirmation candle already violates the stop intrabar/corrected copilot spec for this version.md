# COPILOT SPEC (FINAL — LOCKED)
# Midas_V2 v0.8.1.8.0
# Confirm-Bar Execution Safety Guard

BEGIN CONTEXT
Previous version: v0.8.1.7.0

Confirmed stable features (DO NOT CHANGE):
- Post-entry expansion confirmation gate (KEEP)
- Backtester TP/SL wick correctness fix (KEEP)

Problem This Version Solves (Exact)

Trades are sometimes entered even though the confirmation candle already violates the stop intrabar.
These trades are structurally invalid at execution time and should never be entered.

This is an execution-safety failure, not a signal or continuation failure.
END CONTEXT

BEGIN GOAL (EXACT)

Add a Confirm-Bar Execution Safety Guard that blocks trade entry if the confirmation bar breaches the stop price intrabar.

This guard applies AFTER:
- Signal validation
- Post-entry expansion confirmation

This guard applies BEFORE:
- Any position creation
- Any risk sizing
- Any TP/SL registration / tracking
END GOAL

BEGIN NON-GOALS (DO NOT DO)

Copilot must NOT:
- Modify signal generation
- Modify post-entry expansion logic
- Modify indicator thresholds
- Modify stop calculation logic
- Add new indicators
- Tune parameters
- Change trade sizing
- Touch backtester execution fixes from v0.8.1.7.0

This version introduces ONE guard only.
END NON-GOALS

BEGIN FILES ALLOWED TO CHANGE (ONLY)
- src/midas_v2/engine/backtester.py
END FILES

BEGIN EXACT RULE DEFINITION

IMPORTANT:
- Use the existing `confirm_bar` already chosen by the post-entry expansion confirmation logic.
- Do NOT re-select bars. Do NOT shift to entry bar or “next bar”. Do NOT recompute windows.
- `confirm_bar` must be the same wick-correct bar stream used for TP/SL evaluation
  (do not use any flattened or surrogate bar representation).

Long Trades (Exact)
If, on the confirmation bar:
    confirm_bar.low <= stop_price
THEN:
    REJECT TRADE
    reason = "confirm_bar_stop_violation"

Equality counts as violation — use <= exactly.

Short Trades (if shorts exist)
If, on the confirmation bar:
    confirm_bar.high >= stop_price
THEN:
    REJECT TRADE
    reason = "confirm_bar_stop_violation"

Equality counts as violation — use >= exactly.
END RULES

BEGIN IMPLEMENTATION DETAILS

1) Where to Insert the Guard (Concrete but Flexible)

Locate the code path where post-entry expansion confirmation succeeds
(i.e., the point after expansion is confirmed and a confirmation bar is already selected;
an existing log line indicating post-entry confirmation may be present, wording may vary).

Insert the guard immediately AFTER that success point.

Insert the guard immediately BEFORE the block that:
- creates the position
- performs risk sizing
- assigns TP/SL
- begins TP/SL tracking

Do NOT add or rename log anchors solely to satisfy this spec.

2) Required Data Inputs (Already Available)

Use existing variables only:
- confirm_bar
- stop_price
- direction (long/short) or side
- symbol
- confirm_bar.ts

3) Exact Guard Logic (No New Helpers)

Implement using the existing local control-flow style.
Do NOT invent new helper functions (e.g., no `reject_trade()` helpers).

The rejection must behave as “no trade happened”:
- no position object
- no sizing
- no TP/SL tracking
- no results row

Pseudo-logic:

if direction == "long" and confirm_bar.low <= stop_price:
    log WHY (required; see below)
    record reject reason "confirm_bar_stop_violation" using the existing reject/decision mechanism if one exists
    continue  # skip entry

if direction == "short" and confirm_bar.high >= stop_price:
    log WHY (required; see below)
    record reject reason "confirm_bar_stop_violation" using the existing reject/decision mechanism if one exists
    continue  # skip entry

Do NOT change CSV schemas or writer logic.

4) Required Logging

Add a single, explicit WHY log when triggered:

[WHY] v0.8.1.8.0 CONFIRM_BAR_STOP_VIOLATION
symbol=<SYMBOL>
direction=<long|short>
ts=<CONFIRM_BAR_TS>
low=<LOW> (long only)
high=<HIGH> (short only)
stop=<STOP_PRICE>

5) Runtime ON/OFF Visibility (Backtester Only)

At run start (where scenario parameters or guards are logged inside backtester.py),
print a single visibility line:

CONFIRM_BAR_GUARD v0.8.1.8.0: enabled=<True/False>

Do NOT add new config keys or modify scenario files.
If an existing enable/disable mechanism already exists in backtester.py, reuse it.
Otherwise, hard-enable the guard for this version and print enabled=True.

END IMPLEMENTATION DETAILS

BEGIN ACCEPTANCE CRITERIA

Correct only if all are true:
- Trades where the confirmation bar violates stop are rejected (<= / >= inclusive)
- Trades with clean confirmation bars are unaffected
- Post-entry expansion logic remains unchanged
- Backtester TP/SL wick logic remains unchanged
- No regression on previously passing days
- Logs clearly show rejection reason when triggered
- Reject occurs before any position creation/sizing/TP/SL tracking

END ACCEPTANCE CRITERIA

BEGIN VERSION TAGGING

All new log lines and any inline comments must include:
- v0.8.1.8.0

END VERSION TAGGING

# END COPILOT SPEC
