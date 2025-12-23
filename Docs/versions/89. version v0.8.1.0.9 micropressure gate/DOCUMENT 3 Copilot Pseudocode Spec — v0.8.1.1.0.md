Copilot Pseudocode Spec — v0.8.1.1.0
(Location Discipline: VWAP Extension Filter)
Version Goal

Introduce a VWAP over-extension filter to enforce location discipline and improve risk-reward.

Scope Rules (Strict)

Modify ONLY:

src/midas_v2/strategy.py

config/scenarios.json

Do NOT modify:

microstructure logic

entry/exit rules

risk sizing logic

Feature must be OFF by default

Scenario Parameters (config/scenarios.json)

Add to Scenario B:

"vwap_extension_gate": false,
"vwap_extension_max_pct": 1.5


(Threshold value to be confirmed via A/B testing.)

StrategyParams Wiring (strategy.py)

Add fields:

vwap_extension_gate: bool

vwap_extension_max_pct: float

Wire them from scenario params with defaults.

Gate Logic (New Helper)

Add helper method:

_vwap_extension_ok(bars, i) -> bool


Logic:

Determine entry price at index i

Compute VWAP at that moment

Compute:

dist_pct = (entry_price - vwap) / vwap * 100


If dist_pct > max_pct → BLOCK

Fail closed if VWAP missing

Integration Point

Insert after existing momentum/confirmation gates

Before execution / plugin hooks

Only active if vwap_extension_gate == True

Logging (Required)

On BLOCK:

[WHY] v0.8.1.1.0 VWAP_EXT: BLOCKED symbol=... time=... price=... vwap=... dist_pct=... max_pct=...


On CHECK:

[WHY] v0.8.1.1.0 VWAP_EXT: CHECK symbol=... time=... dist_pct=... max_pct=...

A/B Test Plan

Gate OFF (baseline)

Gate ON

Same dates, same universe

Compare:

trade count

avg loss

expectancy

Use TWCS snapshots to visually validate decisions

End of Spec