Handover — v0.8.1.32.0 → v0.8.1.33.0
Context

Project goal: Emulate successful Cameron-style projects.

Recent work focused on restoring correctness and observability after long periods of zero-trade days.

v0.8.1.31.0 fixed a hidden global kill-switch (post-damage lockout scope).

v0.8.1.32.0 added a narrow loss-control guard.

What v0.8.1.32.0 Did (Completed)

Added POST_DAMAGE_CONTINUATION_BLOCK:

Blocks post-damage VWAP reclaim entries unless real continuation is shown (≥2 of last 3 candles green and above VWAP).

Added full observability:

Telemetry counters

Day totals

REGIME_SUMMARY reporting

Trade-card visibility

Important:
This guard fired only once in Aug 05–07 testing and did not cause zero-trade days.

Validation Results (Aug 05–07, Scenario B)

Aug 05: 0 trades

Aug 06: 2 trades (1W / 1L, −5.32)

Aug 07: 0 trades

Key finding:
Zero-trade days persisted despite the new guard.

Root Cause Identified (Very Important)

Telemetry clearly shows participation suppression comes from:

Marginal VWAP gate (dominant; thousands of blocks on zero-trade days)

Post-damage entry lockout on hostile days

The new continuation guard is not a participation blocker.

Example Loss (Accepted)

MYGN SL −2.5% (2025-08-06 10:51)

Entry was below a falling VWAP with no momentum.

Classified as a normal, acceptable loss, not a bug or design failure.

Decision

Freeze v0.8.1.32.0. No further changes.

Move to participation restoration next.

Next Version Intent — v0.8.1.33.0

Single objective only:

Restore participation by relaxing the marginal VWAP gate.

Planned change:

Relax marginal VWAP requirement from 2-of-3 → 1-of-3 candles above VWAP.

Explicit constraints:

No new filters

No new guards

No refactors

No sizing changes

One change only

Validation Plan (Required)

Good regime: 2025-08-05 → 2025-08-07 (Scenario B)

Hostile regime: 2025-12-02 → 2025-12-06 (Scenario B)

Success criteria:

Fewer zero-trade days

Increased participation

Losses remain explainable and bounded

Final Note

The project is now past the “invisible groundwork” phase.
v0.8.1.33.0 is expected to produce visible behavioral change if the diagnosis is correct.