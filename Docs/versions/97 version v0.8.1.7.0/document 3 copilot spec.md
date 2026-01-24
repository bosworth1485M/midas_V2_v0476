COPILOT SPEC (FINAL — LOCKED)
Midas_V2 v0.8.1.8.0
Confirm-Bar Execution Safety Guard
BEGIN CONTEXT
Version Lineage

Previous version: v0.8.1.7.0

Confirmed stable features:

Post-entry expansion confirmation gate (KEEP)

Backtester TP/SL wick correctness fix (KEEP)

Problem This Version Solves (Exact)

Trades are sometimes entered even though the confirmation candle already violates the stop intrabar.
These trades are structurally invalid at execution time and should never be entered.

This is an execution-safety failure, not a signal or continuation failure.

BEGIN GOAL (EXACT)

Add a Confirm-Bar Execution Safety Guard that blocks trade entry if the confirmation bar breaches the stop price intrabar.

This applies after:

Signal validation

Post-entry expansion confirmation

This applies before:

Position creation

Risk sizing

TP/SL tracking

BEGIN NON-GOALS (DO NOT DO)

Copilot must NOT:

Modify signal generation

Modify post-entry expansion logic

Modify indicator thresholds

Modify stop calculation logic

Add new indicators

Tune parameters

Change trade sizing

Touch backtester execution fixes from v0.8.1.7.0

This version introduces one guard only.

BEGIN EXACT RULE DEFINITION
Long Trades

If, on the confirmation bar:

confirm_bar.low <= stop_price


Then:

REJECT TRADE
reason = "confirm_bar_stop_violation"

Short Trades (for completeness, if present)
confirm_bar.high >= stop_price


Reject analogously.

BEGIN IMPLEMENTATION LOCATION
File Allowed to Change (ONLY):
src/midas_v2/engine/backtester.py


No other files may be modified.

BEGIN IMPLEMENTATION DETAILS
1. Where to Insert the Guard

Insert the guard immediately after:

Post-entry expansion confirmation

Confirmation bar selection

Insert before:

Position object creation

Risk sizing

TP/SL registration

This is typically near logic that transitions from:

POST_EXP: CONFIRMED


to:

POSITION_SET

2. Required Data Inputs (Already Available)

You must use existing variables only:

confirm_bar

stop_price

direction (long/short)

symbol

confirm_bar.ts

Do not recompute or derive new values.

3. Exact Guard Logic (Pseudo-Code)
if direction == "long":
    if confirm_bar.low <= stop_price:
        log("[WHY] v0.8.1.8.0 CONFIRM_BAR_STOP_VIOLATION",
            symbol=symbol,
            ts=confirm_bar.ts,
            low=confirm_bar.low,
            stop=stop_price)
        reject_trade()
        continue


(Short side mirrored if applicable.)

BEGIN REQUIRED LOGGING

Add a single, explicit WHY log:

[WHY] v0.8.1.8.0 CONFIRM_BAR_STOP_VIOLATION
symbol=<SYMBOL>
ts=<CONFIRM_BAR_TS>
low=<LOW>
stop=<STOP_PRICE>


Logging is mandatory.

BEGIN ACCEPTANCE CRITERIA

Copilot’s implementation is correct only if all are true:

Trades where the confirmation bar violates stop are rejected

Trades with clean confirmation bars are unaffected

Post-entry expansion logic remains unchanged

Backtester TP/SL wick logic remains unchanged

No regression on previously passing days

Logs clearly show rejection reason when triggered

BEGIN VALIDATION INSTRUCTIONS (FOR HUMAN, NOT COPILOT)

After implementation:

Re-run previously losing days from v0.8.1.7.0

Confirm rejected trades correspond to:

Stop breached on confirmation candle

Re-run known winners:

Winners must remain intact

Only after sanity confirmation:

Run a short multi-day range

BEGIN VERSION TAGGING

All new log lines and comments must include:

v0.8.1.8.0


No other version numbers allowed.

END COPILOT SPEC