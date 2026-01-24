Document 3 — Copilot Implementation Spec
Midas_V2 v0.8.1.6.0
DAY_GATE: Require close_gt_vwap for Day Eligibility (Scenario B)
1. GOAL (EXACT)

Strengthen DAY_GATE so that a trading day may only PASS if:

Existing DAY_GATE conditions are satisfied
AND

At least one symbol passed DAY_GATE via close_gt_vwap
(close_gt_vwap_count >= 1)

This prevents green-body-only days from being tradable.

2. SCOPE RULES (NON-NEGOTIABLE)

This version must not change:

Entry logic (green streak, MACD, RVOL, etc.)

v0.8.1.4.0 Structural Damage Guard logic

v0.8.1.5.0 auto-switch logic

VWAP Extension Gate

Risk sizing, TP, SL, or trade limits

Any thresholds or indicator calculations

Any files outside the ones listed below

One structural change only: DAY_GATE eligibility rule.

3. FILES ALLOWED TO CHANGE (ONLY)

config/scenarios.json

src/midas_v2/engine/backtester.py (logging or enforcement only)

No other files.

4. CHANGE 1 — config/scenarios.json (Scenario B ONLY)

The key already exists and is supported by the code.

Set only this:

"require_day_gate_close_gt_vwap": true


Rules:

Modify Scenario B params only

Do not reformat JSON

Do not change ordering or whitespace

Do not touch other scenarios

5. CHANGE 2 — engine/backtester.py (DAY_GATE enforcement)
5.1 Existing context (do not re-derive)

DAY_GATE already computes:

close_gt_vwap_count

green_body_count

passed_symbols

day_gate_failed

Do not change:

How bars are scanned

How rules are evaluated

How counts are computed

5.2 Required behavior change

When require_day_gate_close_gt_vwap == true:

DAY_GATE must FAIL if:

close_gt_vwap_count < 1


even if:

passed_symbols >= min_symbols


When the flag is false:

DAY_GATE behavior must remain exactly unchanged

5.3 Implementation guidance (safe pattern)

Inside the DAY_GATE decision block:

After existing rule counts are computed

Before final PASS/FAIL is logged

Add logic equivalent to:

if require_day_gate_close_gt_vwap and close_gt_vwap_count < 1:
    day_gate_failed = True
    failure_reason = "no_close_gt_vwap"


Do not change:

min_symbols

any thresholds

any rule definitions

6. LOGGING REQUIREMENTS (MINIMAL)
6.1 Add ONE config log line (version-tagged)

Near the start of DAY_GATE evaluation, log:

DAY_GATE v0.8.1.6.0: CONFIG require_close_gt_vwap=<true/false>


Rules:

Exactly one line per day

Do not change existing DAY_GATE logs

Do not alter formats of existing lines

6.2 PASS / FAIL logs

Existing PASS / FAIL logs must remain unchanged

If the day fails due to the new rule, it must surface naturally via:

DAY_GATE: FAILED ... reason=insufficient_follow_through


or equivalent existing wording
(No new failure strings required)

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

Compare vs v0.8.1.5.0.

9. SUCCESS CRITERIA

Hostile months (May / July / September):

Fewer losing days

Smaller drawdowns

August:

Profitability preserved

Logs explain behavior without ambiguity

No regression in entry logic

10. END STATE

v0.8.1.5.0 remains untouched

v0.8.1.6.0 introduces one day-quality upgrade

Behavior is reversible via config

END COPILOT SPEC — v0.8.1.6.0