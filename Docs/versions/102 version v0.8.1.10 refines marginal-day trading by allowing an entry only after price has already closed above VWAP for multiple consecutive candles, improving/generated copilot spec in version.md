COPILOT IMPLEMENTATION SPEC (FINAL — LOCKED, FIXED)
Midas_V2 v0.8.1.10.0
Marginal-day entry requires prior closes above VWAP (2-bar VWAP acceptance pre-confirm)

GOAL (EXACT)
Refine marginal-day trading so Scenario B only enters a marginal-day trade after price has already CLOSED above VWAP for multiple consecutive completed candles, while preserving all existing correct behavior.

This version removes a specific TWCS-proven failure class (e.g., “first close above VWAP” marginal entries like GRI 2025-04-01) while preserving TWCS-proven marginal winners (e.g., JNVR 2025-04-07) and leaving hostile/healthy behavior unchanged.

------------------------------------------------------------
FILES ALLOWED TO CHANGE (ONLY)
------------------------------------------------------------
src/midas_v2/engine/backtester.py

NO other files.
NO config changes.
NO refactors.
NO new helpers.
NO changes to strategy.py, indicators, scenario JSON, runners, or TWCS.

------------------------------------------------------------
WHAT ALREADY EXISTS (DO NOT RE-IMPLEMENT)
------------------------------------------------------------
In current code (v0.8.1.9.0), these already exist and must remain unchanged:

1) Day classification via close_gt_vwap_count:
   - 0 hostile → no trades
   - 1 marginal → allow at most 1 completed trade/day
   - >=2 healthy → unchanged

2) day_trade_count:
   - increments only when a trade finalizes (TP or SL)

3) effective_day_gate_failed mechanism:
   - starts as day_gate_failed
   - on marginal day with day_trade_count < 1, override to allow the first marginal trade
   - on marginal day with day_trade_count >= 1, cap suppresses further entries

4) Existing marginal logs:
   - MARGINAL_DAY_ELIGIBLE
   - MARGINAL_DAY_TRADE_CAP_REACHED

5) Log-once infrastructure:
   - early_reject_logged is a set
   - pattern: reject_key = f"{date_str}:{sym}:REASON"
   - log once then add to early_reject_logged

6) Existing “DAY_GATE_FAILED” EARLY_REJECT log block:
   - do not alter it

------------------------------------------------------------
NEW RULE TO ADD (EXACT)
------------------------------------------------------------
Rule name (for human discussion):
“MARGINAL VWAP ACCEPTANCE (2-bar pre-confirm)”

When the new rule applies (MANDATORY)
Run this check ONLY when ALL are true:

A) require_day_follow_through == True
   (DAY_GATE feature is enabled for this scenario)

B) close_gt_vwap_count == 1
   (day is classified as marginal)

C) day_trade_count < 1
   (marginal-day trade is still available)

D) Entry is otherwise being considered at the current bar index i, meaning:
   - position is None
   - pending_entry is None
   - effective_day_gate_failed is False
   AND we are immediately before the existing combined entry condition that calls:
   strat.should_enter(bars, i)

If any of A–D are false, DO NOT run this rule.

What the rule enforces (MECHANICAL)
Before allowing entry on a marginal day (as defined above):

Let i be the index of the candidate entry candle in the minute-bar series.

1) If i < 2:
   - FAIL CLOSED (reject the entry attempt for this bar via this rule)

2) Examine the two most recent completed candles immediately before entry:
   - indices i-1 and i-2

Both candles must satisfy ALL of the following:

- green candle:
  close > open

- VWAP acceptance:
  close > vwap_at_that_bar  (for that same bar)

If either candle fails either condition → reject the entry attempt for this bar.

------------------------------------------------------------
VWAP CALCULATION (CRITICAL — MUST MATCH CURRENT CODE REALITY)
------------------------------------------------------------
Do NOT rely on bar.vwap.

Compute vwap_at_that_bar for i-1 and i-2 using the SAME incremental PV/V method used elsewhere in backtester.py.

IMPORTANT: Match field names used in this codebase:
- high: b_k.h
- low:  b_k.l
- close: b_k.c
- open:  b_k.o
- volume: b_k.v

