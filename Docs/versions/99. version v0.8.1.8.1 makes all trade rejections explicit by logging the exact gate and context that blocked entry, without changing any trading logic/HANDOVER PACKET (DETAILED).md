HANDOVER PACKET (DETAILED)
Midas_V2 — v0.8.1.8.0 Validation & Tagging Thread
Use this at the start of the new thread to restore full context.
1) Where we are right now (state of the project)

You completed and validated v0.8.1.7.1 (Execution Correctness Hotfix).

You then proceeded with v0.8.1.8.0 (Confirm-Bar Execution Safety Guard).

Code changes for v0.8.1.8.0 have been applied to:

src/midas_v2/engine/backtester.py

The system UI has become slow due to the large thread/log volume, so continuing validation in a new thread is sensible.

This new thread is purely for:

final validation,

ensuring no over-blocking regressions,

and then tagging v0.8.1.8.0 if it passes.

2) Why v0.8.1.7.1 was needed (and what it fixed)
The discovered “correctness blocker”

We proved a systemic accounting failure:

Trades labeled TP could have negative PnL

Days could report Win%=100% while total PnL was negative

This made win-rate and A/B testing untrustworthy.

v0.8.1.7.1 core fix (locked / validated)

Two fixes were implemented and validated:

TP/SL rebase at confirm-time entry

In POST_EXP flow, the signal-time TP/SL could mismatch the confirm-time entry price.

Fix: recompute tp, sl = strat.targets(entry) when entry actually happens (confirm time), ensuring tp > entry for longs.

PnL/outcome invariants

TP must never have negative PnL.

SL must never have positive PnL.

Errors are explicit and detectable.

v0.8.1.7.1 validation result

You validated that:

TP_but_negative_pnl = 0

ERR_outcomes = 0

The system is now internally consistent (outcome labels match economics).

This restored trust in results so v0.8.1.8.0 could be evaluated.

3) The purpose of v0.8.1.8.0 (what it is and is not)
Goal (exact)

Prevent trades where the confirmation candle already violates the stop intrabar.

This is an execution-safety rule:

not signal quality,

not indicator tuning,

not profitability engineering,

simply: “don’t enter trades that are already stopped out at the moment of entry.”

Rule definition (long)

If on the confirmation candle:

confirm_bar.low <= stop_price
→ reject trade, reason confirm_bar_stop_violation

Placement (critical)

After: signal validation + post-entry expansion confirmation (POST_EXP CONFIRMED)

Before: position creation / sizing / TP/SL tracking (POST_EXP POSITION_SET)

Observability requirement (met)

Runtime visibility line at run start:

CONFIRM_BAR_GUARD v0.8.1.8.0: enabled=True

WHY log on rejection:

[WHY] v0.8.1.8.0 CONFIRM_BAR_STOP_VIOLATION ...

No JSON knob: hard-enabled, but printed.

4) A-side evidence (proved the failure class exists)

Before implementing the guard, we proved the failure class exists using TWCS + full run logs.

April 7, 2025 (Scenario B) — canonical A evidence day

JNVR

Log: POSITION_SET ... sl=29.5815 at 10:14

TWCS entry meta: confirm candle low at 10:14 = 27.69

27.69 <= 29.5815 → violation

Trade stopped out immediately (exit same minute)
→ This is exactly what v0.8.1.8.0 must block.

MESA

Log: POSITION_SET ... sl=15.5039625 at 09:42

TWCS entry meta: confirm candle low at 09:42 = 15.00

15.00 <= 15.5039 → violation

Trade stopped out immediately (exit same minute)
→ Another textbook violation.

NWTG

Confirm time 12:05, stop ~2.93475.

Raw CSV has duplicate timestamps at 12:05:

one bar low 2.9501 (no violation)

another bar low 2.78 (violation)

Because the engine merges duplicate timestamps for wick correctness, the merged low is 2.78, so the guard treats it as a true violation.

5) Implementation status of v0.8.1.8.0 (what Copilot did)

Copilot applied:

Guard runtime visibility line in run_backtest()

Guard logic inserted immediately after POST_EXP confirmed flow, before position creation.

Initially the guard used confirm_bar = bar.
We later corrected this to:

confirm_bar = pos_bar_by_ts.get(bar.ts, bar)
to align with wick-correct evaluation in the presence of duplicate timestamps.

After that correction:

guard was fully spec-aligned with wick-correct stream.

6) B-side evidence (post-implementation test results)
Single day B-test: 2025-04-07

After v0.8.1.8.0:

Guard logged ON

Guard triggered for:

JNVR @ 10:14

MESA @ 09:42

NWTG @ 12:05

Result: trades dropped to 0 for that day.

This matched the proven A evidence (the trades were invalid at execution time).

7) Multi-day April test and the new concern

You ran a cluster test:

2025-04-01 to 2025-04-10 (Scenario B)

Extracted totals showed:

Apr 1: 0 trades (guard fired for ICCT @ 13:20)

Apr 2: 0 trades

Apr 3: 2 trades (1 win, 1 loss, pnl -8.09) and guard fired for PTIX @ 15:01

Apr 4: 0 trades

Apr 7: 0 trades (JNVR/MESA/NWTG blocked)

Apr 8: 0 trades

Apr 9: 0 trades

Apr 10: 0 trades

So trade count collapsed across the cluster, and the key open question became:

Is the guard too aggressive due to duplicate timestamp merging (min low across duplicates), causing false positives and over-blocking?

This needs a time-diverse check before tagging.

8) What is required before tagging v0.8.1.8.0
Mandatory next validation: second regime cluster

Run a time-diverse cluster, e.g.:

2025-08-05 to 2025-08-09 (Scenario B)

Then evaluate:

Do trades still occur on “normal” days?

Is the guard only firing on true immediate-stop cases?

Does the system collapse to near-zero trades again?

Decision gate

If August cluster still collapses to ~0 trades, we should not tag yet.

Instead, we adjust the confirm-bar definition to avoid dup-merge over-blocking (while still blocking TWCS-proven failures).

The likely adjustment (if needed):

use the actual confirm entry bar (bar) for confirm-bar wick test,

while keeping TP/SL wick correctness fix untouched.

This maintains the “confirm candle used for entry” interpretation and reduces false positives from duplicate artifacts.

9) Snapshot timestamp confusion (resolved)

Snapshot folders showed late-2025/2026 timestamps because:

Windows folder timestamps reflect file write time (system clock in 2026),

NOT trade date/time.

Trade timing truth is stored inside:

trade_snapshot_entry_meta.json (date, entry_time)

trade_snapshot_exit_meta.json (date, exit_time)

We validated this by comparing:

file modified time vs meta trade date/time.

10) Exact next step in the new thread (do this first)

Run the August cluster (Aug 5–9, Scenario B) with log capture.

Extract:

per-day [B] -> trades=... pnl=...

all CONFIRM_BAR_STOP_VIOLATION lines

Decide:

✅ tag v0.8.1.8.0, or

🔧 adjust confirm-bar definition to reduce over-blocking, rerun both clusters, then tag.

One-sentence statement for the new thread opener

“We are validating v0.8.1.8.0 confirm-bar execution safety guard (block if confirm candle breaches stop intrabar) after restoring execution correctness in v0.8.1.7.1; April cluster showed major trade-count collapse, so we must run a time-diverse August cluster before tagging to confirm the guard isn’t over-blocking due to duplicate timestamp bar merging.”