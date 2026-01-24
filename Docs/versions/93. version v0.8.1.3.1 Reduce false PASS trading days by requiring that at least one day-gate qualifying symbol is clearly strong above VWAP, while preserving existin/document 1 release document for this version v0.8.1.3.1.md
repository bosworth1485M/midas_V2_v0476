DOCUMENT 1
Version Specification & Findings
Midas_V2 – VWAP Reclaim After Structural Damage (Next Version)
1. Purpose of This Version

The purpose of this version is to remove a specific, repeatedly observed losing trade pattern:

Trades that reclaim VWAP weakly after recent structural damage.

This pattern was identified through TWCS analysis, not indicators, and was observed to pass existing rules while still producing losses.

This version does not add new features.
It reinterprets existing data to block structurally weak entries.

2. Key Finding (TWCS-Derived)
Core Observation

Through TWCS snapshot analysis (notably SPRU on 2025-08-08), we observed:

A strong red displacement candle (structural damage) shortly before entry

A weak bounce back to VWAP

Entry triggered because prior green candles and VWAP reclaim technically passed

Price failed shortly after entry

Conclusion

Green candles and VWAP reclaims occurring after structural damage do not represent real strength.

This explains why certain trades pass rules yet lose.

3. Example Trade Used for Diagnosis
SPRU – 2025-08-08

TWCS entry snapshot shows:

Clear red damage candle

No sustained acceptance above VWAP

Entry occurred during a fragile reclaim

This trade is the canonical failure example for this version.

4. Hypothesis Locked for This Version

Do not enter trades that reclaim VWAP weakly after recent structural damage.

This hypothesis was agreed explicitly and is the sole design goal of the version.

5. Rule Implemented (Conceptual)
Structural Damage Definition

Look back 5 completed 1-minute candles before entry

A candle is considered damage if:

close < open (red)

body fraction ≥ 0.60

If one or more such candles exist → recent structural damage = TRUE

Recovery Requirement (Only if damage exists)

Look at the last 2 completed candles before entry

Both candles must:

close above VWAP

be green

If not satisfied → entry is blocked

6. Why This Rule Is Safe

Uses existing candle + VWAP data only

No new indicators

No parameter optimization

No new timeframes

Conservative: only activates after damage

This rule does nothing to healthy continuation trades.

7. Software Changes (This Version)
Files Modified

backtester.py

Add logic to:

detect recent structural damage

conditionally require VWAP acceptance

Add logging for:

damage detection

pass / block decision

scenarios.json

Add a single toggle under Scenario B:

reject_reclaim_after_damage: true|false

Toggle Behavior

OFF → behavior identical to prior version

ON → applies the new structural filter

8. Validation Process Used

This version follows the stored workflow rules:

TWCS visual validation

Confirm rule blocks SPRU-style losers

Confirm rule does not block CYRX-style winners

Time-diverse testing

Recent cluster (Aug-2025)

Older cluster (different month/year)

Only if both pass is the version accepted.

9. Permanent Rules Now Governing the Project (Summary)

The following rules are now stored and enforced permanently:

Trading / Structure Rules

Structure beats indicators

Green candles only count if they occur before damage

VWAP reclaim alone is insufficient after damage

TWCS is for diagnosis, not direct filtering

One structural fix per version

Validation Rules

Each version must pass time-diverse validation

TWCS must confirm the fix blocks the intended failure

Fix must not break winners

Workflow / Tooling Rules

Relational DB only after 2 validated structural fixes + stable expectancy

DB is not for indicator discovery or blind optimization

Website only after statistical validation

No infrastructure changes during a fix

Hypothesis-first analysis

These rules define the project’s path to profitability.