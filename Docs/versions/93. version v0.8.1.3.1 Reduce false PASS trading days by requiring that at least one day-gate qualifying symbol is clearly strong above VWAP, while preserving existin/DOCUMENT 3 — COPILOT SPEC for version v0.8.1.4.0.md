DOCUMENT 3 — COPILOT SPEC
Midas_V2 v0.8.1.4.0
Version Name

Reject Weak VWAP Reclaim After Structural Damage

⚠️ COPILOT OPERATING CONSTRAINTS (READ FIRST)

Copilot is not allowed to:

run backtests

run range runners

execute commands

change risk sizing

add indicators

refactor unrelated code

Copilot may only modify the files listed below.

All changes must be minimal, reversible, and toggleable.

All modified lines must be tagged with the version number.

🎯 GOAL (EXACT)

Implement a single structural guard that:

Blocks trade entries that reclaim VWAP weakly after recent structural damage.

This logic must:

block SPRU 2025-08-08

not block CYRX 2025-08-06

activate only when damage is present

otherwise leave behavior unchanged

📁 FILES ALLOWED TO CHANGE

Copilot may modify only the following files:

src/midas_v2/engine/backtester.py

config/scenarios.json

No other files may be edited.

⚙️ CONFIGURATION CHANGE
File: config/scenarios.json

Under Scenario B, add the following toggle:

"reject_reclaim_after_damage": false


Rules:

Default value must be false

No other scenario blocks may be modified

No existing fields may be renamed or removed

🧠 LOGIC TO IMPLEMENT
(ONLY WHEN reject_reclaim_after_damage == true)
STEP 1 — Detect Recent Structural Damage

Lookback window:

Last 5 completed 1-minute candles before the entry attempt

A candle counts as structural damage if both are true:

close < open (red candle)

body_fraction >= 0.60

If one or more such candles exist:

recent_structural_damage = True


Otherwise:

recent_structural_damage = False


📌 This logic must be local and conservative — no long lookbacks.

STEP 2 — Require Recovery / Acceptance Above VWAP

(ONLY if recent_structural_damage == True)

Inspect the last 2 completed 1-minute candles before entry.

Both candles must satisfy all of the following:

close > vwap

close > open (green candle)

If either candle fails, the entry must be blocked.

🚫 BLOCKING BEHAVIOR

When blocked:

The trade must not enter

No alternative entry logic may run

The block must be logged (see below)

When passed:

Entry logic proceeds unchanged

🧾 LOGGING (MANDATORY, CONCISE)

Add exactly these logs (no extra verbosity):

STRUCT_DAMAGE v0.8.1.4.0: detected symbol=XYZ
STRUCT_DAMAGE v0.8.1.4.0: BLOCKED symbol=XYZ reason=weak_vwap_reclaim
STRUCT_DAMAGE v0.8.1.4.0: PASSED symbol=XYZ reason=accepted_above_vwap


Logging rules:

One log per decision

No per-candle spam

Must include version number

🏷️ VERSION TAGGING (MANDATORY)

Every new or modified line must include:

# v0.8.1.4.0


This includes:

logic

conditionals

helper functions (if any)

❌ FORBIDDEN CHANGES

Copilot must not:

change existing indicators

add parameters other than the toggle

alter risk management

alter position sizing

alter trade exits

introduce new dependencies

run or suggest running tests

🧪 MANUAL VALIDATION (USER WILL PERFORM)

Copilot must not run validation.
User will manually perform:

TWCS Validation

SPRU 2025-08-08 → must be blocked

CYRX 2025-08-06 → must still pass

Time-Diverse Range Testing

Recent cluster (Aug-2025)

Older cluster (different month/year)

✅ SUCCESS CONDITION

This version is successful only if:

The targeted failure class is blocked

No unrelated winners are blocked

Behavior change is limited to the defined scope

END COPILOT SPEC — v0.8.1.4.0