DOCUMENT 3 — Copilot Spec
v0.8.1.2.0
Payoff Geometry: Tighten Stop Loss Only

This spec assumes VWAP extension is already ON and is part of the baseline.

BEGIN

Copilot Pseudocode Spec — v0.8.1.2.0
Reduce Stop Loss from −2.5% to −2.0% for Scenario B
Version Goal

Improve payoff geometry by tightening the stop loss only, while keeping:

VWAP extension gate ON

Entry logic unchanged

Take-profit unchanged (+2.0%)

Add inline trace comments near modified code:

# v0.8.1.2.0

HARD SCOPE RULES (STRICT)
Allowed files

config/scenarios.json

src/midas_v2/strategy.py (only if required)

DO NOT modify

VWAP extension logic

Entry filters (MACD, green streak, RVOL, gate minutes)

Take-profit logic

Risk sizing / RiskManager

Microstructure / 1-second logic

TWCS snapshot generation

Any scripts, runners, or tests

No refactors.
No formatting changes beyond the exact edit.

1) Primary change — configuration

File: config/scenarios.json

In Scenario B only, set:

"sl_pct": 2.0


Confirm the following remain unchanged:

"tp_pct": 2.0
"vwap_extension_gate": true
"vwap_extension_max_pct": 1.5


Do not alter other scenarios.

2) Code change (ONLY if necessary)

File: src/midas_v2/strategy.py

Only edit this file if:

a hard-coded default conflicts with scenario config, or

sl_pct is not being honored consistently.

If a change is required:

Ensure sl_pct from Scenario B remains the source of truth

Do not change stop-loss formula logic

Add # v0.8.1.2.0 next to modified lines

Do not touch TP logic

3) Verification checklist (Copilot must confirm)

After edits, verify:

Trade output shows Stop loss: 2.0% in “TRADING PARAMETERS”

Take profit still shows 2.0%

VWAP logs (VWAP_EXT) still appear during runs

No other behavior changed

4) Test plan (for user)

Run:

python scripts\run_range_and_summarize.py --start 2025-08-06 --end 2025-08-06 --scenario B


Then:

python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-09 --scenario B


Compare results against v0.8.1.1.0 (VWAP ON, SL 2.5).

END