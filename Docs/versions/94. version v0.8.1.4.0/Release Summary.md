Release Summary
Midas_V2 — v0.8.1.4.0
Structural Guard: Reject Weak VWAP Reclaims After Structural Damage
1. Purpose of This Version

v0.8.1.4.0 introduces a structural damage guard designed to block a specific and repeatedly observed failure class:

Entries that occur after significant downside structural damage, where price only weakly reclaims VWAP and lacks true acceptance.

This version does not attempt to improve all trades, increase frequency, or optimize parameters.
Its purpose is narrowly defined:

Prevent false strength entries after real damage

Improve trade quality in trend-friendly regimes

Preserve explainability and reversibility

This guard was derived directly from TWCS (Trade With Candle Snapshots) analysis, not from indicator tuning.

2. Canonical Failure That Motivated the Change
SPRU — 2025-08-08 @ 11:14 (Scenario B)

TWCS analysis showed:

A large red displacement candle prior to entry (true structural damage)

Subsequent green candles that:

did not reclaim VWAP

showed no acceptance or follow-through

Entry was mechanically allowed (green streak, MACD, etc.)

Trade stopped out quickly

This trade became the canonical failure case for v0.8.1.4.0.

The key insight:

Green candles after damage are not strength unless VWAP is reclaimed with acceptance.

3. What the New Guard Does (Behavioral Definition)

When enabled, the Structural Damage / Weak VWAP Reclaim Guard:

Step 1 — Detect Recent Structural Damage

Looks back over the last 8 completed 1-minute candles

Flags damage if any candle is:

red (close < open)

with large real body (≥ 60% of candle range)

This identifies true downside displacement, not noise.

Step 2 — Require VWAP Acceptance After Damage

If damage is detected, an entry is only allowed if:

The last completed candle (i-1):

is green

closes above VWAP

The entry candle (i):

is green

closes above VWAP

This enforces acceptance, not a marginal tag.

If either condition fails, the entry is blocked.

Step 3 — Logging & Observability

Every decision is logged clearly:

STRUCT_DAMAGE v0.8.1.4.0: detected symbol=XYZ
STRUCT_DAMAGE v0.8.1.4.0: BLOCKED symbol=XYZ reason=weak_vwap_reclaim


or

STRUCT_DAMAGE v0.8.1.4.0: PASSED symbol=XYZ reason=accepted_above_vwap


This ensures the guard is:

explainable

debuggable

reversible

4. What This Guard Does Not Do

v0.8.1.4.0 does not:

ban VWAP-below trades globally

modify indicators (MACD, green streak, RVOL, etc.)

change risk sizing, stops, or targets

attempt to predict regime

apply in the absence of structural damage

It is not a general trend filter.

5. Validation Methodology (Strict and Sequential)

This version followed the full measurable profitability workflow.

5.1 Single-Day Sanity (TWCS-Anchored)

2025-08-08

SPRU 11:14 → blocked

Later SPRU re-entry → allowed, hit TP

Confirmed the guard blocks the intended failure only

5.2 Small Cluster Test

2025-08-06 → 2025-08-09

Result:

Positive PnL

Healthy win rate

No obvious suppression of all trades

This confirmed the guard behaved sensibly beyond one day.

5.3 Full August 2025 Range

2025-08-01 → 2025-08-31

Result:

+41.88 PnL

~67% win rate

Fewer low-quality entries

No reappearance of the SPRU-style failure

Conclusion:
Guard is beneficial in August-style (trend-friendly) conditions.

5.4 Out-of-Sample Regime Tests
July 2025

Trades: 37

Win rate: 29.7%

PnL: –$600.60 

range_2025-07-01_to_2025-07-31_B

September 2025

Trades: 27

Win rate: 33.3%

PnL: –$377.13 

range_2025-09-01_to_2025-09-30_B

Conclusion:
Guard is harmful when applied unconditionally in choppy / hostile regimes.

6. Final Empirical Conclusion

v0.8.1.4.0 is a regime-dependent structural guard.

✅ Helpful in clean, trending environments (August)

❌ Harmful when forced ON in choppy or mean-reverting regimes (July, September)

This is not a failure of the idea — it is a correct and valuable discovery.

The guard does exactly what it was designed to do.

7. Release Decision
v0.8.1.4.0 is frozen and complete with the following classification:

Structural Damage Guard — Effective when enabled selectively; not suitable as an always-ON baseline.

Action taken:

Code is retained

Guard remains toggleable

ON/OFF state is printed at runtime

Guard is treated as a tool, not a constant

No further tuning is performed in this version.

8. Implications for the Next Version

This release directly motivates the next hypothesis:

The problem is no longer “what to block”, but “when to block it”.

Next Version Direction (Not Implemented Here)

v0.8.1.5.0 will introduce a day/regime switch

Its sole purpose will be to decide:

Enable v0.8.1.4.0 only on days with early follow-through strength

No new indicators or thresholds are justified until that question is answered.

9. Summary in One Sentence

v0.8.1.4.0 successfully blocks weak VWAP reclaims after structural damage, improves results in trend-friendly regimes, and must be applied conditionally rather than universally.