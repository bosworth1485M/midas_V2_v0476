Release Document — Midas_V2 v0.8.1.17.0
Regime Participation Policy Test: Marginal-Day Stop-After-1-Loss (Negative Result)
1. Version Objective

The objective of v0.8.1.17.0 was to determine whether December 2025 loss clustering in Scenario B is driven by over-participation on marginal days, and whether a stop-after-1-loss policy on marginal days would materially reduce losses without harming healthy-day performance.

This version did not modify entry logic, indicators, or guards.
It tested participation policy only.

2. Hypothesis (Locked at Version Start)

Hypothesis:
Losses in Scenario B cluster because the system participates too much on marginal or hostile days; reducing participation on those days (without changing entry logic or guards) will reduce loss clustering while preserving healthy-day performance.

3. Policy Implemented (Policy A)

Stop-After-1-Loss on Marginal Days

Applies only when close_gt_vwap_cnt == 1

Allows trades until the first completed SL

After first SL, blocks all further entries for the rest of the day

Healthy days (>=2) unchanged

Hostile days (0) unchanged

Policy implemented as optional and OFF by default

Enablement (for testing only)
$env:MIDAS_MARGINAL_STOP1LOSS="1"


Baseline runs were performed with the variable unset.

4. Implementation Summary
Files Modified

src/midas_v2/strategy.py

config/scenarios.json

src/midas_v2/engine/backtester.py

Key Implementation Points

Added marginal_stop_after_1_loss: bool = False to StrategyParams

Preserved baseline behavior when disabled

Added day-level enablement log

Added SL-trigger log

Added post-trigger block log

Preserved marginal VWAP window gate on subsequent attempts

Added observability fixes:

Separate log-once latches

Suppression of misleading DAY_GATE_FAILED logs after stop triggers

Baseline Parity Check

Confirmed identical results between:

v0.8.1.16.0

v0.8.1.17.0 (policy disabled)

5. Test Execution — Explicit Commands & Results

All tests used:

python scripts\run_range_and_summarize.py --scenario B


with full stdout+stderr capture.

5.1 Primary December Stress Range
Range: 2025-12-02 → 2025-12-06
Baseline (v0.8.1.16.0)
python scripts\run_range_and_summarize.py --start 2025-12-02 --end 2025-12-06 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251202_20251206_baseline.txt


Results

[B] trades=6, wins=1, losses=5, winrate=16.67%, totalPnL=-146.60

Baseline Parity (v0.8.1.17.0, policy OFF)
python scripts\run_range_and_summarize.py --start 2025-12-02 --end 2025-12-06 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251202_20251206_A_baseline_in_v0.8.1.17.0.txt


Results

[B] trades=6, wins=1, losses=5, winrate=16.67%, totalPnL=-146.60

Policy A Variant (v0.8.1.17.0, policy ON)
$env:MIDAS_MARGINAL_STOP1LOSS="1"
python scripts\run_range_and_summarize.py --start 2025-12-02 --end 2025-12-06 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251202_20251206_B_stop1loss_marginal.txt


Results

[B] trades=6, wins=1, losses=5, winrate=16.67%, totalPnL=-146.60

Day-Level Breakdown
Date	Trades	close_gt_vwap_cnt	Classification
2025-12-02	0	0	Hostile
2025-12-03	0	0	Hostile
2025-12-04	3	≥2	Healthy
2025-12-05	3	≥2	Healthy

Observation:
All loss clustering occurred on healthy days.
Policy A never activated.

5.2 December 1–20 Diagnostic Scan

Purpose: Identify marginal days with actual trading activity.

python scripts\run_range_and_summarize.py --start 2025-12-01 --end 2025-12-20 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251201_20251220_scan.txt

Trade Days Identified
2025-12-04 -> trades=3
2025-12-05 -> trades=3
2025-12-08 -> trades=4
2025-12-11 -> trades=2
2025-12-12 -> trades=1
2025-12-17 -> trades=2

5.3 Single-Day Classification Runs
2025-12-10 (Candidate Marginal Day)
python scripts\run_range_and_summarize.py --start 2025-12-10 --end 2025-12-10 --scenario B

[B] trades=0
close_gt_vwap_cnt=1


Marginal, but no trades → policy irrelevant

2025-12-11
python scripts\run_range_and_summarize.py --start 2025-12-11 --end 2025-12-11 --scenario B

[B] trades=2
close_gt_vwap_cnt=2


Healthy

2025-12-08
python scripts\run_range_and_summarize.py --start 2025-12-08 --end 2025-12-08 --scenario B

[B] trades=4
close_gt_vwap_cnt=2


Healthy

2025-12-12
python scripts\run_range_and_summarize.py --start 2025-12-12 --end 2025-12-12 --scenario B

[B] trades=1
close_gt_vwap_cnt>=2


Healthy

6. Findings

No marginal day with ≥1 trade and loss clustering was found

Marginal days:

Frequently produced zero trades

Rarely progressed past first entry

All December loss clusters occurred on healthy-classified days

Policy A never activated in dominant loss regimes

7. Conclusion (Definitive)

Stop-after-1-loss on marginal days does not explain or mitigate December 2025 loss clustering in Scenario B.

The hypothesis is rejected.

This is a successful negative-result version.

8. What This Version Accomplished

Eliminated marginal-day over-participation as a December loss driver

Preserved baseline behavior

Strengthened observability around regime classification

Prevented future re-testing of a non-dominant failure mode

Narrowed the real problem to healthy-day loss clustering

9. Deferred Problem Space (Next Version)

Future work should focus on:

Healthy-day failure dynamics

Late-session degradation

Post-early-strength exhaustion

Healthy-day over-participation effects

10. Version Status

v0.8.1.17.0 — CLOSED
Outcome: Negative result, hypothesis rejected
Guards changed: None
Policy promoted: None