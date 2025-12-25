DOCUMENT 1 — v0.8.1.1.0
Detailed Technical Summary & Validation Report
Use this file at the start of the next session to restore context.
1. What this feature is, and why it exists (high-level context)
The problem being addressed

Before v0.8.1.1.0, Scenario B showed a recurring structural weakness:

Even with correct momentum confirmation (MACD, green streaks, RVOL)

The strategy frequently entered too late, after price had already extended

This resulted in:

multiple stop-loss hits in clusters

poor risk-reward geometry

negative expectancy, even on days with decent win rates

In short:

The strategy could identify strength, but not whether that strength was already exhausted.

This is a location problem, not a signal problem.

The solution introduced in v0.8.1.1.0

v0.8.1.1.0 introduced a VWAP Extension Gate — a simple, interpretable location-discipline rule:

Do not enter a trade if price is already too far above VWAP at the moment of entry.

Key idea:

VWAP acts as a fair-value anchor

Momentum entries far above VWAP often have poor risk-reward

Blocking those entries avoids “FOMO” chases while still allowing:

pullbacks

reclaims

later, better-located entries

This mirrors guardrails used in many profitable Cameron-style systems.

What this version did not try to do

This version did not:

change TP/SL

add new indicators

change microstructure logic

optimize win rate directly

introduce partials or trade management

It asked one focused question:

If we add location discipline using VWAP, does expectancy improve?

2. Software changes made (authoritative)
Files modified (only two)

src/midas_v2/strategy.py

config/scenarios.json

No other scripts, runners, or data pipelines were changed.

This tight scope was intentional to ensure clean attribution.

3. Configuration changes (config/scenarios.json)
New parameters added to Scenario B
"vwap_extension_gate": <bool>,
"vwap_extension_max_pct": <float>


Initial defaults:

vwap_extension_gate = false

vwap_extension_max_pct = 1.5

This allowed:

clean A/B testing

safe baseline preservation

After validation, you chose to keep the gate ON operationally, and that decision is documented explicitly (see Section 7).

4. Strategy code changes (strategy.py)
4.1 StrategyParams additions

Two new parameters were added and wired through the existing parameter factory:

vwap_extension_gate

vwap_extension_max_pct

These are scenario-controlled, not hard-coded.

4.2 New helper: _vwap_extension_ok(...)

A new helper function was introduced to evaluate entry location:

Logic:

Uses the actual strategy entry decision price (in this codepath: bars[i].c)

Uses the existing minute-level VWAP series (_vwap_series)

Computes:

dist_pct = (entry_price - vwap) / vwap * 100


Decision rules:

PASS if dist_pct <= max_pct

PASS if dist_pct <= 0 (entry below VWAP)

BLOCK if dist_pct > max_pct

Fail-closed if VWAP missing or invalid

This ensures:

safety

deterministic behavior

no silent failures

4.3 Integration point

The VWAP extension gate was inserted:

After existing momentum/confirmation gates

Before entry acceptance / plugin hooks

Only active when vwap_extension_gate == true

This placement ensures:

it does not interfere with signal generation

it purely filters where entries are allowed

4.4 WHY logging (crucial for validation)

New structured logs were added:

VWAP_EXT: CHECK

VWAP_EXT: BLOCKED reason=overextended

VWAP_EXT: BLOCKED reason=missing_vwap

These logs were critical for:

verifying correct behavior

visually validating blocked entries via TWCS

understanding why trades were skipped or allowed

5. Copilot usage (how the feature was implemented)

Copilot was used in a controlled, spec-driven way:

Only two files were edited

Copilot verified that the actual entry decision price in this path is bar.c

No refactors were introduced

Copilot confirmed:

parameters were wired correctly

no syntax errors

no unintended file changes

This ensured the feature matched the design exactly.

6. Test methodology (how the feature was evaluated)
Test runner used

All tests were run via:

python scripts\run_range_and_summarize.py --start <DATE> --end <DATE> --scenario B


This ensured:

identical universe generation

identical data inputs

identical risk sizing

identical TP/SL

only one variable changed: VWAP gate ON vs OFF

7. Results: did the feature work?
7.1 Single-day validation — 2025-08-06

Gate OFF (baseline):

trades=4

winrate=25%

PnL = −76.94

Gate ON (1.5%):

trades=4

winrate=75%

PnL = +48.74

Why this mattered:

Known bad chase entries were blocked

Later, better-located entries were allowed

Clean winners were preserved

This was the first strong signal that the feature addressed a real structural issue.

7.2 Neutral-day check — 2025-08-07

Gate OFF: −13.82
Gate ON: −13.85

Interpretation:

The gate did not artificially improve results

It changed which entry was taken (e.g., AVAH) but not the outcome

This confirmed the gate was not overfitting or forcing wins

7.3 5-day block test — 2025-08-05 → 2025-08-09

This was the decisive validation.

Baseline (gate OFF)

trades=14

winrate=35.71%

Total PnL = −174.79

VWAP gate ON (1.5%)

trades=15

winrate=53.33%

Total PnL = −21.31

Net improvement

PnL lift: +153.48

Loss count reduced

Worst-day damage significantly reduced

Trade count stable (no starvation)

7.4 Behavioral confirmation (most important)

From the logs:

Overextended entries (AIP, MYGN, CYRX, AVAH, LZ) were blocked

Later entries closer to VWAP were often taken — and often won

No evidence of systematically blocking strong early winners

This confirmed the feature worked for the reason it was designed, not by accident.

8. Final decision for v0.8.1.1.0

Based on:

single-day tests

neutral-day checks

5-day block improvement

behavioral validation

You made the explicit decision to:

Keep the VWAP extension gate ON as part of the Scenario B baseline.

This is not a silent toggle — it is a documented baseline upgrade.

9. What this version accomplished (plain English)

Before:
Scenario B chased momentum without regard to location, leading to repeated poor entries.

After:
Scenario B now:

still trades momentum

but refuses entries that are already too far from value

This did not “optimize” the strategy — it completed it.

10. Why this version is complete

This version:

answered one clear question

made one conceptual change

validated it rigorously

did not mix in payoff or management changes

That makes v0.8.1.1.0 a clean, defensible milestone.