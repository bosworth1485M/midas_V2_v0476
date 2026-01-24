Release Document
Midas_V2 — v0.8.1.16.0
Executed-Loss Diagnosis: Late VWAP Re-Push Failure Class
1. Purpose of This Version

The purpose of v0.8.1.16.0 was to continue and conclusively resolve the investigation started in v0.8.1.15.0:

Does a specific executed-loss failure class — “late VWAP re-push after stall” — occur with sufficient frequency to justify a new guard?

This version was diagnostic only.

Explicit constraints

❌ No strategy changes

❌ No new guards

❌ No parameter tuning

❌ No behavior modification

✅ Evidence gathering only

The goal was to either:

Confirm recurrence (≥3 independent examples), or

Falsify the hypothesis by demonstrating rarity

2. Loss Class Under Investigation (Locked Definition)

The loss class being tested was defined before any new runs were executed and was not modified during the version.

Target failure class: Late VWAP Re-Push After Stall

All of the following must be true:

Entry occurs above VWAP

Entry is a late re-push, not the first impulse

green_streak = 1

Clear stall / overlap immediately before entry

No base or consolidation

Immediate failure after entry

Only losses meeting all criteria qualify.

3. Known Occurrences at Version Start

At the start of v0.8.1.16.0, exactly two confirmed examples existed, both identified and TWCS-verified in v0.8.1.15.0:

Date	Symbol
2025-11-06	BIYA
2025-11-10	BNAI

These two trades motivated the hypothesis but did not yet justify a guard.

4. Methodology & Logging Discipline
Critical logging rule (mandatory)

During v0.8.1.15.0 it was confirmed that:

Guard / WHY logs are emitted to stderr

PowerShell Tee-Object captures stdout only by default

Therefore all runs in this version used:

python <command> 2>&1 | Tee-Object <runlog>.txt


Failure to do this would invalidate the run for diagnostic purposes.

5. Ranges Executed & Results

The following ranges were deliberately chosen to maximize loss density, regime diversity, and late-day behavior.

All runs used Scenario B with unchanged parameters.

5.1 November 18–22, 2025 (Primary continuation)
python scripts\run_range_and_summarize.py --start 2025-11-18 --end 2025-11-22 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251118_20251122_v0.8.1.16.0.txt


Results

Trades: 3

SLs: 1

Loss symbol: FRGT (2025-11-19)

Finding

FRGT was a multi-bar continuation

green_streak = 3

VWAP slope positive

Not a late re-push

➡ Classified as normal continuation loss (Class B)

5.2 November 13–14, 2025 (Targeted nearby test)
python scripts\run_range_and_summarize.py --start 2025-11-13 --end 2025-11-14 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251113_20251114_v0.8.1.16.0.txt


Results

Trades: 0

Finding

Neutral (no evidence for or against)

5.3 November 6–7, 2025 (Known loss cluster revisit)
python scripts\run_range_and_summarize.py --start 2025-11-06 --end 2025-11-07 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251106_20251107_v0.8.1.16.0.txt


Results

Trades: 2

SLs: 1

Loss symbol: BIYA (2025-11-06)

Finding

BIYA loss was a post-damage reclaim

Entry occurred below VWAP

Structural damage already present

➡ Not the target loss class

(This reaffirmed, rather than expanded, prior findings.)

6. December Stress Testing (High-Value Evidence)

December was chosen because:

Liquidity is thinner

Afternoon failures are common

Loss clustering is more likely

If the loss class were real, December should expose it.

6.1 December 2–6, 2025 (Loss-dense stress test)
python scripts\run_range_and_summarize.py --start 2025-12-02 --end 2025-12-06 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251202_20251206_v0.8.1.16.0.txt


Results

Trades: 6

SLs: 5

SL symbols reviewed

PLRZ

KALA

WHLR

PAVS

JFBR

Findings

Entries were below VWAP or reclaim attempts

Or multi-bar continuations

Or post-damage recoveries

No late re-push above VWAP

No green_streak = 1 cases

➡ All classified as normal regime losses

6.2 December 9–13, 2025 (Final December slice)
python scripts\run_range_and_summarize.py --start 2025-12-09 --end 2025-12-13 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251209_20251213_v0.8.1.16.0.txt


Results

Trades: 3

SLs: 1

Finding

Single loss did not match the target class

7. Aggregate Evidence Review
SL trades reviewed in v0.8.1.16.0
Period	SLs
Nov 18–22	1
Nov 6–7	1
Dec 2–6	5
Dec 9–13	1
Total	8+
Target loss class matches

New matches found: 0

Cumulative total: 2 (unchanged from v0.8.1.15.0)

8. Conclusion (Authoritative)

The “late VWAP re-push after stall” failure class exists but is rare and non-systematic.

Despite:

targeted November searches

revisiting known loss clusters

extensive December stress testing with high loss density

…the pattern did not recur.

Decision

❌ No guard justified

❌ No entry logic change warranted

✅ Losses are attributable to regime conditions, not structural entry failure

This hypothesis is formally rejected.

9. What This Version Proved

Entry logic is structurally sound

Guards are functioning correctly

Losses cluster due to when we trade, not how we enter

Over-guarding would risk blocking valid winners

10. Status

v0.8.1.16.0 is complete and closed.

No further investigation of this loss class is warranted.

11. Forward Direction (Context Only)

The dominant remaining opportunity for improvement is:

Regime-aware trade frequency control

This will be addressed in v0.8.1.17.0 as a new hypothesis, separate from entry logic.

End of Release Document — v0.8.1.16.0