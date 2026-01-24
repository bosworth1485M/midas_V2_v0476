HANDOVER — v0.8.1.31.0 → v0.8.1.32.0

Context
- v0.8.1.31.0 was an ALIGNMENT version.
- Goal was participation restoration, not profitability.
- Root issue identified in v0.8.1.30.0: POST_DAMAGE_ENTRY_LOCKOUT acted as a global symbol kill-switch.

What changed in v0.8.1.31.0
- POST_DAMAGE_ENTRY_LOCKOUT narrowed to apply ONLY on hostile days (day_class == "hostile").
- Change applied in both enforcement paths (normal entry + pending-confirm).
- No other guards, thresholds, indicators, or sizing logic changed.
- One observability log added to announce hostile-only scope.

Validation performed
- Good regime (2025-08-05 → 2025-08-07, Scenario B):
  - Participation improved (2/3 days traded vs frequent zero-trade days previously).
  - PnL negative by design (out of scope).
- Hostile regime (2025-12-02 → 2025-12-06, Scenario B):
  - Loss protection preserved.
  - No catastrophic loss clusters reintroduced.

Conclusion
- v0.8.1.31.0 PASSED its alignment objective.
- Structural damage now behaves contextually (Cameron-style) instead of globally.
- Remaining losses are now visible and repeatable.

Next version intent (v0.8.1.32.0)
- Remove the dominant remaining loss class:
  post-damage VWAP reclaims that enter before continuation is proven.
- Target guard: POST_DAMAGE_CONTINUATION_BLOCK (single change).
- Maintain same two-regime A/B validation (Aug 05–07, Dec 02–06).
