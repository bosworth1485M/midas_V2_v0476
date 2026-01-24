DOCUMENT 2 — HANDOVER SPECIFICATION
Midas_V2 v0.8.1.4.0
Version Name

Reject Weak VWAP Reclaim After Structural Damage

1. Version Identity (Unambiguous)

Version: v0.8.1.4.0

Type: Structural guard (behavioral refinement)

Scope: Single failure class

Status: Design locked, implementation pending

Dependencies: None

Infrastructure changes: Forbidden

This version introduces exactly one structural fix and nothing else.

2. Purpose of v0.8.1.4.0 (Exact)

The sole purpose of this version is:

To block trade entries that occur after recent structural price damage when the subsequent VWAP reclaim does not demonstrate real acceptance or continuation strength.

This version exists because such trades:

pass current indicator-based rules,

look valid by backtest logic,

but consistently fail in real price structure (as shown by TWCS).

3. Canonical Failure Class (Locked)
Failure Class Name

Weak VWAP Reclaim After Structural Damage

This name must be used consistently in:

documentation

commit messages

TWCS notes

later database tagging

Structural Pattern Being Fixed

A trade belongs to this failure class if and only if the following sequence occurs:

Recent structural damage

One or more strong red candles

Clear selling pressure

Occurring shortly before the entry attempt

Return to VWAP

Price touches or crosses VWAP

Existing reclaim logic is satisfied

Weak reclaim

No sustained closes above VWAP

Little or no continuation

Momentum remains fragile

Entry still occurs

Because green candles and VWAP reclaim rules pass

Despite structure being compromised

Trade fails

Typically fast stop-out or rollover

4. Canonical Reference Trade (Must Be Remembered)
SPRU — 2025-08-08

This trade is the defining example for v0.8.1.4.0.

TWCS clearly shows:

a strong red damage candle before entry,

a weak, non-accepting reclaim to VWAP,

entry triggered by rules rather than strength,

loss shortly after.

Any implementation for v0.8.1.4.0 must block this trade.

If it does not, the version is invalid.

5. Behavioral Change Introduced by This Version
Before v0.8.1.4.0

VWAP reclaim + green candles can trigger entry

Structural context is ignored

Green candles count even if they occur after damage

After v0.8.1.4.0

If recent structural damage is detected:

VWAP reclaim alone is insufficient

Entry requires clear acceptance above VWAP

Green candles occurring after damage do not imply strength

This is a contextual tightening, not a strategy change.

6. What Counts as “Structural Damage” (Intent)

Structural damage is interpreted:

Over a short lookback window

Using existing 1-minute candles

Based on body dominance, not wicks

Designed to detect real selling pressure, not chop

The goal is to identify moments where price behavior changes from:

healthy pullback → damaged structure

7. What Counts as “Recovery / Acceptance”

Recovery is not:

a single close above VWAP

a wick through VWAP

a marginal reclaim

Recovery is:

multiple consecutive closes above VWAP

green candles showing follow-through

evidence buyers regained control

This distinction is the heart of the version.

8. Explicit Non-Goals (Hard Constraints)

v0.8.1.4.0 must not:

add new indicators

add new timeframes

tune unrelated parameters

change risk sizing

refactor architecture

introduce the relational database

re-enable or expand the local website

improve performance unrelated to this fix

If a change does not serve the defined failure class, it does not belong.

9. Validation Requirements (Mandatory)
A. TWCS Validation

Before range testing:

SPRU 2025-08-08 is blocked

CYRX 2025-08-06 (winner) is not blocked

Visual confirmation is required

B. Time-Diverse Validation

After TWCS passes:

One recent cluster (Aug-2025)

One older cluster (different month/year)

Confirm:

failure class reduced

winners preserved

10. Acceptance Criteria
Accept v0.8.1.4.0 if:

The failure class is blocked in TWCS

Winners remain structurally intact

Trade count is lower but cleaner

No unrelated behavior changes appear

Reject or Revise if:

Winners are blocked due to over-tight logic

Damage detection triggers too often

Recovery requirement is too strict

11. Explicit Deferral (Locked)

The following are explicitly deferred until after v0.8.1.4.0 is validated:

identifying the next failure class

introducing the relational database

re-activating the local website

any feature expansion

12. Summary Statement (For Next Thread Header)

v0.8.1.4.0 implements a single structural guard to block weak VWAP reclaims that occur after recent price damage, based on TWCS-validated failure patterns (e.g., SPRU 2025-08-08). No new features or infrastructure changes are included.