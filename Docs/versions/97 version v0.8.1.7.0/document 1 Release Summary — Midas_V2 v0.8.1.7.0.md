Release Summary — Midas_V2 v0.8.1.7.0
Purpose of This Version

Version v0.8.1.7.0 had two narrowly defined objectives:

Introduce and evaluate a Post-Entry Expansion Confirmation Gate

Fix a backtester execution bug that caused incorrect TP/SL outcomes

This version was not intended to solve all losing trades or materially raise profitability by itself.
It was designed to separate signal quality from execution correctness.

Both objectives were successfully achieved.

1. Post-Entry Expansion Confirmation Gate
What Was Implemented

A post-entry expansion confirmation gate was added to Scenario B:

After a valid entry signal, the trade enters a PENDING state

A short confirmation window is applied (e.g. ~1–2 minutes)

Price must demonstrate minimum post-entry expansion (bps)

Outcomes:

CONFIRMED → trade is entered

EXPIRED → trade is discarded (no position)

This gate answers a precise question:

Did price actually follow through immediately after the signal?

Findings from Testing & TWCS Analysis

Based on TWCS snapshots, logs, and replay analysis:

The gate correctly blocks:

Fake breakouts with no continuation

“Green candle but no pressure” setups

Entries that stall immediately after signal

The gate does NOT block:

Trades that initially expand but then reverse intrabar

Stop-outs caused by deep wicks on the confirmation candle

This behavior is correct and expected.

Conclusion on the Post-Entry Expansion Gate

The post-entry expansion confirmation gate is valid, useful, and should be kept.

Key conclusions:

It isolates a real failure class

It improves trade quality without over-filtering

It does not distort other strategy logic

It should remain enabled (or available) going forward

This version successfully validated the gate’s mechanical and conceptual correctness.

2. Backtester Execution Bug (TP / SL Handling)
Issue Identified

During this version, a critical execution bug was discovered:

TP / SL checks were sometimes evaluated on mutated or flattened bars

This caused:

Missed take-profits

False stop-losses

Inconsistencies between raw data and backtest results

Example: TCMD (2025-08-05) failed to register a valid TP despite price exceeding the target.

Fix Implemented

TP/SL logic now evaluates against true OHLC bars with full wicks

Timestamp-safe bar handling was added to prevent mutation or misalignment

Verified by:

TCMD correctly hitting TP

August 6 winners reappearing

No regressions on neutral days

Conclusion on the Backtester Fix

Execution correctness is restored.

This fix is infrastructure-level, not a strategy tweak.
It ensures future strategy evaluation is trustworthy.

3. New Failure Class Identified (Deferred by Design)

This version identified — but intentionally did not fix — a separate failure class:

Confirm-Bar Execution Safety Failure

Characteristics:

Entry signal is valid

Post-entry expansion occurs

But the confirming candle violates the stop intrabar

Trade is entered anyway and stopped out

Key insight:

This is not a momentum failure or a continuation failure — it is an execution-safety failure.

Why This Was Not Fixed in v0.8.1.7.0

Intentionally deferred to preserve clarity:

Mixing this rule into the post-entry gate would blur failure classes

One-change-per-version discipline was maintained

The issue is clearly defined and isolated for the next version

4. Proposal for the Next Version
Working Concept

Confirm-Bar Execution Safety Guard

Conceptual rule:

Do not enter a trade if the confirmation candle violates the stop intrabar.

Example logic:

if confirm_bar.low <= stop_price:
    reject_trade(reason="confirm_bar_stop_violation")


Properties:

Single-bar rule

No indicator changes

No interaction with post-entry expansion logic

Fully testable via TWCS snapshots

5. Will the Next Proposal Improve Profitability?
Short Answer (Direct):

Yes — this is a high-confidence profitability improvement.

Why?

Because it targets a known, repeatable losing pattern:

Trades that look valid

Show initial expansion

But are structurally unsafe at entry

These trades:

Contribute disproportionately to drawdowns

Are not filtered by momentum or expansion logic

Are identifiable visually and programmatically

This makes the rule:

Low risk

High signal-to-noise

Unlikely to remove winners

Likely to reduce losses

It improves expectancy, not just win rate.

6. Final Status of v0.8.1.7.0

You can accurately record:

v0.8.1.7.0 validates the post-entry expansion confirmation gate and fixes execution correctness.
A separate confirm-bar execution safety failure class is identified and deferred to the next version.

This is a successful, well-scoped release.