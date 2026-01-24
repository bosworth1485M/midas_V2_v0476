Handover Document — Midas_V2 v0.8.1.8.0
Use this document at the start of the next version thread to restore full context.
1. Current Project State (After v0.8.1.7.0)
Version Completed

v0.8.1.7.0

Strategy Context

Active scenario: Scenario B (Gap-and-Go)

Core philosophy unchanged:

Structure > indicators

Avoid fake continuation

Preserve execution correctness

2. What v0.8.1.7.0 Accomplished (Context You Must Carry Forward)
2.1 Post-Entry Expansion Confirmation Gate — VALIDATED

Status:
✅ Keep this gate

What it does:

After a valid entry signal, requires short-window price expansion

Trades remain PENDING until expansion is confirmed

Trades with no immediate follow-through are discarded

Conclusion (Locked):

This gate blocks a real and common failure class

It improves trade quality

It does not over-filter winners

It should remain enabled or available in future versions

⚠️ Do not revisit whether this gate is useful — that question is answered.

2.2 Backtester Execution Bug — FIXED

Bug:

TP / SL checks were sometimes evaluated on flattened or mutated bars

This caused false negatives (missed TP) and false SLs

Fix Implemented:

TP / SL evaluation now uses true OHLC bars with wicks

Timestamp-safe handling prevents bar mutation issues

Verified by:

TCMD (2025-08-05) correctly hitting TP

August 6 winners restored

No regressions on neutral days

Conclusion (Locked):

Backtester execution correctness is restored.
Strategy evaluation is now trustworthy again.

3. Known Weakness That Was NOT Fixed (By Design)
Confirm-Bar Execution Safety Failure

Observed Pattern:

Entry signal valid

Post-entry expansion confirmed

But confirmation candle violates the stop intrabar

Trade is entered anyway and stops out shortly after

Key Insight:

This is not a momentum failure

This is not a continuation failure

This is an execution safety failure

This failure class was clearly identified via:

TWCS snapshots

Bar-by-bar inspection

Repeatable loss patterns

4. Purpose of v0.8.1.8.0 (Next Version)
Primary Goal (Exact)

Prevent trades where the confirmation candle already violates the stop.

This version is narrowly scoped to address one failure class only.

5. Proposed Feature for v0.8.1.8.0
Confirm-Bar Execution Safety Guard

Conceptual Rule:

If the confirmation bar trades through the stop intrabar,
do not enter the trade.


Canonical logic (long example):

if confirm_bar.low <= stop_price:
    reject_trade(reason="confirm_bar_stop_violation")

Why This Rule Is Safe

It does not alter signal generation

It does not depend on indicators

It only checks structural price safety

It removes trades that are already invalid at execution time

Why This Rule Was Deferred to v0.8.1.8.0

One structural change per version discipline

Keeps failure classes clean and diagnosable

Avoids conflating continuation quality with execution safety

6. Expected Impact of v0.8.1.8.0
What It Should Improve

Reduce avoidable stop-outs

Improve expectancy

Reduce drawdown volatility

What It Will NOT Do

It will not increase trade count

It will not create new winners

It will not mask deeper structural issues

This is a loss reducer, not a signal booster.

7. Validation Plan for v0.8.1.8.0 (Must Follow)
Step 1 — Sanity Check

Re-run known losing days from v0.8.1.7.0

Confirm:

Trades rejected due to confirm-bar stop violation

No false rejections of clean winners

Step 2 — Short Range Test

Small cluster (3–5 days)

Compare:

Feature OFF vs ON

Same dates, same symbols

Step 3 — Full Range (Only If Step 2 Passes)

Multi-week or monthly range

Expect:

Fewer losses

Equal or improved expectancy

8. What NOT to Do in v0.8.1.8.0

🚫 Do not:

Rework post-entry expansion logic

Touch indicators or MACD logic

Add new gates beyond confirm-bar safety

Tune parameters preemptively

This version must stay surgical.

9. Summary for the Next Version Thread

When starting v0.8.1.8.0, the opening statement should be:

“v0.8.1.8.0 introduces a confirm-bar execution safety guard to block trades where the confirmation candle violates the stop intrabar. This addresses a known execution-level failure class identified in v0.8.1.7.0.”