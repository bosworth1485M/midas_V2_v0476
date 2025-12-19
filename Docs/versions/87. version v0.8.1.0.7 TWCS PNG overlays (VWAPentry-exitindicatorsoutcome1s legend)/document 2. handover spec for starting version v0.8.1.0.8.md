DOCUMENT 2
Handover Specification — Midas_V2 v0.8.1.0.7 → v0.8.1.0.8
0. Executive Summary (Read This First)

v0.8.1.0.7 is complete and frozen.
It delivered visual clarity and enabled definitive failure-mode discovery.

v0.8.1.0.8 introduces the first behavior change, but in a strictly controlled, reversible, experimental form:

A single microstructure-aware entry gate, ON/OFF, applied only to Scenario B, designed to test one hypothesis.

This version is not about optimization.
It is about testing whether removing one confirmed failure mode improves expectancy.

1. State of the System at Start of v0.8.1.0.8

At the handover point, the system has:

1.1 Data & Observability (Completed)

Full Polygon 1-second OHLCV data ingested and stored

TWCS snapshots for entry and exit

Self-contained TWCS PNGs showing:

price

indicators

VWAP

microstructure

outcome

Stable day/range runners

Zero regressions from earlier versions

This observability layer is trusted and must not be altered.

1.2 Confirmed Analytical Findings (Frozen)

From v0.8.1.0.7 analysis (2025-08-06, Scenario B):

Dominant failure mode identified and confirmed:

Entries taken into non-expanding 1-second microstructure

Occurs even when:

VWAP slope is positive

MACD is strong

Green streak rules pass

Evidence:

PHGE (winner) → supportive microstructure

MYGN, AIMD, CYRX (losers) → stalled / compressed / worked tape

This finding is not speculative and not to be re-litigated in v0.8.1.0.8.

2. Purpose of v0.8.1.0.8
2.1 What This Version Is For

v0.8.1.0.8 exists to answer one question only:

Does requiring a recent 1-second expansion phase remove the dominant loss bucket in Scenario B?

This is an experiment, not a permanent rule.

2.2 What This Version Is NOT For

v0.8.1.0.8 must not:

Tune MACD

Adjust VWAP logic

Change green-streak rules

Modify risk sizing

Modify stop or target logic

Introduce multiple gates

Add optimization loops

Change TWCS visualization

Change snapshot schemas

Any of the above would contaminate the experiment.

3. Experiment Design (Frozen)
3.1 Name

Microstructure Expansion Gate — Definition A

3.2 Formal Definition (Authoritative)

For a candidate entry at time T:

Look at 1-second candles in the window:

[T − 30 seconds, T)


Compute:

prior_high = max(high) in that window

breakout_level = prior_high × (1 + 0.0010)
(i.e. +10 basis points)

Let:

last_close = close of the final 1-second candle at or before T

The gate passes iff:

There exists at least one 1-second candle in the window whose high ≥ breakout_level
AND

last_close ≥ breakout_level

If any required data is missing → gate fails.

3.3 Parameters (Frozen for v0.8.1.0.8)
Parameter	Value	Notes
Window size	30 seconds	Short-term impulse
Breakout threshold	10 bps	Above noise, below overfitting
Data source	Existing 1s candles	No new fetches
Direction	LONG only	Scenario B

These values must not be tuned in this version.

4. Scope of Application
4.1 Scenario Scope

ONLY Scenario B

No other scenarios touched

No default behavior changed

4.2 Entry Timing Scope

Gate is applied immediately before placing an entry

It does not alter signal generation

It only determines whether a valid signal is allowed to execute

5. Configuration & Reversibility
5.1 Configuration Location

File:

config/scenarios.json

5.2 New Scenario B Fields

Add the following fields under Scenario B only:

"micro_expansion_gate": false,
"micro_expansion_window_s": 30,
"micro_expansion_breakout_bps": 10


Defaults:

Gate OFF

Full backward compatibility

5.3 Reversibility Guarantee

Turning "micro_expansion_gate": false must restore identical behavior to v0.8.1.0.7

No code paths should execute when disabled

6. Code Changes — Exact Files (Explicit)

This addresses your earlier concern directly.

6.1 Primary Entry Logic File (Required)

File to modify:

src/midas_v2/strategy/strategy.py


(or the exact file where Scenario B entry decisions are made)

Reason:

This is where entry permission is determined

Gate must be applied here to preserve causality

6.2 Optional Helper Module (Only if Needed)

If a clean separation is helpful:

src/midas_v2/strategy/microstructure.py


This file may contain:

micro_expansion_ok(...)

If adding a new file feels like scope creep, the helper may live inside strategy.py.

6.3 Files Explicitly NOT Modified

twcs_plotter.py

snapshot writers

data loaders

risk manager

runners

analyzers

7. Helper Function Contract (Strict)
Function Signature
def micro_expansion_ok(
    candles_1s: list[dict],
    entry_dt: datetime,
    window_s: int,
    breakout_bps: float
) -> bool:

Behavioral Rules

Parse timestamps defensively

Filter candles: T - window_s ≤ t < T

Compute prior high

Compute breakout level

Evaluate conditions exactly as defined

If anything missing → return False

No side effects.
No logging inside helper.

8. Logging & Observability
8.1 When Gate Blocks an Entry

Emit exactly one log line per blocked entry:

[WHY] v0.8.1.0.8 MICRO_EXPANSION_GATE: BLOCKED
symbol=...
time=...
prior_high=...
breakout_level=...
last_close=...


Use n/a safely

Never crash

This enables simple grep-based counting

8.2 When Gate Passes

Do not log by default

(Optional debug logging allowed only if already supported)

9. Acceptance Criteria
9.1 Functional

Gate OFF → identical results to v0.8.1.0.7

Gate ON → fewer trades, no crashes

Logs show blocked entries

9.2 Analytical

We are looking for one or more of:

Higher win rate

Improved net PnL

Removal of the “worked tape” loss bucket

Cleaner remaining TWCS PNGs

If none observed → gate is discarded.

10. Rules for v0.8.1.0.8 Development

These are non-negotiable:

One experiment only

No tuning

No stacking filters

No silent behavior changes

No expanding scope

Everything version-tagged # v0.8.1.0.8

11. End-of-Version Expectations

At the end of v0.8.1.0.8, we should have:

A clear A/B comparison

A decision:

Promote

Refine

Discard

No ambiguity about what the gate did

Only after that decision do we consider:

parameter tweaks

additional microstructure logic

integration with sizing

12. Final Statement (Intent Lock)

v0.8.1.0.8 exists to test a single, visually-validated hypothesis under strict experimental discipline.

Nothing more.
Nothing less.