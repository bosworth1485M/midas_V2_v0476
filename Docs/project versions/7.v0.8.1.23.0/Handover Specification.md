Handover Specification
Transition from v0.8.1.23.0 → v0.8.1.24.0
Use this document at the start of the next version thread to restore full context.
1. Context Summary (What Was Just Completed)
Version Closed

v0.8.1.23.0 — Strict post-damage entry lockout

Purpose of v0.8.1.23.0

To test a structure-first safety rule:

Once structural damage occurs for a symbol intraday, permanently block all subsequent entries for that symbol that day, regardless of day regime.

Result

v0.8.1.23.0 was successfully validated as a loss-subtraction safety layer.

2. Structural Findings from v0.8.1.23.0
Key Finding (Proven)

Post-damage entries are a dominant loss class in the tested periods. Removing them:

Eliminated same-bar and near-immediate stop-outs

Removed catastrophic intraday loss clusters

Did so deterministically and reproducibly

Trade-off (Expected and Accepted)

Many historical “winners” were also blocked

This confirmed that some winners occurred despite structural damage, not because structure was healthy

This trade-off was intentional and acceptable for a safety-floor version.

3. Ranges and Tests Already Run (Ground Truth)

All tests below were run with identical universes, identical parameters, and strict A/B discipline.

3.1 Single-Day Sanity Tests
Date	Version	Result	Notes
2025-10-23	v0.8.1.22.0	1 trade, TP (SLMT)	Post-damage winner
2025-10-23	v0.8.1.23.0	0 trades	SLMT correctly blocked
2025-10-27	v0.8.1.22.0	2 trades, both SL (BKYI)	Canonical failure
2025-10-27	v0.8.1.23.0	0 trades	BKYI eliminated
2025-12-05	v0.8.1.22.0	3 trades, all SL	Loss-heavy healthy day
2025-12-05	v0.8.1.23.0	0 trades	All losses eliminated

These three days formed the sanity validation cluster (recent + different month).

3.2 Contiguous Range Test (Known Regime)
Range	Version	Trades	PnL
2025-10-20 → 2025-10-31	v0.8.1.22.0	7 trades	-56.18
2025-10-20 → 2025-10-31	v0.8.1.23.0	0 trades	0.00

Interpretation:
v0.8.1.23.0 completely removed a loss-heavy regime at the cost of zero participation.

3.3 Exploratory Range (Early November 2025)
Range	Version	Trades	Result
2025-11-03 → 2025-11-07	v0.8.1.22.0	Trades present	Mixed
2025-11-03 → 2025-11-07	v0.8.1.23.0	0 trades	Flat

This confirmed that modern market structure frequently prints early structural damage, making a strict lockout highly selective.

4. TWCS-Based Structural Analysis (Critical Insight)

TWCS (Trade-With-Candle-Snapshots) analysis compared:

BKYI — 2025-10-27 (post-damage loser)

SLMT — 2025-10-23 (post-damage winner)

Structural Comparison
Structural Question	BKYI (Loss)	SLMT (Win)
Structural damage before entry	Yes	Yes
VWAP reclaimed	Yes	Yes
≥2 bars closing above VWAP before entry	No	Yes
Red displacement after reclaim	Yes	No
Conclusion

The decisive difference was not damage itself, but whether structure healed:

A genuine VWAP reclaim followed by multiple stable closes above VWAP, with no new structural damage, distinguished the winner from the loser.

This insight motivates v0.8.1.24.0.

5. Purpose of the Next Version (v0.8.1.24.0)
Objective (One Sentence)

Test a narrow, structure-aware escape hatch that re-admits post-damage entries only after VWAP has been reclaimed and proven stable via consecutive confirmation closes, while preserving the strict v0.8.1.23.0 safety floor.

Key Philosophy

v0.8.1.23.0 remains the default safety behavior

v0.8.1.24.0 adds one controlled exception, not a relaxation

6. Locked Design Decisions for v0.8.1.24.0

These decisions are final and must not be revisited during implementation:

Escape hatch only — does not replace post-damage lockout

VWAP reclaim + 2 consecutive confirmation closes

Reclaim bar does not count as confirmation

Entry allowed only on the bar after the second confirmation close

No structural-damage bars during reclaim + confirmation window

One healed attempt per symbol per day

Ignore premarket structure (RTH-only)

Explicit failure condition:

Reject if BKYI-like failures reappear or same-/next-bar SLs increase vs v0.8.1.23.0

7. Required Testing Plan for v0.8.1.24.0 (PRIMARY FRAME)
7.1 Three-Version Comparative Testing (MANDATORY)

All testing must be executed as a three-version comparison:

v0.8.1.22.0 — unprotected baseline

v0.8.1.23.0 — strict structural safety floor

v0.8.1.24.0 — safety floor + VWAP-heal escape hatch

No conclusions about v0.8.1.24.0 are valid unless all three versions are run on the same ranges.

This framework answers:

What happens with no protection?

What losses are removed by strict structure?

What opportunity can be safely reintroduced?

7.2 Familiar / Previously Studied Ranges (Repeat Exactly)

Run all three versions on:

2025-10-23 (SLMT day)

2025-10-27 (BKYI canonical failure)

2025-12-05 (loss-heavy healthy day)

2025-10-20 → 2025-10-31

2025-11-03 → 2025-11-07

7.3 Unfamiliar / Out-of-Sample Ranges (Mandatory)

Add two multi-week unfamiliar ranges, run in all three versions:

Range A — January 2026

Preferred: full month

Minimum: Jan 6 → Jan 31, 2026

Purpose: test behavior in a new-year regime

Range B — March 2025

Preferred: full month

Minimum: Mar 1 → Mar 31, 2025

Purpose: test behavior in a different historical volatility regime

8. Analysis Requirements (Non-Negotiable)
8.1 Quantitative (Per Range, Per Version)

For each range and version record:

Trades

Wins / losses

Win rate

Total PnL

Same-bar stop-outs

Next-bar stop-outs

The key question is not profitability alone, but loss behavior relative to v0.8.1.23.0.

8.2 TWCS-Based Qualitative Review (MANDATORY)

For every trade admitted by v0.8.1.24.0 that was blocked in v0.8.1.23.0:

Inspect TWCS snapshots

Verify:

reclaim bar

two confirmation closes

absence of new damage

correct entry timing (post-confirmation bar)

Compare against:

v0.8.1.23.0 blocked outcome

v0.8.1.22.0 behavior (if traded)

TWCS is first-class evidence; aggregates alone are insufficient.

9. Success / Failure Criteria for v0.8.1.24.0
Success

Preserves loss suppression of v0.8.1.23.0

Re-admits a small, explainable set of structurally clean trades

No increase in same-/next-bar stop-outs

TWCS confirms genuine structure healing

Failure

Re-admits BKYI-like false reclaims

Increases early stop-outs

Behaves closer to v0.8.1.22.0 than v0.8.1.23.0

TWCS does not clearly justify admitted trades

10. Closing Guidance

v0.8.1.23.0 established a structural safety floor.
v0.8.1.24.0 is a controlled escape-hatch experiment, not a strategy rewrite.

This version must remain:

slow

skeptical

reversible

three-version validated

TWCS-driven

Do not optimize, tune, or broaden beyond the defined escape hatch.

End of Handover Specification — v0.8.1.24.0