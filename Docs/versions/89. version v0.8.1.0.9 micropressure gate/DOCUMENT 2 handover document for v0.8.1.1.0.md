DOCUMENT 2
Technical Handover: v0.8.1.0.9 → v0.8.1.1.0
Current System State
What is solid and should not be revisited immediately:

Minute-level Cameron logic (gap, MACD, green streaks, RVOL, gate minutes)

TWCS snapshot generation and PNG diagnostics

Risk sizing and daily loss limits

Microstructure ingestion plumbing (kept for future use)

What was explicitly rejected:

Hard 1-second pressure gates as entry permission logic

Core Insight from v0.8.1.0.9

Edge does not come from confirming strength more precisely.
It comes from refusing bad entry locations.

Microstructure gates attempted to refine timing.
Losses are occurring due to location (over-extension).

Direction for Next Version
v0.8.1.1.0 Focus:

Location Discipline

Specifically:

Avoid entries that are already too far from value

Improve risk-reward geometry

Reduce late, over-extended momentum entries

What the next version MUST do:

Introduce one location-based rule

Use VWAP as the reference (single, stable anchor)

Be fully A/B testable

Integrate clean WHY logging

Use TWCS to visually confirm blocked trades

What it MUST NOT do:

Revisit microstructure / seconds logic

Add multiple new knobs

Add support & resistance yet

Tune many thresholds simultaneously

Why VWAP Extension Comes Next

In profitable Cameron-style software projects:

VWAP distance filters were one of the few permanent guardrails

They removed late FOMO entries

They improved average loss and expectancy

They reduced need for additional confirmation logic

Success Criteria for v0.8.1.1.0

A VWAP extension filter should:

Block trades that visually look “too high” in TWCS

Preserve early clean winners

Improve at least one of:

average loss

expectancy

profit factor

If it fails:

Check correctness

Adjust threshold modestly

Scope by scenario if needed

Reject cleanly if still harmful