COPILOT IMPLEMENTATION SPEC (FINAL-FINAL — LOCKED)
Midas_V2 v0.8.1.7.0
Post-Entry Expansion Confirmation Gate (Minute-Level Only, NO LOOKAHEAD)

Status: FINAL-FINAL
Rule: One fix, one gate, no scope creep
Design constraint: NO LOOKAHEAD (must be backtest-realistic + deployable live)

1. GOAL (EXACT)

Add a post-entry expansion confirmation gate that blocks otherwise valid entries which fail to show immediate expansion away from VWAP, using minute-level data only.

This gate targets the dominant TWCS-proven failure class:

Valid acceptance → valid entry signal → no expansion → stall → stop-out

Important: The implementation must be live-realistic:

It must not use future bars to decide at the signal time.

It must instead use a pending confirmation window.

The gate must be:

OFF by default

Reversible

A/B testable

Explainable in logs and TWCS

No trade management changes (no TP/SL/exits changes)

2. NON-GOALS (DO NOT DO)

Copilot must NOT:

Modify DAY_GATE logic

Modify Structural Damage / weak VWAP reclaim logic

Modify VWAP Extension Gate

Tune MACD, green streak, RVOL, or thresholds

Add new indicators or data sources

Add 1-second / microstructure logic

Change sizing, TP, SL, exits, or trade management

Combine multiple fixes

Refactor unrelated code

3. FILES ALLOWED TO CHANGE (ONLY)

ONLY the following files may be modified:

config/scenarios.json

src/midas_v2/strategy.py

src/midas_v2/engine/backtester.py

No other files may be edited.

4. CONFIGURATION CHANGES
config/scenarios.json
4.1 Scenario B — New Params (ONLY)

Add the following keys under Scenario B → params:

"post_entry_expansion_gate": false,
"post_entry_expansion_minutes": 2,
"post_entry_expansion_min_bps": 10


Rules:

Default state must be OFF

Do not modify other scenarios

Do not reformat JSON

Do not reorder keys

Do not touch unrelated params

5. CODE CHANGES
5.1 strategy.py — Extend StrategyParams

Add fields:

post_entry_expansion_gate: bool
post_entry_expansion_minutes: int
post_entry_expansion_min_bps: float


Requirements:

Defaults align with config

No behavior change when gate is OFF

5.2 strategy.py — Add Helper (Version-Tagged)

Add helper:

def _post_entry_expansion_confirmed(self, symbol, confirm_window_high, vwap_at_signal):
    """
    v0.8.1.7.0 — Post-entry expansion confirmation (minute bars only, NO LOOKAHEAD)
    """


Required behavior:

Compute:

expansion_bps = (confirm_window_high - vwap_at_signal) / vwap_at_signal * 10_000

PASS only if:

expansion_bps >= post_entry_expansion_min_bps

No alternative metrics

No indicator mixing

Do not recompute VWAP:

Use VWAP at the original signal bar (“VWAP at signal”)

Note: This helper must not scan future bars. It takes a high value that the backtester accumulates as bars arrive.

5.3 backtester.py — Integration (CRITICAL): Pending-Entry Confirmation (NO LOOKAHEAD)

Replace the lookahead “check future bars now” concept with a pending-confirm mechanism.

Correct concept

When the normal strategy entry conditions would trigger at bar index i:

Do NOT enter immediately.

Create a pending entry record that stores:

symbol

signal_idx = i

signal_time

vwap_at_signal (VWAP value at the signal bar)

expires_idx = i + post_entry_expansion_minutes

max_high_since_signal = high of bar i (or start at bar i+1; choose one and be consistent; if ambiguous → fail closed)

For each subsequent bar j as it arrives:

Update max_high_since_signal = max(max_high_since_signal, bar[j].h)

If j <= expires_idx and expansion condition becomes true:

ENTER at bar j (the first confirming bar)

Use the normal entry price convention for “enter on bar j” consistent with existing engine (e.g., entry = bar.c at j)

Clear the pending entry

If j > expires_idx and still not confirmed:

Drop/clear the pending entry

No trade is taken

Ordering constraints

Pending-entry logic must occur:

After DAY_GATE (if enabled)

After Structural Damage guard (effective flag)

After all existing entry prerequisites are satisfied (the point where you currently would set entry = bar.c)

Before a trade is created/recorded

State constraints (minimal)

Support at most one pending entry per symbol at a time (if new signal arrives while pending exists, ignore the new signal or keep the earlier pending — choose deterministic behavior and log it).

Do not introduce new complex objects or refactors.

6. LOGGING (MANDATORY)

All logs must be deterministic and explainable, consistent with current style.

Signal detected → Pending created
[WHY] v0.8.1.7.0 POST_EXP: PENDING symbol=... signal_time=... minutes=... min_bps=...

Pending check (optional but allowed if not too noisy)
[WHY] v0.8.1.7.0 POST_EXP: CHECK symbol=... t=... observed_bps=... required_bps=...

Confirmed → Entry allowed (entered on confirm bar)
[WHY] v0.8.1.7.0 POST_EXP: CONFIRMED symbol=... confirm_time=... observed_bps=... required_bps=...

Expired → Entry blocked (never entered)
[WHY] v0.8.1.7.0 POST_EXP: EXPIRED symbol=... reason=no_expansion observed_bps=... required_bps=...


Rules:

Do not alter existing log formats

Logs must clearly show whether the gate was ON/OFF

If you implement “one pending per symbol,” log when a new signal is ignored due to an existing pending.

7. FAILURE MODE RULES

Fail closed / be conservative on:

Missing data

Ambiguous indexing

Unexpected state (e.g., pending exists but symbol disappears)

Do not rescue trades. Do not soften rules dynamically.

8. TWCS COMPATIBILITY

This gate must be diagnosable via existing TWCS plots.

Expected TWCS behavior:

Former stall losers: should show “signal then no expansion within N minutes → EXPIRED”

Winners: should show “signal then expansion quickly → CONFIRMED and entered on confirm bar”

No TWCS plotting changes required.

9. VALIDATION (COPILOT MUST NOT RUN)

User will validate using existing scripts:

Sanity (TWCS-anchored)

ARBB — 2025-04-15 → expect EXPIRED (no trade)

LHAI — 2025-07-25 → expect EXPIRED (no trade)

Known August winner → expect CONFIRMED (entry occurs on confirm bar)

Range

April / May / July → reduced drawdowns

August → minimal impact (watch that delayed-entry timing doesn’t kill winners)

10. SUCCESS CRITERIA

Successful if:

Post-entry stall losers are materially reduced

Winners remain largely unaffected (allowing for small entry timing shift)

Logs + TWCS clearly explain behavior

No regressions

11. VERSION TAGGING RULE

All new or modified logic must include inline comments:

# v0.8.1.7.0


END COPILOT SPEC — v0.8.1.7.0