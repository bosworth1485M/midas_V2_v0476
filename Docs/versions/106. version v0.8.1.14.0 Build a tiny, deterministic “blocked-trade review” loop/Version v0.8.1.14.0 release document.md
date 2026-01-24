Version v0.8.1.14.0 — Blocked-Trade Diagnostic Analysis (No Code Changes)
Purpose of This Version

The purpose of v0.8.1.14.0 is to analyze the blocked-trade diagnostics introduced in v0.8.1.13.0 and determine whether the Post-Damage VWAP Reclaim Continuation Guard:

prevents losses,

blocks profitable opportunities, or

is profit-neutral.

This version is analysis-only.
No strategy logic, thresholds, configuration, or execution behavior were changed.

The goal is to produce evidence-based justification for either:

keeping the guard unchanged, or

modifying it in a future version.

Background (Context from v0.8.1.13.0)

Version v0.8.1.13.0 introduced diagnostic JSON snapshots written when the following guard blocks a trade:

Guard: Post-Damage VWAP Reclaim Continuation Guard

Condition: fewer than 2 green candles closing above VWAP in the last three completed bars (i-1, i-2, i-3) after structural damage recovery.

These JSONs capture:

symbol, date, time

continuation count

day classification

scenario

guard state flags

They are written log-once per symbol per day and are diagnostics-only.

Scope of v0.8.1.14.0

This version answers one narrow question:

When this guard blocks a trade, does that block help, hurt, or not matter for realized profit?

To answer this, we:

Re-ran controlled historical ranges

Enumerated all blocked-trade snapshots

Matched each blocked candidate to actual executed trades on the same day

Classified each block as:

Neutral

Undetermined (potentially relevant)

Missed winner (none observed)

Ranges Executed
1. Hostile regime (baseline sanity check)
python scripts\run_range_and_summarize.py --start 2025-04-01 --end 2025-04-10 --scenario B | Tee-Object out\auto\B_runlog_20250401_20250410_v0.8.1.14.0.txt


Results

[B] trades=4, wins=1, losses=3, winrate=25.00%, totalPnL=-76.87


Blocked snapshots

POST_DAMAGE_CONTINUATION_BLOCK snapshots: 0


Conclusion

The guard did not fire at all in hostile conditions.

This guard does not explain April losses.

2. Ambiguous / mixed regime
python scripts\run_range_and_summarize.py --start 2025-07-14 --end 2025-07-18 --scenario B | Tee-Object out\auto\B_runlog_20250714_20250718_v0.8.1.14.0.txt


Results

[B] trades=7, wins=3, losses=4, winrate=42.86%, totalPnL=-55.97


Blocked snapshots

POST_DAMAGE_CONTINUATION_BLOCK snapshots: 1


This range produced insufficient signal for strong conclusions and was not pursued further.

3. Snapshot-rich diagnostic regime (primary analysis)
python scripts\run_range_and_summarize.py --start 2025-11-01 --end 2025-11-30 --scenario B | Tee-Object out\auto\B_runlog_20251101_20251130_v0.8.1.14.0.txt


Results

[B] trades=17, wins=8, losses=9, winrate=47.06%, totalPnL=-90.71


Blocked snapshots discovered

Get-ChildItem .\out\202511* -Recurse -Filter "POST_DAMAGE_CONTINUATION_BLOCK_*.json"


Found 4 blocked candidates:

Date	Symbol	Time
2025-11-04	IHRT	10:31
2025-11-06	ALTO	11:10
2025-11-12	VCIG	14:00
2025-11-26	MNDR	10:21

All shared identical structural characteristics:

day_class = healthy

count = 1

recent_structural_damage = true

recovery_passed = true

Block-by-Block Outcome Analysis
1. IHRT — 2025-11-04
Get-Content .\out\20251104\B\results_2025-11-04.csv

symbol,outcome,pnl
NFE,TP,28.00


Classification: Neutral
IHRT was blocked, but another symbol traded and won.
The block did not prevent profit.

2. VCIG — 2025-11-12
Get-Content .\out\20251112\B\results_2025-11-12.csv

symbol,outcome,pnl
CMCT,TP,27.95


Classification: Neutral
VCIG was blocked, another symbol won.

3. ALTO — 2025-11-06
Get-Content .\out\20251106\B\results_2025-11-06.csv

symbol,outcome,pnl
BIYA,SL,-34.77
YGMZ,TP,27.97


Classification: Undetermined (potentially relevant)
The day lost money.
ALTO was blocked, but insufficient data exists to determine whether it would have replaced BIYA or also failed.

4. MNDR — 2025-11-26
Get-Content .\out\20251126\B\results_2025-11-26.csv

symbol,outcome,pnl
AMBR,TP,27.98
INHD,SL,-34.98


Classification: Undetermined (potentially relevant)
Same situation as ALTO: loss day, blocked symbol, no evidence of missed winner.

Summary of Findings
Classification	Count
Neutral	2
Undetermined	2
Missed winner	0

Key Observations

The guard never blocked an observed winner

Most blocks were profit-neutral

A minority coincided with losing days but lacked sufficient evidence to indicate harm

The guard fires rarely and only in healthy days with minimal continuation

Final Conclusion for v0.8.1.14.0

There is no evidence that the Post-Damage VWAP Reclaim Continuation Guard is harming profitability.

Based on November 2025 analysis:

The guard appears mostly profit-neutral

No blocked trades demonstrably reduced profit

The data does not justify relaxing or modifying this guard

Decision

Action Taken:
✔ No changes to the guard

Rationale:
Evidence does not support modification.

Status

✅ Analysis complete

✅ Evidence documented

✅ No code changes

✅ Version ready to close and tag

Transition to Next Version

The next version (v0.8.1.15.0) will not revisit blocked-trade logic.

Its focus will be:

Diagnosing why executed trades lose money, using TWCS and executed-trade artifacts.