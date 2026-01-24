HANDOVER — v0.8.1.19.0

Version closed: v0.8.1.19.0

What was added

POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD

Blocks late, weak VWAP reclaims after structural damage on healthy days.

TRADE CARD console output

Human-readable entry/exit cards (symbol, scenario, rules, risk, results).

Observability only. No trading logic changes.

What was proven (A/B + TWCS)

December trap regime benefit

2025-12-04: A −41.66 → B +21.29 (clear improvement).

Remaining December losses are a different class

2025-12-05: WHLR, PAVS, JFBR.

TWCS shows late momentum exhaustion at extended highs, not VWAP reclaims.

Regression results

November: B worse than A (measured, no new failure modes).

October: B worse than A (measured, no new failure modes).

Regression is modest and diffuse, not a structural break.

Decisions

Keep v0.8.1.19.0 (guard is valid and targeted).

Accept October/November regression for now.

Do not stack another fix in this version.

Momentum-exhaustion losses explicitly deferred.

Guard status

Guard remains ON by default.

Guard is regime-sensitive (candidate for future gating).

Documented side effect: opportunity cost in trend-friendly regimes.

Documentation updates required

PROJECT_STATUS.md: add v0.8.1.19.0 summary (guard + regression note).

ACTIVE_GUARDS_LEDGER.md: add guard entry with regime sensitivity.

Handover (this file): completed.

Explicitly out of scope

No exhaustion-at-highs guard yet.

No regime gating yet.

No further logic changes in v0.8.1.19.0.

Next version focus (v0.8.1.20.0)

Regime awareness or guard-impact telemetry.

Observability / measurement first.

One change only.