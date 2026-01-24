HANDOVER SPECIFICATION — v0.8.1.28.0
Title: Enforce Ascending Green Candles on Intact Structure (Scenario B)

FROM: v0.8.1.27.0  
TO: v0.8.1.28.0

────────────────────────────────────────
1) CONTEXT / WHY THIS VERSION EXISTS
────────────────────────────────────────

Version v0.8.1.27.0 successfully realigned Scenario B by converting DAY_GATE
from a hard kill-switch into a throttle. This restored participation on days
that previously produced zero trades.

However, validation of v0.8.1.27.0 exposed a **major logical correctness bug**
in the continuation logic:

- The system allowed trades when it detected “green candles”,
- but those green candles were **not ascending in the same price structure**
  as the trade entry.

This violates the core Cameron-style principle:
“Continuation must be shown by ascending green candles on intact structure.”

The issue is **not** parameter tuning and **not** sizing.
It is a **logic correctness failure**.

────────────────────────────────────────
2) CONCRETE FAILURE OBSERVED (EVIDENCE)
────────────────────────────────────────

The problem was observed clearly in the following validation window:

Primary failure window:
- **2025-11-18 → 2025-11-22**
- Scenario: **B**
- Version: **v0.8.1.27.0**

Observed outcome:
- 1 trade fired on **2025-11-20**
- Symbol: **MAGN**
- Outcome: **SL (−17.28)**

TWCS analysis showed:

- A **large red displacement candle** caused structural damage.
- Subsequent green candles occurred in a **different (higher) price zone**.
- The trade was entered in a **lower, damaged price zone**.
- There were **not ascending green candles in the entry structure**.
- The system counted green candles **by time**, not by **price continuity**.

Conclusion:
- The rule “3 green candles” was applied mechanically,
  but **incorrectly**, because it did not enforce:
  - ascending closes
  - same price zone
  - reset after structural damage

This trade should never have been allowed.

────────────────────────────────────────
3) ROOT CAUSE (CLEAR STATEMENT)
────────────────────────────────────────

Root cause:

> The continuation logic checks for green candles with sufficient body size,
> but does **not** enforce that those candles are:
> (a) ascending, and
> (b) part of the same intact price structure as the entry.

As a result, green candles from a **different price zone** or **post-damage**
can qualify an entry incorrectly.

This is a **major logic bug**, not a tuning issue.

────────────────────────────────────────
4) OBJECTIVE OF v0.8.1.28.0
────────────────────────────────────────

Correct the continuation logic so that Scenario B trades **only** when:

- There are **N ascending green candles** (default N = rise_bars = 3),
- Each candle has a real body (existing green_body_min),
- Candles are **ascending in price** (higher closes, non-decreasing lows),
- Candles occur on **intact structure**,
- Any structural damage **resets / invalidates** the green count.

This aligns Scenario B with successful Cameron-style behavior.

────────────────────────────────────────
5) SCOPE (STRICT)
────────────────────────────────────────

This version changes **ONE thing only**:

✔ Enforce *ascending green candles on intact structure*  
✔ Reset continuation after structural damage  

Explicit non-changes:
✘ No DAY_GATE changes  
✘ No MACD changes  
✘ No VWAP changes  
✘ No RVOL changes  
✘ No TP / SL changes  
✘ No sizing changes  

Scenario scope:
- **Scenario B only**
- All other scenarios remain unchanged

────────────────────────────────────────
6) DATE RANGES FOR VALIDATION
────────────────────────────────────────

Validation must be done across **multiple regimes**, not a single window.

A) Primary regression / failure reproduction
- **2025-11-18 → 2025-11-22**
- Expected result:
  - MAGN trade is **blocked**
  - No structurally similar post-damage trades allowed

B) Recent hostile / choppy regime
- **2025-12-02 → 2025-12-06**
- Purpose:
  - Confirm reduction of structurally bad entries
  - Ensure system does not degrade into random chop trades

C) Known good momentum regime
- **2025-08-05 → 2025-08-15**
- Purpose:
  - Ensure valid momentum trades are preserved
  - Ascending continuation still allowed when structure is intact

D) Older time-diverse regime
- **2025-07-14 → 2025-07-18**
- Purpose:
  - Confirm rule is robust across market regimes
  - Avoid overfitting to recent conditions

────────────────────────────────────────
7) SUCCESS CRITERIA
────────────────────────────────────────

v0.8.1.28.0 is considered successful if:

- Structurally invalid trades like MAGN are blocked
- No explosion of false negatives on clean momentum days
- Win rate improves OR loss quality improves (fewer “never should exist” losses)
- TWCS confirms blocked trades are structurally invalid
- The system continues to produce trades in good regimes

────────────────────────────────────────
8) HANDOVER NOTES / GUARDRAILS
────────────────────────────────────────

- This version addresses **logic correctness**, not performance optimization.
- If results degrade severely, STOP — do not stack more rules.
- Do not loosen thresholds to “get trades back”.
- Structure must remain the primary gate.

────────────────────────────────────────
9) VERSION SUMMARY (ONE LINE)
────────────────────────────────────────

v0.8.1.28.0 enforces ascending green candle continuation on intact structure for
Scenario B, correcting a major logic bug exposed after DAY_GATE realignment.

END OF HANDOVER SPEC
