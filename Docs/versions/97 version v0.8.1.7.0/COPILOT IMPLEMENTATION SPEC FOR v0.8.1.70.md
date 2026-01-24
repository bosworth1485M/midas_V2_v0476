COPILOT IMPLEMENTATION SPEC (FINAL — LOCKED)
Midas_V2 v0.8.1.7.0
Post-Entry Expansion Confirmation Gate (Minute-Level Only)

Status: FINAL
Rule: One fix, one gate, no scope creep
Validation: TWCS-anchored + range (user-run only)

1. GOAL (EXACT)

Add a post-entry expansion confirmation gate that blocks otherwise valid entries which fail to expand immediately away from VWAP after entry, using minute-level data only.

This gate targets the dominant TWCS-proven failure class:

Valid acceptance → valid entry → no expansion → stall → stop-out

The gate must be:

OFF by default

Reversible

A/B testable

Explainable in logs and TWCS

Lookahead-based by design (cancel-if-no-immediate-expansion)

Failure means the trade is never entered (no exit logic involved).

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

Defaults must align with config

No behavior change when gate is OFF

5.2 strategy.py — Add Helper (Version-Tagged)

Add helper method:

def _post_entry_expansion_ok(self, symbol, entry_idx, vwap_at_entry):
    """
    v0.8.1.7.0 — Post-entry expansion confirmation (minute bars only)
    """

Required behavior (explicit):

Look forward post_entry_expansion_minutes minute bars

Window definition:

start = entry_idx + 1

end = entry_idx + post_entry_expansion_minutes (inclusive)

If insufficient future bars → FAIL CLOSED

Compute:

max_high over window

expansion_bps = (max_high - vwap_at_entry) / vwap_at_entry * 10_000

PASS only if:

expansion_bps >= post_entry_expansion_min_bps

No alternative metrics

No indicator mixing

Do not recompute VWAP

Use VWAP value already computed at entry_idx

5.3 backtester.py — Integration Point (CRITICAL)

The gate must be executed in backtester, not strategy, to ensure correct ordering.

Exact placement:

After:

DAY_GATE (if enabled)

Structural Damage guard (effective flag)

Before:

Entry is committed (entry = bar.c or equivalent)

Flow requirement:

IF strategy.post_entry_expansion_gate is enabled
AND helper returns FAIL
→ block entry
→ do not enter trade


No exits are modified (trade never exists)

No reordering of existing guards

6. LOGGING (MANDATORY)

Logs must match existing WHY / guard style.

CHECK
[WHY] v0.8.1.7.0 POST_EXP: CHECK symbol=... entry_time=... minutes=... min_bps=...

BLOCKED
[WHY] v0.8.1.7.0 POST_EXP: BLOCKED symbol=... reason=no_expansion observed_bps=... required_bps=...

PASSED
[WHY] v0.8.1.7.0 POST_EXP: PASSED symbol=... observed_bps=...


Rules:

Logs must be deterministic

Logs must explain why an entry was blocked

Do not alter existing log formats

7. FAILURE MODE RULES

Fail closed on:

Insufficient future bars

Missing data

Ambiguous indexing

Do not attempt to rescue trades
Do not soften rules dynamically

8. TWCS COMPATIBILITY

This gate must be:

Diagnosable via existing TWCS plots

Visually obvious when comparing:

Blocked losers → no post-entry expansion

Allowed winners → immediate expansion

No TWCS plotting changes are required.

9. VALIDATION (COPILOT MUST NOT RUN)

User will validate using existing scripts:

Sanity (TWCS-anchored)

ARBB — 2025-04-15 → expect BLOCK

LHAI — 2025-07-25 → expect BLOCK

Known August winner → expect PASS

Range

April / May / July → reduced drawdowns

August → minimal impact

10. SUCCESS CRITERIA

This version is successful if:

Post-entry stall losers are materially reduced

Winners remain largely unaffected

Logs + TWCS clearly explain behavior

No regressions introduced

Failure is acceptable only if the hypothesis is clearly disproven.

11. VERSION TAGGING RULE

All new or modified logic must include inline comments:

# v0.8.1.7.0


END COPILOT SPEC — v0.8.1.7.0