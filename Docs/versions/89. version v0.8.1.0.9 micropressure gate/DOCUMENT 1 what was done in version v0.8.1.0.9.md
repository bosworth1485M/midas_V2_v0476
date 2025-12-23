DOCUMENT 1
Session Summary for Midas_V2 v0.8.1.0.9
(Use this file at the start of the next session to restore context)
Version Intent

v0.8.1.0.9 was a hypothesis-testing version whose sole purpose was to answer:

Can “intent” be encoded as a 1-second microstructure gate in fully systematic Cameron-style software, in a way that improves expectancy?

This version explicitly did not attempt:

tuning for profitability

adding unrelated filters

changing minute-level strategy logic

It was a research version, not a production one.

What Was Implemented
1️⃣ Micro Pressure Gate (Definition B)

A new experimental gate was introduced:

Name: micro_pressure_gate

Purpose: detect short-term “pressure” in 1-second data at the moment of minute-bar entry

Definition tested:
B1 – Rising Highs Count

Look back N seconds (default 20)

Count the maximum streak of consecutive higher 1-second highs

Pass if max_streak ≥ min_rising

Parameters added:
"micro_pressure_gate": false,
"micro_pressure_window_s": 20,
"micro_pressure_min_rising": 3


Gate is OFF by default.

2️⃣ Code Changes (Authoritative)

Files modified in v0.8.1.0.9:

src/midas_v2/strategy.py

Added StrategyParams fields:

micro_pressure_gate

micro_pressure_window_s

micro_pressure_min_rising

Implemented _micro_pressure_ok() helper:

robust timestamp normalization

windowed 1-second candle selection

max rising-high streak logic

fail-closed behavior on missing/ambiguous data

Integrated pressure gate as Gate 6:

after MACD gate

before plugin hooks

Added structured WHY logging:

MICRO_PRESSURE_GATE: CHECK

MICRO_PRESSURE_GATE: BLOCKED

Removed leftover TEMP BAR_TIME debug logging from v0.8.1.0.8

config/scenarios.json

Added micro pressure parameters to Scenario B

Ensured default state = OFF

What Was Tested
Test Day: 2025-08-06

Scenario: B (Gap-and-Go)
Universe: top gappers, identical across runs

Three configurations were tested:

Config	Result
Baseline (gate OFF)	4 trades, 1 win, PnL ≈ −76.94
Pressure gate ON (min_rising=3)	Winner blocked, PnL worsened
Pressure gate ON (min_rising=2)	Winner still blocked, more losers, PnL worsened
Key Observations

Known good trade (PHGE 09:58) was blocked in all pressure-gate variants

Losing trades were not reliably filtered

Many symbols produced insufficient_candles failures → structural fragility

Overall expectancy decreased, not improved

Conclusion of v0.8.1.0.9

Explicit 1-second “rising pressure” gates do not improve expectancy in this Cameron-style software stack at this stage.

This is not a failure — it is a successful rejection of a hypothesis, preventing future over-engineering.

Release State (Important)

micro_pressure_gate = false

micro_expansion_gate = false

Baseline behavior restored and verified

v0.8.1.0.9 is safe to tag