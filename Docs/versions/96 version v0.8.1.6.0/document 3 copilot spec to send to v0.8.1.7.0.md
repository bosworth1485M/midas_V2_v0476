Document 3 — Copilot Implementation Spec
Midas_V2 v0.8.1.7.0
Post-Entry Expansion Confirmation Gate (Minute-Level Only)

Status: FINAL DRAFT
Rule: One fix, one gate, no scope creep

1. GOAL (EXACT)

Add a post-entry expansion confirmation gate that blocks entries which fail to show immediate expansion away from VWAP after entry, using minute-level data only.

This gate targets the dominant TWCS-proven failure class:

Valid acceptance → valid entry → no expansion → stop-out

The gate must be:

OFF by default

Reversible

A/B testable

Explainable in logs and TWCS

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

config/scenarios.json

src/midas_v2/strategy.py

No other files may be modified.

4. CONFIGURATION CHANGES (config/scenarios.json)
4.1 New Scenario B parameters (ONLY)

Add the following keys under Scenario B → params:

"post_entry_expansion_gate": false,
"post_entry_expansion_minutes": 2,
"post_entry_expansion_min_bps": 10

Rules

Default state must be OFF

Do not modify other scenarios

Do not reformat JSON

Do not reorder keys

Do not touch unrelated params

5. CODE CHANGES (src/midas_v2/strategy.py)
5.1 Extend StrategyParams

Add fields to StrategyParams:

post_entry_expansion_gate: bool

post_entry_expansion_minutes: int

post_entry_expansion_min_bps: float

Ensure:

Defaults align with config

No behavior changes when gate is OFF

5.2 Add Helper (Version-Tagged)

Add a helper function, version-tagged:

def _post_entry_expansion_ok(self, symbol, entry_idx, entry_price, vwap_at_entry):
    """
    v0.8.1.7.0 — Post-entry expansion confirmation (minute bars only)
    """

Required behavior (conceptual, not optimized):

Look forward post_entry_expansion_minutes minute bars from entry_idx

If insufficient bars exist → fail closed

Compute max_high in that window

Compute expansion_bps relative to VWAP at entry:

expansion_bps = (max_high - vwap_at_entry) / vwap_at_entry * 10_000


Pass if:

expansion_bps >= post_entry_expansion_min_bps


No alternative metrics. No indicator mixing.

5.3 Integration Point (CRITICAL)

Insert the new gate late in the entry decision flow, after:

DAY_GATE

Structural Damage guard (effective flag)

VWAP Extension Gate

Existing entry conditions (MACD, green streak, etc.)

If the gate fails:

Block the entry

Do not enter the trade

Do not modify exits (since trade never exists)

5.4 Logging (MANDATORY)

Add structured WHY logs in the same style as existing guards:

CHECK

POST_EXP: CHECK symbol=... entry_time=... minutes=... min_bps=...


BLOCKED

POST_EXP: BLOCKED symbol=... reason=no_expansion observed_bps=... required_bps=...


PASSED

POST_EXP: PASSED symbol=... observed_bps=...


Rules:

Logs must be deterministic

Logs must explain why an entry was blocked

Do not alter existing log formats

6. FAILURE MODE RULES

Fail closed on:

insufficient future bars

missing data

ambiguous indexing

Do not attempt to “rescue” trades

Do not soften rules dynamically

7. TWCS COMPATIBILITY (IMPORTANT)

This gate must be:

Diagnosable via existing TWCS plots

Visually obvious when comparing:

blocked losers (no expansion)

allowed winners (immediate expansion)

No TWCS plotting changes are required in this version.

8. VALIDATION (COPILOT MUST NOT RUN)

User will validate using existing scripts:

Sanity (TWCS-anchored)

ARBB — 2025-04-15 (expect BLOCK)

LHAI — 2025-07-25 (expect BLOCK)

Known August winner (expect PASS)

Range

April / May / July → reduced drawdowns

August → minimal impact

9. SUCCESS CRITERIA

This version is successful if:

Post-entry stall losers are materially reduced

Winners remain largely unaffected

Logs + TWCS clearly explain behavior

No regressions introduced

Failure is acceptable only if hypothesis is clearly disproven.

10. VERSION TAGGING RULE

All new or modified logic must include inline comments:

# v0.8.1.7.0


for traceability.

END COPILOT SPEC — v0.8.1.7.0