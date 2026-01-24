Close-Out Specification — Midas_V2 v0.8.1.21.0
Use this file at the start of the next session to restore full context.
0) Status

v0.8.1.21.0 is COMPLETE and CLOSED.

This version introduced observability only.
No strategy, guard, sizing, or execution behavior was changed.

1) Goal (Single Purpose)

The sole goal of v0.8.1.21.0 was to add day-level telemetry so that the following question could be answered with evidence:

Should POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD logic execute on all trading days, or only on hostile days?

This version was not intended to:

improve profitability

unblock trades

modify guard logic

tune parameters

make behavioral decisions

2) Exit Condition (Definition of Done)

This version is considered complete when:

REGIME_SUMMARY prints exactly once per trading day

REGIME_SUMMARY values reconcile with:

Trade Cards

per-day results CSVs

range totals

REGIME_SUMMARY data clearly distinguishes trap regimes from trend-capable regimes

A precise, testable next hypothesis is identified

All exit conditions were met.

3) What Was Implemented
3.1 REGIME_SUMMARY (Daily Telemetry)

A REGIME_SUMMARY block was added to the backtester with the following properties:

Emitted once per trading day, after all symbols are processed

Fully reconciles with trades and PnL

Contains:

date, scenario, and day classification (healthy / marginal / hostile)

universe size

closed trades (TP / SL / win rate)

realized day PnL

aggregated block totals:

struct_damage

post_damage_weak_reclaim

vwap_ext

marginal_vwap_gate

minutes_since_damage_at_entry distribution (count, min, p50, max)

data quality totals (duplicate timestamps, position mismatches, missing 1s data)

3.2 Damage Lookback Explicitness

A constant defines the lookback used for minutes-since-damage telemetry:

REGIME_DAMAGE_LOOKBACK_BARS = 60


The REGIME_SUMMARY output prints this value explicitly so the metric is self-describing and not confused with other damage concepts in the system.

4) Precise Clarification of Current Guard Behavior

This section replaces all prior ambiguous wording.

4.1 Current behavior (mechanical description)

For every trading day (healthy, marginal, hostile):

A trade candidate is evaluated.

If the candidate reaches the post-damage reclaim logic, the
POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD code path executes.

If the guard’s internal conditions are satisfied (structural damage detected and reclaim deemed weak), the trade is blocked.

There is no regime-level condition that prevents this guard logic from executing on healthy days.

4.2 Exact implication of the above

Healthy day classification does not bypass the POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD.
When a post-damage reclaim candidate on a healthy day satisfies the guard’s internal conditions, the trade is blocked.

This statement describes what the code does, not what it should do.

5) What Is Known vs What Is Not Known
5.1 What is known (from v0.8.1.21.0)

The guard executes on healthy days.

The guard blocks some post-damage reclaim candidates on healthy days.

In hostile regimes, post-damage reclaim trades are systematically unprofitable.

In trend-capable regimes, similar post-damage reclaim patterns produce mixed outcomes.

5.2 What is NOT known

Whether the trades blocked on healthy days would have:

improved PnL

worsened PnL

had no material effect

No A/B test has yet been run where:

A = guard executes on healthy days

B = guard does not execute on healthy days

Therefore:

It is not established that the blocked healthy-day trades “should have run.”

6) Tests Run (Commands and Observed Results)
6.1 Trap / Hostile Regime — December 2025
Command
python scripts\run_range_and_summarize.py --start 2025-12-02 --end 2025-12-06 --scenario B 2>&1 | Tee-Object -FilePath out\auto\B_runlog_20251202_20251206_v0.8.1.21.0.txt

Observed Outcomes

Hostile days produced no trades.

December “healthy” days produced trades that:

occurred shortly after structural damage

resulted in net losses

Range totals:

[B] trades=6, wins=2, losses=4, winrate=33.33%, totalPnL=-83.64


Interpretation:

Post-damage reclaim behavior is consistently punished in this regime.

6.2 Trend-Capable Regime — October 2025
Command
python scripts\run_range_and_summarize.py --start 2025-10-20 --end 2025-10-31 --scenario B 2>&1 | Tee-Object -FilePath out\auto\B_runlog_20251020_20251031_v0.8.1.21.0.txt

Observed Outcomes

Similar post-damage reclaim timing appears.

Outcomes are mixed (both wins and losses).

Losses are not systematic.

Interpretation:

The same trade class behaves differently depending on regime.

7) Key Finding (Strictly Stated)

POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD logic executes on healthy days and blocks qualifying post-damage reclaim candidates.
In hostile regimes, this behavior aligns with loss prevention.
In trend-capable regimes, the effect of this blocking is unknown and requires direct testing.

No claim of correctness or incorrectness is made beyond this.

8) Decision Enabled by This Version

This version enables the following experiment, not a conclusion:

Test whether preventing POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD logic from executing on healthy days reduces losses in hostile regimes without degrading performance in trend-capable regimes.

9) What This Version Does NOT Claim

It does not claim blocked trades were winners.

It does not claim the guard is wrong.

It does not claim regime gating will increase profit.

Those claims require a behavior-change version.

10) Next Version Plan — v0.8.1.22.0
Goal (Single Experiment)

Introduce a regime-level gate such that:

Hostile day → POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD logic executes (unchanged)

Healthy day → POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD logic does not execute

No other behavior changes.

Validation

Re-run:

2025-12-02 → 2025-12-06

2025-10-20 → 2025-10-31

Compare trade count, PnL, and drawdown.

11) Artifacts

out\auto\B_runlog_20251202_20251206_v0.8.1.21.0.txt

out\auto\B_runlog_20251020_20251031_v0.8.1.21.0.txt

out\auto\range_summary_20251202_20251206_B.csv

out\auto\range_summary_20251020_20251031_B.csv

End of Close-Out Specification — v0.8.1.21.0