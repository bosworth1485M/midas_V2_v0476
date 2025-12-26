DOCUMENT 3
Copilot Specification
Midas_V2 — v0.8.1.3.0: Day Follow-Through Gate
Use this document as the ONLY instruction set for Copilot in v0.8.1.3.0
1. Version goal (single sentence)

Add an optional day-level follow-through gate to Scenario B that disables trading on weak momentum days, in order to reduce clustered losses on bad days without changing trade-level logic.

2. Background (do not implement anything from here)

Prior versions established:

VWAP Extension Gate improves entry quality

Payoff geometry tuning (SL 2.0 vs 2.5) does not improve profitability

Losses are dominated by bad days, not bad trades

This version addresses day selection, not trade management.

3. Absolute scope rules (MUST FOLLOW)
✅ Allowed

Add new optional parameters to Scenario B

Add minimal day-level evaluation logic

Add WHY logging explaining pass/fail

❌ Not allowed

No SL / TP changes

No entry logic changes

No sizing changes

No catalysts

No refactors

No microstructure logic

No partial exits

No trailing stops

No adaptive logic

If Copilot touches anything outside this scope, it is wrong.

4. Files allowed to change
✅ Allowed files

config/scenarios.json

src/midas_v2/strategy.py (ONLY if day-level logic lives here)

OR the appropriate runner/day-context file if day-state is handled outside strategy

❌ Forbidden

Any other Python file

Any test or utility file

Any script not strictly required for day gating

5. New configuration parameters (Scenario B ONLY)

Add the following fields under Scenario B in config/scenarios.json:

"require_day_follow_through": false,
"day_follow_through_minutes": 20,
"day_follow_through_min_symbols": 2


Notes:

Default must be false

No other scenarios may be modified

No existing parameters may be changed

6. Behavioral definition (v1 – minimal and strict)

If require_day_follow_through == true, then:

Before day_follow_through_minutes after market open
→ Do not evaluate the gate
→ No trades are allowed yet (existing gate_minutes logic still applies)

At or after day_follow_through_minutes:

Evaluate the day once

Count how many symbols in the current universe show follow-through

If the count is below day_follow_through_min_symbols:

Mark the day as FAILED

Disable all Scenario B trading for the remainder of the day

If the count meets or exceeds the threshold:

Mark the day as PASSED

Allow Scenario B trading normally

This decision must be:

Binary (pass / fail)

Sticky for the day (no re-evaluation)

7. Definition of “follow-through” (choose ONE rule)

A symbol counts as showing follow-through if ANY ONE of the following is true at evaluation time:

Price is above VWAP

OR price has exceeded the opening-range high

OR the most recent candle is green with body ≥ green_body_min

Do not require all conditions.
Do not stack conditions.
This is a coarse filter by design.

8. Pseudocode (high-level, mandatory behavior)
if scenario.require_day_follow_through:

    if now < market_open + day_follow_through_minutes:
        block_trading(reason="day_gate_pending")

    else if not day_gate_evaluated:
        count = count_symbols_with_follow_through(universe)

        if count < day_follow_through_min_symbols:
            day_gate_failed = True
            log("DAY_GATE: FAILED symbols=%d" % count)
        else:
            day_gate_passed = True
            log("DAY_GATE: PASSED symbols=%d" % count)

    if day_gate_failed:
        block_trading(reason="day_gate_failed")

9. Logging requirements (MANDATORY)

Add WHY logs, once per day:

DAY_GATE: CHECK

DAY_GATE: PASSED symbols=<n>

DAY_GATE: FAILED symbols=<n> reason=insufficient_follow_through

These logs must:

Appear even when the gate is disabled

Be emitted before any trades

Be visible in standard backtest output

10. Interaction with existing logic

This gate is evaluated before any trade entries

It does not modify:

VWAP Extension Gate

MACD logic

RVOL logic

SL / TP

Sizing

Existing gate_minutes remains unchanged

This is a day-level hard stop, not a filter layered onto trades.

11. Validation plan (must be followed)

After implementation, run identical date blocks:

python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-09 --scenario B


Compare:

Gate OFF (baseline)

Gate ON

Success criteria:

Worst-day losses reduced

Average daily PnL improved

Trade count on strong days roughly unchanged

12. Version discipline

This version must introduce only the day follow-through gate

No tuning beyond defaults

No second knob added

Results must be documented before any further work

13. Inline version tagging (REQUIRED)

Any new or modified code lines must include:

# v0.8.1.3.0


This is mandatory for traceability.

14. Final Copilot instruction

Implement the minimum possible code to add a day-level follow-through gate for Scenario B, exactly as specified above, and nothing more.

End of DOCUMENT 3