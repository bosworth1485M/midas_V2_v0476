DOCUMENT 2 — Technical Handover
v0.8.1.1.0 → v0.8.1.2.0
Use this file at the start of the next version thread to restore full context.
1. Current baseline state (this is now the truth)

As of v0.8.1.1.0, Scenario B has been intentionally upgraded.

Scenario B baseline now includes:

Momentum confirmation (unchanged)

Risk sizing (unchanged)

VWAP Extension Gate (location discipline) — ON

vwap_extension_gate = true

vwap_extension_max_pct = 1.5

This is no longer experimental.
It is considered core entry logic.

Any future results should not be compared to pre-VWAP Scenario B unless explicitly stated.

2. What v0.8.1.1.0 conclusively proved
Core finding

The system’s main weakness was entry location, not signal quality.

Adding VWAP-based location discipline:

materially reduced losses

improved win rate

reduced worst-day damage

preserved legitimate momentum winners

Quantified evidence

Across a 5-day block (2025-08-05 → 2025-08-09):

Baseline OFF: −174.79

VWAP ON: −21.31

Net improvement: +153.48

This validates VWAP extension as a structural guardrail, not a cosmetic filter.

3. What is still not fixed (and why that matters)

Even with improved entry quality, profitability remains constrained by payoff geometry:

Take-profit: +2.0%

Stop-loss: −2.5%

Break-even win rate ≈ 56%

This explains why:

Even 50–55% win rates can still lose money

Good entries still fail to compound into consistent profitability

This is not an entry problem anymore.
It is now a risk/reward math problem.

4. Goal of the next version (v0.8.1.2.0)
Single-sentence version goal

Improve payoff geometry with one minimal change, assuming VWAP-disciplined entries.

This version must answer:

Given better entry location, can improved stop placement convert that edge into profitability?

5. Scope rules for v0.8.1.2.0 (strict)
MUST change

Stop-loss percentage for Scenario B only

MUST NOT change

VWAP extension logic

Entry filters (MACD, green streak, RVOL, gate minutes)

Take-profit logic

Risk sizing logic

Microstructure / 1-second logic

TWCS / logging / snapshots

Any scripts or runners

No feature stacking.
No refactors.
No tuning spree.

6. The specific change to be tested
Proposed adjustment

Stop-loss: from −2.5% → −2.0%

Take-profit: remains +2.0%

Why this change

Lowers break-even WR from ~56% → ~50%

Aligns better with VWAP-anchored entries

Minimal, interpretable, reversible

Preserves symmetry (+2 / −2)

This is the lowest-risk payoff adjustment available.

7. Evaluation plan (carry forward exactly)

Use the same runner and dates for comparability:

Smoke test
python scripts\run_range_and_summarize.py --start 2025-08-06 --end 2025-08-06 --scenario B

Block test
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-09 --scenario B

Success criteria (any one is sufficient)

Total PnL improves

Worst-day loss decreases

Average loss per losing trade decreases
without major reduction in trade count

8. What NOT to consider yet

These are explicitly deferred to later versions:

Partial profits

Break-even stops

Trailing logic

TP changes

New filters

Those remain valid ideas — just not for v0.8.1.2.0.

9. Summary for the next thread

v0.8.1.1.0 fixed where we enter

v0.8.1.2.0 should fix how much we lose when wrong

Only one variable changes

Results stay interpretable