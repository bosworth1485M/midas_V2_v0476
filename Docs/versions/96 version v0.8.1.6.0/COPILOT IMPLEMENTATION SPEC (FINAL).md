COPILOT IMPLEMENTATION SPEC (FINAL — LOCKED)
Midas_V2 v0.8.1.6.0
DAY_GATE: Require close_gt_vwap for Day Eligibility (Scenario B)
1. GOAL (EXACT)

Strengthen DAY_GATE so that a trading day may only PASS if:

All existing DAY_GATE conditions are satisfied
AND

At least one symbol has close_gt_vwap == true, as already reflected by the existing counter close_gt_vwap_count >= 1

This uses only existing DAY_GATE signals and does not change how close_gt_vwap_count is computed.

This prevents green-body-only “fake strength” days from being tradable.

2. SCOPE RULES (NON-NEGOTIABLE)

This version must NOT change:

Entry logic (green streak, MACD, RVOL, reclaim logic, etc.)

v0.8.1.4.0 Structural Damage Guard logic

v0.8.1.5.0 auto-switch logic

VWAP Extension Gate

Risk sizing, TP, SL, daily limits, or position sizing

Any thresholds or indicator calculations

Any files outside the ones explicitly listed below

One structural change only:
DAY_GATE day eligibility rule.

3. FILES ALLOWED TO CHANGE (ONLY)

config/scenarios.json

src/midas_v2/engine/backtester.py
(DAY_GATE enforcement and minimal logging only)

No other files may be modified.

4. CHANGE 1 — config/scenarios.json (Scenario B ONLY)

The configuration key already exists and is supported by the code.

Set only the following:

"require_day_gate_close_gt_vwap": true

Rules

Modify Scenario B params only

Do not reformat JSON

Do not change ordering or whitespace

Do not touch any other scenarios

5. CHANGE 2 — engine/backtester.py (DAY_GATE enforcement)
5.1 Existing context (DO NOT re-derive)

DAY_GATE already computes:

close_gt_vwap_count

green_body_count

passed_symbols

day_gate_failed

Do NOT change:

How bars are scanned

How rules are evaluated

How counters are computed

How symbols qualify for DAY_GATE

5.2 Required behavior change

When:

require_day_gate_close_gt_vwap == true


DAY_GATE must FAIL if:

close_gt_vwap_count < 1


This must apply even if:

passed_symbols >= min_symbols


When the flag is false:

DAY_GATE behavior must remain bit-for-bit identical to v0.8.1.5.0

5.3 Implementation guidance (safe pattern)

Inside the existing DAY_GATE decision block:

After all existing rule counts are computed

Before the final PASS / FAIL decision is logged

Add logic equivalent to:

if require_day_gate_close_gt_vwap and close_gt_vwap_count < 1:
    day_gate_failed = True
    failure_reason = "no_close_gt_vwap"

Do NOT change:

min_symbols

Any thresholds

Any rule definitions

Any shared logic used by the auto-switch system

6. LOGGING REQUIREMENTS (MINIMAL)
6.1 Config log (EXACTLY ONE LINE)

Near the start of DAY_GATE evaluation, log once per day:

DAY_GATE v0.8.1.6.0: CONFIG require_close_gt_vwap=<true|false>

Rules

Exactly one line per day

Do not modify any existing DAY_GATE logs

Do not change formats of existing log lines

6.2 PASS / FAIL logs

Existing PASS / FAIL logs must remain unchanged

If the day fails due to this new rule, it must surface naturally via existing wording, e.g.:

DAY_GATE: FAILED ... reason=insufficient_follow_through


No new failure strings are required or allowed.

7. SAFETY CONSTRAINTS (CRITICAL)

Copilot must NOT:

Modify entry gating logic

Modify how day_gate_failed is used outside DAY_GATE

Modify auto-switch logic

Modify Structural Damage Guard logic

Add new guards

Refactor unrelated code

Introduce new configuration keys

Change log formats beyond the single config line

8. VALIDATION (USER WILL RUN — COPILOT MUST NOT)
Stage 1 — Single-day sanity

2025-08-08

Expect DAY_GATE PASS

Trades still occur

Identify a historical green-body-only day

Expect DAY_GATE FAIL

Zero trades

Stage 2 — Month ranges

Run Scenario B:

May 2025

July 2025

August 2025

September 2025

Compare results directly vs v0.8.1.5.0.

9. SUCCESS CRITERIA
Hostile months (May / July / September)

Fewer losing days

Smaller drawdowns

August

Profitability preserved

No regression in trade frequency or quality

Logs

Behavior explained without ambiguity

No unexplained DAY_GATE outcomes

10. END STATE

v0.8.1.5.0 behavior remains untouched

v0.8.1.6.0 introduces one day-quality upgrade

Behavior is fully reversible via configuration

No hidden coupling or side effects

END COPILOT SPEC — Midas_V2 v0.8.1.6.0