Method:
- For each bar k, typical price: tp = (b_k.h + b_k.l + b_k.c) / 3.0
- Maintain running sums from bar 0 through bar k:
  cum_pv += tp * b_k.v
  cum_v  += b_k.v
- vwap_k = cum_pv / cum_v (only if cum_v > 0)

Fail-closed behavior:
- If cum_v <= 0 at any point such that vwap for i-2 or i-1 cannot be computed, treat VWAP as unavailable and FAIL CLOSED (reject).

Implementation constraint:
- You may compute VWAP up to i-1 inside the new rule block in a minimal way.
- NO helper functions.
- NO refactor.
- Keep it local and deterministic.

TIP (ALLOWED, MINIMAL):
Compute running PV/V once in a small loop for k in range(i):
- capture vwap at k == i-2 and k == i-1
- stop early once both are captured

------------------------------------------------------------
REJECTION BEHAVIOR (MANDATORY)
------------------------------------------------------------
When the rule rejects an entry attempt:

- Do NOT change day_trade_count
- Do NOT change effective_day_gate_failed
- Do NOT change any other guard behavior
- Do NOT create pending_entry
- Do NOT alter position
- Simply skip this bar’s entry attempt (continue)

Reject reason (EXACT STRING):
MARGINAL_VWAP_ACCEPT_FAIL

Logging (log-once, MUST MATCH EXISTING PATTERN)
- Use early_reject_logged set
- Key format MUST be:
  reject_key = f"{date_str}:{sym}:MARGINAL_VWAP_ACCEPT_FAIL"

- If reject_key not in early_reject_logged:
  - candidate_ts = bar.ts if hasattr(bar, "ts") else f"bar_{i}"
  - log a single short line (WARNING level preferred to match other EARLY_REJECT style):
    "[WHY] v0.8.1.10.0 EARLY_REJECT reason=MARGINAL_VWAP_ACCEPT_FAIL symbol={sym} ts={candidate_ts} details=i={i} prev_ok={...}"
  - Add reject_key to early_reject_logged

Do NOT print arrays. Keep it short.

Include (minimum useful details):
- which of i-1 and i-2 failed
- whether failure was “not_green” or “close_le_vwap”
- optionally include the close and computed vwap for the failing bar (one or two floats), but keep it brief.

------------------------------------------------------------
PLACEMENT (MANDATORY — USE ANCHORS)
------------------------------------------------------------
Insert the new rule check:

- inside the per-bar loop
- AFTER effective_day_gate_failed has been computed for the current bar/day
- AFTER the existing “DAY_GATE_FAILED” EARLY_REJECT block (so we only gate when entry is actually eligible)
- BEFORE the existing combined entry condition that calls strat.should_enter(bars, i)

Do NOT move or restructure existing blocks.

Implementation style:
- Use a local boolean like marginal_vwap_ok = True, and if False: early-reject + continue
  OR directly: if rule applies and fails: early-reject + continue

------------------------------------------------------------
WHAT MUST NOT CHANGE
------------------------------------------------------------
- DAY_GATE computation and counters (including close_gt_vwap_count)
- marginal-day cap logic (still max 1 completed trade/day)
- hostile day and healthy day behavior
- sizing / TP / SL / exits
- existing guards (STRUCT_DAMAGE, VWAP extension, confirm-bar guard, post-entry expansion gate, etc.)
- any behavior outside marginal days
- any behavior on bars where entry is not being considered

------------------------------------------------------------
ACCEPTANCE (FOR HUMAN REVIEW)
------------------------------------------------------------
After implementation (A/B in April 2025 using run_range_and_summarize.py + Tee-Object logs):

1) GRI-type marginal SLs where entry is the FIRST close above VWAP should be blocked
   (rule rejects because i-1 and/or i-2 were not already VWAP-accepted)

2) JNVR-type marginal winners where price has ALREADY been above VWAP for multiple completed candles should remain allowed

3) Hostile and healthy days behave exactly as before

4) Log evidence:
   At least one log line exists when the rule blocks an entry:
   reason=MARGINAL_VWAP_ACCEPT_FAIL (log-once per symbol/day)

END OF SPEC (LOCKED)
