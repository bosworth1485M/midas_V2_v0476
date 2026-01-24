Release Specification — Midas_V2 v0.8.1.7.1
Execution Correctness Hotfix

“TP outcomes must never lose money”

1. Purpose of This Version

The purpose of v0.8.1.7.1 is to restore execution correctness and analytical trustworthiness in Midas_V2 by fixing a critical invariant violation:

Trades labeled as TP (Take Profit) were sometimes producing negative PnL.

This violates fundamental trading logic and corrupts:

win rate statistics

expectancy calculations

drawdown analysis

A/B testing results

TWCS failure analysis

This version is a pure correctness hotfix.
It intentionally does not change strategy logic, trade selection, indicators, gates, or parameters.

2. Symptoms Observed (Pre-Fix)
2.1 Impossible Trade Outcomes

Multiple historical result files contained rows such as:

Date	Symbol	Outcome	PnL
2025-04-01	ICCT	TP	-5.48
2025-08-20	NBY	TP	-4.37
2025-08-29	MOVE	TP	-105.54
2025-09-10	WLDS	TP	-102.31

A TP outcome with negative PnL is impossible by definition.

2.2 Secondary Symptom: “Impossible Days”

On some days, aggregate summaries showed:

Win% = 100%

TotalPnL < 0

This is not required for the bug to exist, but it was the most obvious signal that outcome labels and economics were inconsistent.

3. Root Cause Analysis
3.1 Confirm-Time Entry vs Signal-Time Targets

Midas_V2 supports post-entry expansion confirmation:

TP/SL were originally computed at signal time

Actual entry price was finalized later at confirm time (entry = bar.c)

TP/SL were sometimes not recomputed after the entry price changed

This created situations where:

tp < entry


Which leads to:

(pnl = tp - entry) < 0


even though the trade was labeled TP.

3.2 Missing Invariant Enforcement

There was no hard guard enforcing:

TP ⇒ pnl ≥ 0

SL ⇒ pnl ≤ 0

So incorrect outcomes silently entered result CSVs.

3.3 TWCS Metadata Mismatch

Even when outcome labels were later corrected in CSVs, TWCS snapshots could still record TP or SL, creating internal inconsistency between:

analytics CSVs

TWCS visual diagnostics

4. Fixes Implemented in v0.8.1.7.1

All changes are confined to a single file:
src/midas_v2/engine/backtester.py

No other files, configs, or strategy logic were modified.

4.1 TP/SL Rebase at Confirm-Time Entry (Primary Fix)

What changed

When a pending entry is confirmed (POST_EXP: CONFIRMED)

Immediately after:

entry = bar.c


TP/SL are recomputed using the final entry price:

new_tp, new_sl = strat.targets(entry)


Why
This guarantees:

tp > entry

sl < entry
for long trades, regardless of post-signal price movement.

Auditability
A [WHY] TP_SL_REBASE log is emitted, recording:

symbol

entry

old_tp / old_sl

new_tp / new_sl

version tag v0.8.1.7.1

This makes the fix fully observable and debuggable.

4.2 Outcome ↔ PnL Invariant Enforcement (Safety Net)

Hard invariants were added at trade close:

Condition	Action
TP with pnl < 0	Relabel outcome → ERR_TP_NEG_PNL
SL with pnl > 0	Relabel outcome → ERR_SL_POS_PNL

Important constraints

PnL is never modified

Entry / TP / SL are not rewritten

Outcome is relabeled only, with a loud [WHY] OUTCOME_PNL_MISMATCH log

This guarantees that incorrect economics can never be silently mislabeled again, even if a future bug reappears.

4.3 TWCS Outcome Consistency Fix

Previously:

CSV might say ERR_TP_NEG_PNL

TWCS snapshot still said TP

Fix

A single outcome variable is now computed

That same value is used for:

trades.append((symbol, outcome, pnl))

TWCS outcome_label

This ensures CSV analytics and TWCS visuals always agree.

4.4 Scope Cleanup (Non-Functional)

During earlier iterations, Copilot introduced:

SimpleTradeSummary

format_simple_trade_calcs(...)

These were:

not used

out-of-scope for a correctness hotfix

They were fully removed, along with unused imports, after confirming no runtime references existed.

No functional behavior was changed by this cleanup.

5. What Was Explicitly NOT Changed

This version does not change:

strategy rules

indicators

gates or regimes

entry timing

exit timing

TP/SL sizing logic

scenario parameters

CSV schema (symbol,outcome,pnl unchanged)

This isolation ensures that performance comparisons across versions remain valid.

6. Validation & Testing Performed

All testing was human-run, not automated by Copilot.

6.1 Structural Safety Checks

Python AST parse:

AST_OK


Verified exactly one _normalize_strategy_params definition

Verified removal of unused helpers

No syntax or import errors

6.2 Known-Bad Day Re-Execution

Re-ran scenario B on historically failing dates:

2025-04-01

2025-08-20

2025-08-29

2025-09-10

This regenerated all affected result CSVs under the new logic.

6.3 Global Invariant Scans (Authoritative)

TP must never be negative

TP_but_negative_pnl = 0


SL must never be positive

SL_but_positive_pnl = 0


No ERR outcomes after fix

ERR_outcomes = 0


This confirms:

the rebase fix resolved the issue at its source

the invariant guard never needed to trigger

no masking or data corruption occurred

7. Resulting Guarantees (Post-v0.8.1.7.1)

After this version:

A trade labeled TP always increases equity

A trade labeled SL always decreases equity

Win rate, expectancy, drawdown, and TWCS analysis are trustworthy again

Future violations cannot silently pass without loud diagnostics

This version restores analytical integrity, which is a prerequisite for all subsequent strategy work.

8. Version Classification

Type: Execution Correctness Hotfix

Risk Level: Low (surgical, invariant-based)

Backward Compatibility: Preserved

Performance Impact: Negligible

Required Before: Any further profitability or strategy tuning

9. Git Tag
v0.8.1.7.1


Commit message

v0.8.1.7.1: execution correctness hotfix (TP>=0, SL<=0; TWCS outcome aligned)
