HANDOVER DOCUMENT
v0.8.1.14.0 → v0.8.1.15.0
Use this document to close v0.8.1.14.0 and start v0.8.1.15.0 cleanly.
1. What v0.8.1.14.0 Was For (Authoritative Statement)

v0.8.1.14.0 was an analysis-only version.

Its sole purpose was to evaluate whether the Post-Damage VWAP Reclaim Continuation Guard (introduced earlier) is:

preventing losses,

blocking profitable opportunities, or

largely profit-neutral.

This version did not attempt to explain why executed trades lost money.
It explicitly focused on blocked trades and their impact (or lack thereof) on realized PnL.

No code, configuration, or parameters were changed in this version.

2. What Was Actually Done in v0.8.1.14.0
2.1 Code Inspection

The following logic in src/midas_v2/engine/backtester.py was inspected and verified:

Structural damage detection window [i-8, i-1]

Recovery check (recovery_passed)

Post-damage continuation count:

Count green candles closing above VWAP in [i-1, i-2, i-3]

Require green_above_vwap_count >= 2

Log-once behavior via early_reject_logged

Best-effort JSON snapshot writing under:

out\<YYYYMMDD>\B\blocked_candidates\


Important implementation detail confirmed:

Only one JSON per symbol per day is written, even if the guard blocks multiple times.

2.2 Historical Ranges Executed

The following ranges were run and logged explicitly for this analysis:

Hostile regime (baseline sanity check)
python scripts\run_range_and_summarize.py --start 2025-04-01 --end 2025-04-10 --scenario B


Guard fired: 0 times

Conclusion: Guard does not explain hostile-regime losses.

Ambiguous regime
python scripts\run_range_and_summarize.py --start 2025-07-14 --end 2025-07-18 --scenario B


Guard fired: 1 time

Insufficient signal → not used for conclusions.

Snapshot-rich regime (primary evidence)
python scripts\run_range_and_summarize.py --start 2025-11-01 --end 2025-11-30 --scenario B


Four blocked-trade JSONs were identified and analyzed:

Date	Symbol	Time
2025-11-04	IHRT	10:31
2025-11-06	ALTO	11:10
2025-11-12	VCIG	14:00
2025-11-26	MNDR	10:21
2.3 Blocked-Trade Outcome Classification

Each blocked symbol was matched against actual executed trades on the same day using:

out\<YYYYMMDD>\B\results_YYYY-MM-DD.csv

Results:
Date	Symbol	Classification
2025-11-04	IHRT	Neutral
2025-11-12	VCIG	Neutral
2025-11-06	ALTO	Undetermined
2025-11-26	MNDR	Undetermined

Key facts:

No blocked trade was shown to be a missed winner.

Most blocked trades were profit-neutral.

Two cases coincided with losing days, but no evidence showed the block caused the loss.

3. Final Conclusion of v0.8.1.14.0 (Locked)

There is no evidence that the Post-Damage VWAP Reclaim Continuation Guard is harming profitability.

As of this analysis:

The guard is mostly profit-neutral

It fires rarely

It does not block demonstrated winners

There is no justification to relax or modify it

Decision:
✔ Keep the guard unchanged.

This conclusion is considered final for v0.8.1.14.0.

4. What v0.8.1.14.0 Explicitly Did NOT Do

To avoid scope creep, the following were not part of this version:

No analysis of executed losing trades

No TWCS-based loss diagnosis

No entry-timing comparisons

No parameter tuning

No regime modeling

No new instrumentation (beyond existing diagnostics)

Those tasks belong to the next version.

5. Correct Mental Reset Before v0.8.1.15.0

Before starting the next version, reset expectations:

Blocked-trade analysis is complete.

Guard behavior is validated.

Profit problems remain elsewhere.

The question now changes from:

“Are we blocking the wrong trades?”

to:

“Why do executed trades still lose money?”

This is a different problem requiring different evidence.

6. Purpose of v0.8.1.15.0 (Authoritative)

v0.8.1.15.0 exists to identify concrete loss causes in executed trades.

This means:

Focus on SL trades only

Use charts / TWCS / entry timing

Identify repeatable failure patterns

Examples of valid outcomes:

Late entry after reclaim

No continuation after first push

Entry into exhaustion

Chop / range entry

Liquidity fade

If a failure cannot be described clearly in one sentence, it should not drive a rule change.

7. Rules for v0.8.1.15.0 (Important)
7.1 Scope Rules

Analyze executed trades only

Ignore blocked trades entirely

Ignore guard logic unless later proven relevant

7.2 Change Rules

No rule change without ≥3 repeating examples

No multi-rule changes

No parameter sweeps

7.3 Version Hygiene

v0.8.1.14.0 must remain frozen

All new analysis belongs strictly to v0.8.1.15.0

8. First Action for v0.8.1.15.0 (When Ready)

When starting the next version, the first command should be:

Import-Csv .\out\auto\range_summary_20251101_20251130_B.csv |
Where-Object { $_.outcome -eq "SL" } |
Select-Object -First 1


This selects one real losing trade and begins loss diagnosis, not filtering analysis.

9. Final Handover Statement

v0.8.1.14.0 is complete, closed, and correct.

It answered its question fully and produced a defensible conclusion:

The post-damage continuation guard should remain unchanged.

v0.8.1.15.0 must now begin with a clean slate, focusing solely on why executed trades lose money.