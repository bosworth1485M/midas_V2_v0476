Handover Spec — v0.8.1.30.0 → v0.8.1.31.0
Context

v0.8.1.30.0 was a diagnostic alignment version. Its purpose was to test whether the ASC_GREEN guard was the primary cause of frequent zero-trade days in Scenario B.

What was changed in v0.8.1.30.0

Scenario B only: ASC_GREEN temporarily disabled via config flag.

No other guards, logic, or sizing rules were modified.

What was tested

A/B comparisons against v0.8.1.29.0 on two regimes:

Dec 02–06, 2025 (hostile regime)

Aug 05–07, 2025 (good momentum regime)

Key findings

ASC_GREEN was actively blocking candidates in v0.8.1.29.0.

Disabling ASC_GREEN removed those blocks, but:

Zero-trade days persisted in hostile regimes.

Dominant blockers were:

POST_DAMAGE_ENTRY_LOCKOUT

STRUCT_DAMAGE_FAIL

In a good regime (Aug 05–07), Scenario B did participate with ASC_GREEN disabled (2 trades, 50% WR, −5.32 PnL).

Conclusion

ASC_GREEN is not the primary participation bottleneck. Structural damage guards are the dominant cause of zero-trade behavior. The hypothesis that ASC_GREEN alone explains zero-trade days was falsified.

Status of guards after v0.8.1.30.0

ASC_GREEN: Disabled for Scenario B only (diagnostic state)

All structural damage guards remain unchanged and active.

Objective for v0.8.1.31.0

Implement the next step of the Cameron Alignment Plan:

Narrow post-damage structural lockouts so they behave like contextual Cameron-style damage rules rather than global symbol kill-switches, restoring participation on valid momentum days without re-admitting known loss patterns.

Constraints for v0.8.1.31.0

One hypothesis only.

One structural rule adjusted.

No new indicators, no refactors, no feature additions.

Participation (zero-trade reduction) is the primary success metric.

Expectancy optimization is explicitly out of scope.

Evaluation criteria

Reduction in zero-trade days in Scenario B on historically “good” regimes.

No resurgence of previously identified catastrophic loss clusters.

Clear A/B separation versus v0.8.1.30.0.

Explicit non-goals

Do not revisit ASC_GREEN yet.

Do not loosen all structure gates.

Do not add recovery logic unless explicitly justified by evidence.