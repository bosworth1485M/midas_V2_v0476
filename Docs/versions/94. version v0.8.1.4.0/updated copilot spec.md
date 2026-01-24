# COPILOT SPEC
# Midas_V2 v0.8.1.4.0
# Reject Weak VWAP Reclaim After Structural Damage

⚠️ OPERATING CONSTRAINTS (MANDATORY)

Copilot must NOT:
- run backtests or scripts
- execute commands
- change risk sizing, exits, or trade management
- add indicators or timeframes
- refactor architecture or reorganize code
- introduce new dependencies
- modify files other than those listed below

All changes must be:
- minimal
- reversible
- fully toggleable
- strictly limited to the defined failure class

Every added or modified line MUST include:
# v0.8.1.4.0

--------------------------------------------------
GOAL (EXACT)
--------------------------------------------------

Implement one structural guard that:

- blocks trade entries that reclaim VWAP weakly after recent structural damage
- blocks SPRU — 2025-08-08 (loser)
- does NOT block MRM — 2025-08-08 (winner)
- activates ONLY when structural damage is present
- leaves all other behavior unchanged
- does nothing when the toggle is OFF

No other behavior may change.

--------------------------------------------------
FILES ALLOWED TO CHANGE (ONLY)
--------------------------------------------------

1) src/midas_v2/engine/backtester.py
2) config/scenarios.json

No other files may be edited.

--------------------------------------------------
CONFIGURATION CHANGE
--------------------------------------------------

File: config/scenarios.json

Under Scenario B, add:

"reject_reclaim_after_damage": false

Rules:
- Default must be false
- If the key is missing, treat it as false
- No other scenario fields may be changed

--------------------------------------------------
WHERE THIS LOGIC MUST LIVE
--------------------------------------------------

In backtester.py, inside run_backtest():

- Apply the guard inside the per-symbol, per-bar loop
- The guard must run inside this existing entry block:

if (not day_gate_failed) and position is None and strat.should_enter(bars, i) and risk.allow_new_trade():

- Evaluate the guard immediately BEFORE:
  entry = bar.c

If blocked:
- do NOT set entry
- do NOT set position
- simply skip entering on this bar

--------------------------------------------------
LOGIC TO IMPLEMENT
(ONLY when reject_reclaim_after_damage == true)
--------------------------------------------------

This guard runs ONLY when an entry attempt is being evaluated.

-------------------------
STEP 1 — STRUCTURAL DAMAGE
-------------------------

Candle indexing:
- i = entry candle index
- completed candles before entry are indices < i

Lookback window:
- candles [i-5, i-1]
- if fewer than 5 candles exist → NO damage

A candle counts as STRUCTURAL DAMAGE if BOTH:
- close < open
- body_fraction ≥ 0.60

body_fraction definition (no guessing):

body = abs(b.c - b.o)
rng  = max(b.h - b.l, 1e-9)
body_fraction = body / rng

If ANY candle in the window qualifies:
recent_structural_damage = True
Else:
recent_structural_damage = False

----------------------------------------
STEP 2 — RECOVERY / VWAP ACCEPTANCE
(ONLY if recent_structural_damage == True)
----------------------------------------

Recovery window:
- candles [i-2, i-1]
- if fewer than 2 candles exist → BLOCK

VWAP COMPUTATION (must match existing day-gate logic):

Compute VWAP incrementally from bar 0:

typical = (b.h + b.l + b.c) / 3.0
running_pv += typical * b.v
running_v  += b.v
vwap_j = running_pv / running_v if running_v > 0 else None

Use VWAP aligned to each candle index.
If VWAP is None / NaN / 0 → treat as FAIL.

Recovery requirement (STRICT BY DESIGN):

BOTH candles [i-2, i-1] must satisfy:
- close > open   (green)
- close > vwap   (accepted above VWAP)

If either candle fails → BLOCK ENTRY

This strict 2-of-2 rule is INTENTIONAL for v0.8.1.4.0.
Do NOT relax it.

--------------------------------------------------
BLOCKING BEHAVIOR
--------------------------------------------------

When blocked:
- do NOT enter a trade
- do NOT mutate position state
- do NOT fall through to other logic
- skip entry on this bar and continue normally

When passed:
- entry logic proceeds unchanged

--------------------------------------------------
LOGGING (EXACT, NO EXTRA)
--------------------------------------------------

Emit logs ONLY when an entry attempt is evaluated.

Exactly two lines per evaluation:

STRUCT_DAMAGE v0.8.1.4.0: detected symbol=XYZ
STRUCT_DAMAGE v0.8.1.4.0: BLOCKED symbol=XYZ reason=weak_vwap_reclaim

OR

STRUCT_DAMAGE v0.8.1.4.0: detected symbol=XYZ
STRUCT_DAMAGE v0.8.1.4.0: PASSED symbol=XYZ reason=accepted_above_vwap

No per-bar spam.
Version tag must match exactly.

--------------------------------------------------
FORBIDDEN CHANGES (RE-STATED)
--------------------------------------------------

Copilot must NOT:
- add indicators
- alter exits or stops
- change risk management
- refactor entry flow
- modify TWCS, sizing, or broker logic
- run or suggest tests

--------------------------------------------------
MANUAL VALIDATION (USER WILL PERFORM)
--------------------------------------------------

After implementation:

1) Single-day sanity check (2025-08-08)
   - SPRU → must NOT trade
   - MRM  → must still trade

2) Only if that passes, run a small range.

--------------------------------------------------
SUCCESS CRITERIA
--------------------------------------------------

v0.8.1.4.0 is successful ONLY if:
- SPRU-style failures are blocked
- MRM-style winners remain intact
- trade count may drop, quality improves
- no unrelated behavior changes appear

END COPILOT SPEC — v0.8.1.4.0
