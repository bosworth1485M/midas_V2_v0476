ACTIVE_GUARDS_LEDGER.md

CUMULATIVE DOCUMENT — DO NOT RESET PER VERSION

This file is the authoritative, long-term record of all active, retired, and experimental guards in Midas_V2.
It captures why each guard exists, what failure class it blocks, when it was introduced, and whether it remains active.

This is not a per-version summary. Each version adds to this ledger.

Style rule: Latest summary and newest guards appear at the top.


POST_DAMAGE_ENTRY_LOCKOUT (v0.8.1.23.0)
- Status: ENABLED (scoped as of v0.8.1.31.0)
- Scope (v0.8.1.31.0): Applies ONLY when day_class == "hostile" (Scenario B day-gate classification).
- Purpose: Prevent post-damage entries on hostile regimes where reclaim/fade losses cluster.
- Notes: Previously acted as a day-long symbol kill-switch after first damage candle; v0.8.1.31.0 narrowed scope to restore participation on marginal/healthy days while preserving hostile-day safety.




ASC_GREEN — Scenario B (Diagnostic Disable) — v0.8.1.30.0

Guard name:
ASC_GREEN (ascending green candles requirement)

Original purpose:
Enforce Cameron-style momentum quality by requiring ascending green candles before allowing continuation entries, intended to filter weak or choppy follow-through.

Change in this version:

Scenario B only: ASC_GREEN temporarily disabled via config flag (disable_asc_green=true)

All other scenarios unchanged

Guard logic remains intact in code; enforcement is bypassed only when the flag is set

Reason for change:
Frequent zero-trade days raised concern that ASC_GREEN might be over-blocking valid Cameron-style continuation entries. This version explicitly tested whether ASC_GREEN was the primary participation bottleneck.

Observed behavior (A/B evidence):

In v0.8.1.29.0, ASC_GREEN was actively blocking many candidates (ASC_GREEN_BLOCK events observed).

In v0.8.1.30.0, ASC_GREEN blocking was fully removed.

Zero-trade days persisted in hostile regimes (Dec 02–06, 2025), indicating ASC_GREEN was not the dominant blocker.

Structural damage guards (POST_DAMAGE_ENTRY_LOCKOUT, STRUCT_DAMAGE_FAIL) were the primary remaining rejection causes.

Conclusion:
ASC_GREEN is confirmed to be a secondary friction guard, not the root cause of zero-trade behavior. Disabling it alone does not restore participation in structurally damaged regimes.

Current status:

Disabled for Scenario B only (diagnostic state)

Remains enabled and unchanged elsewhere

Treated as reversible and under evaluation

Side effects / risks:

Removing ASC_GREEN may admit lower-quality continuations if structural guards are later relaxed.

ASC_GREEN should not be permanently removed without contextualizing it within revised structure-damage rules.

Re-enable procedure:

Remove or set disable_asc_green=false for Scenario B in config/scenarios.json

No code changes required

Next planned action (per roadmap):
Do not further adjust ASC_GREEN yet.
Proceed to v0.8.1.31.0, which will scope and narrow post-damage structural lockouts so participation is restored in valid regimes before re-evaluating secondary quality filters.

This version is explicitly marked as PLANNED / PROPOSED and does not claim anything has changed yet.

MARGINAL_VWAP_WINDOW_REJECT — Insufficient-History Bypass

Status: PLANNED for v0.8.1.29.0 (not implemented yet)

Guard name: MARGINAL_VWAP_WINDOW_REJECT (introduced v0.8.1.11.0)

Type: ALIGNMENT (Cameron alignment) + SAFETY (prevent false rejects) + OBSERVABILITY

Purpose

Document a planned alignment fix to prevent the marginal VWAP window gate from making a hard reject decision when the required bar window does not yet exist at the market open. This change is intended to restore Cameron-aligned behavior: insufficient data → wait/unknown, not “reject.”

Observed failure class (evidence)

Repeated logs:
MARGINAL_VWAP_WINDOW_REJECT ... ts=09:30 hits=0

Root cause: the window [i-1, i-2, i-3] is out-of-bounds when i < 3, making hits=0 mathematically unavoidable.

Effect: systematic early suppression of trades (including in good August momentum days), plus distorted observability due to dedupe hiding later meaningful rejects.

Planned change for v0.8.1.29.0

When evaluating the marginal VWAP window:

If i < 3 (insufficient history / empty window):

Do NOT reject

Do NOT log MARGINAL_VWAP_WINDOW_REJECT as a WARNING

Do NOT add the reject dedupe key for this case

Do NOT increment marginal-gate block telemetry

Optionally log once per symbol/day at INFO or DEBUG:
MARGINAL_VWAP_WINDOW_INSUFFICIENT

For i ≥ 3:

Behavior unchanged (same window, same thresholds, same reject semantics)

When ON / OFF

Not active yet

Will be ON by default starting v0.8.1.29.0 only after implementation and validation

Can be disabled for A/B comparison against v0.8.1.28.0 if needed

Known risks / considerations

Expected to increase trade engagement near the open, especially on good momentum days

Does not weaken downstream protections (ASC_GREEN, VWAP_EXT, POST_DAMAGE locks, DAY_GATE throttle remain unchanged)

Reduces noisy early-open WARNING logs and improves interpretability

Validation plan (required before promotion)

Sanity window: 2025-11-18 → 2025-11-22 (Scenario B)

Hostile cluster: 2025-12-02 → 2025-12-06

Good momentum cluster: 2025-08-05 → 2025-08-15

Older cluster: 2025-07-14 → 2025-07-18

Success criteria:

Trade engagement restored on August without reintroducing known loss clusters

≥ +3 pp win rate or +0.2R expectancy or profit factor ≥ 1.2 with positive PnL lift

TWCS confirms the empty-window failure class is eliminated

Notes

This entry is documentation of intent, not an active guard. It must be updated to “Implemented” only after v0.8.1.29.0 passes validation.







Active Guards Ledger Entry — v0.8.1.26.0
Guard Name

DAY_GATE (Follow-Through Day Classification)

Status

ACTIVE — UNDER ALIGNMENT REVIEW

First Introduced
Guard: ASCENDING_GREEN_CONTINUATION_GUARD

Introduced in: v0.8.1.28.0
Applies to: Scenario B
Status: ACTIVE (default ON)

Purpose

Ensure that continuation entries occur only on intact structure with real upward momentum, by enforcing ascending green candles, not merely the presence of green candles.

Guard Definition

A continuation entry is permitted only if the last N candles (where N = rise_bars, default 3):

Are green (close > open)

Have a real body (meets green_body_min)

Are ascending:

Each candle closes higher than the previous

Lows do not move downward

Belong to the same continuous price structure

If any structural damage occurs after the first candle in the sequence, the continuation count is reset/invalidated.

Failure Class Blocked

Post-damage continuation entries, where:

A large red displacement breaks structure

Green candles occur afterward or in a different price zone

The system previously misclassified this as valid continuation

Example:

MAGN — 2025-11-20 (Scenario B, v0.8.1.27.0)

Evidence

Validation window: 2025-11-18 → 2025-11-22

Observed SL on MAGN due to continuation counted after structural damage

TWCS confirmed:

No ascending green candles in the entry price zone

Continuation signal was structurally invalid

Behavior When ON

Blocks trades that satisfy green-count mechanically but fail ascending + structure criteria

Resets continuation immediately after structural damage

Produces explicit WHY logs:

ASC_GREEN_BLOCK

reason codes (e.g., non_ascending_close, post_damage_reset)

Known Side Effects

May reduce trade count on choppy or post-flush days

Does not affect clean momentum days with intact structure

Designed to improve loss quality, not trade frequency

A/B Testing Procedure

A: v0.8.1.27.0 (no ascending enforcement)

B: v0.8.1.28.0 (guard ON)

Test clusters:

2025-11-18 → 2025-11-22 (failure reproduction)

2025-12-02 → 2025-12-06 (hostile)

2025-08-05 → 2025-08-15 (good momentum)

2025-07-14 → 2025-07-18 (time-diverse)

Removal / Disable Criteria

This guard may be toggled OFF only if:

It blocks a statistically significant number of structurally valid winners, and

TWCS evidence shows continuation was intact but misclassified

Any disablement must be accompanied by:

Explicit A/B comparison

Documented TWCS evidence

Project log entry

Notes

This guard enforces an implicit assumption used by successful Cameron-style traders:

Continuation means ascending price, not just green candles.
Earlier versions (pre–v0.8.1.26.0)
Formal review and reclassification initiated in v0.8.1.26.0

Purpose

DAY_GATE evaluates early-session market follow-through to classify the trading day as:

Healthy

Marginal

Hostile

The original intent was to:

Reduce exposure on weak tape

Prevent low-quality trades during broadly unsupportive market conditions

Provide regime context for risk and participation decisions

Current Behavior (As of v0.8.1.26.0)

When DAY_GATE fails follow-through criteria:

The day is classified as hostile or marginal

Scenario B enforces a hard global block via:

EARLY_REJECT(DAY_GATE_FAILED) at approximately 09:30

All symbols are prevented from entering trades for the remainder of the session

This behavior is intentional and deterministic, not a bug.

Observed Side Effects

Empirical testing (Oct–Dec 2025) demonstrated that:

DAY_GATE frequently fails due to insufficient multi-symbol follow-through

This results in entire trading days with zero participation for Scenario B

Multi-week and multi-month zero-trade periods were observed

High-quality single-name momentum setups were suppressed on mixed or weak tape

Alignment Assessment

⚠️ Behavioral Misalignment Identified

While DAY_GATE successfully blocks low-quality conditions, its current hard-block consequence is not aligned with the behavior of the most successful Cameron-style trading projects, which typically:

Scale down risk and trade count on weak tape

Do not globally disable trading solely due to lack of multi-symbol follow-through

Allow participation in exceptional single-name momentum even on mixed days

This guard therefore represents a strategic divergence, not a correctness issue.

Decision in v0.8.1.26.0

No immediate behavior change

Guard remains active and unchanged in this version

Strategic intent and concerns are explicitly documented

Alignment review deferred to next version per Cameron Alignment Plan

This preserves safety while preventing silent drift.

Planned Action (Per CAMERON_ALIGNMENT_PLAN.md)

In the next version:

Scenario B only

DAY_GATE classification logic will be preserved

DAY_GATE consequence will be modified:

From hard global block

To throttled participation (reduced trade count and/or reduced risk)

All changes will be validated via strict A/B testing

No other guards are scheduled for modification in the same version.

Guard Type Classification

Primary Type: SAFETY (loss-subtraction)

Secondary Impact: ALIGNMENT (currently negative)

Review Status: ACTIVE, UNDER REALIGNMENT

Notes

This entry exists to ensure that:

DAY_GATE behavior is not misinterpreted as accidental

Zero-trade periods are understood as guard-driven

Future changes are evaluated against explicit Cameron alignment criteria

Ledger Status:
🟡 Active, functioning as designed
🟡 Strategic realignment pending
🟢 Fully documented and intentional

POST_DAMAGE_VWAP_HEAL_ESCAPE (v0.8.1.24.0)

Guard: POST_DAMAGE_VWAP_HEAL_ESCAPE (v0.8.1.24.0)
Type: Post-damage exception (escape hatch) layered on safety floor
Default: ON in v0.8.1.24.0+ (treat as reversible/diagnostic)

Purpose

Allow a single post-damage entry only when structure has clearly “healed” via VWAP reclaim stability, while preserving the strict post-damage lockout as the default safety floor.

Failure class targeted

Blocks BKYI-class false reclaims: damage → weak reclaim → no stabilization → immediate stop-outs.

Re-admits SLMT-class healed setups: damage → VWAP reclaim → multiple stable closes above VWAP → continuation.

Rule (exact)

Escape hatch allows entry only if:

Damage occurred earlier in RTH (damage_first_idx set)

VWAP reclaim occurs (close > VWAP)

Two consecutive confirmation closes above VWAP occur after reclaim (reclaim bar does not count)

No structural-damage bars occur during reclaim→confirm window

Entry permitted only on bar i = confirm2_i + 1

One healed attempt per symbol/day

RTH-only

Observability

Must emit:

VWAP_HEAL_RECLAIM

VWAP_HEAL_READY

POST_DAMAGE_HEAL_ENTRY_ALLOWED source=normal|pending_confirm
and day-level post_damage_heal_entries_allowed in REGIME_SUMMARY blocks_total.

Known side effects

Can admit rare “healed” trades that still lose (expected).

Outcomes may be contaminated on symbol/days with duplicate timestamps until v0.8.1.25.0 correctness fix lands.

A/B procedure

Compare:

A: v0.8.1.22.0 (unprotected)

B: v0.8.1.23.0 (floor)

C: v0.8.1.24.0 (floor + hatch)

Must re-run:

2025-10-23 (SLMT) — hatch should allow healed entry

2025-10-27 (BKYI) — hatch must NOT allow entry

Reject if:

BKYI-like failures reappear

same/next-bar SLs increase vs v0.8.1.23.0







POST_DAMAGE_ENTRY_LOCKOUT

Version introduced: v0.8.1.23.0
Status: ✅ Active (validated safety floor)

Purpose

Prevent intraday entries on symbols that have already suffered structural damage, eliminating a dominant class of same-bar and near-immediate stop-outs.

Guard definition

Once a structural damage bar occurs for a symbol during RTH, all subsequent entries for that symbol are blocked for the remainder of the day, regardless of day regime (healthy / marginal / hostile).

This guard applies to:

normal entry attempts, and

pending entry confirmations.

Failure class blocked

Post-damage VWAP reclaims that immediately fail

Same-bar or next-bar stop-outs following early red displacement

BKYI-class failures (damage → weak reclaim → instant SL)

Evidence / validation

Validated via strict A/B testing against v0.8.1.22.0:

Single-day tests:

2025-10-23 (SLMT)

2025-10-27 (BKYI canonical failure)

2025-12-05 (loss-heavy healthy day)

Contiguous range:

2025-10-20 → 2025-10-31

Exploratory ranges:

Early November 2025

Results:

Losses attributable to post-damage entries were eliminated.

Guard behaved deterministically with no leaks.

TWCS confirmed that blocked trades shared a consistent structural failure pattern.

Known side effects

Guard is intentionally strict.

Blocks some historical winners that occurred after early structural damage.

Can lead to zero-trade days in regimes where early damage is common.

These side effects are accepted and desired for a safety-layer guard.

Relationship to other guards

Acts after structural damage detection.

Does not replace day gate, VWAP extension, or marginal-day logic.

Serves as a hard safety floor upon which narrow exceptions may be layered.

Interaction with v0.8.1.24.0

v0.8.1.23.0 remains the default behavior.

v0.8.1.24.0 introduces a narrow escape hatch (VWAP heal with confirmation) that overrides this guard only under strictly defined structural conditions.

The lockout itself is not removed.

A/B testing procedure (for future changes)

To evaluate any modification or exception:

Run identical ranges in:

v0.8.1.22.0 (no lockout)

v0.8.1.23.0 (strict lockout baseline)

candidate version

Confirm:

BKYI-class failures remain blocked

same-bar / next-bar SLs do not increase

Review TWCS for every re-admitted trade

When to turn OFF

Only for explicit diagnostic comparison runs.

Must never be disabled silently in production tests.
GUARD: POST_DAMAGE_ENTRY_LOCKOUT (v0.8.1.23.0) — PLANNED

Status: Planned (OFF; not implemented yet)

Purpose: Prevent entries after structural damage even on “healthy” days (structure overrides regime).

Failure class blocked: Healthy-day post-damage grind reclaim → immediate SL / clustered losses (e.g., BKYI 2025-10-27).

Trigger condition: Structural damage detected for a symbol intraday (same damage definition already used by STRUCT_DAMAGE logic). Once detected, latch damage_seen=True for that symbol/day.

Block behavior: While damage_seen=True, block all new entries for that symbol for the rest of the day (no continuation exception in v0.8.1.23.0).

Logging requirement: Log once per symbol/day when the lockout blocks an entry: [WHY] v0.8.1.23.0 POST_DAMAGE_ENTRY_LOCKOUT … damage_ts … day_class …

Known side effects (expected): May reduce trade count by blocking late re-entries; risk of blocking rare legitimate post-damage recoveries (to be evaluated).

A/B test procedure:

A: baseline commit 1e48efb

B: v0.8.1.23.0 with lockout enabled

Sanity: 2025-10-27 (BKYI loss), 2025-10-23 (SLMT winner), one Dec hostile day

Ranges: 2025-10-20→10-31 and 2025-12-02→12-06

Pass criteria: measurable lift (≥ +3pp WR or +PnL) and TWCS confirms BKYI-class is blocked while SLMT-class remains allowed.




GUARD: POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD — Hostile-only scope test (v0.8.1.22.0)

Status: Tested → REJECTED (do not rely on as a loss-control mechanism)

Purpose (tested): Evaluate whether restricting post-damage weak VWAP reclaim blocking to hostile days only improves outcomes.

Failure class targeted: Post-damage weak VWAP reclaims on hostile days.

Change tested: Guard execution limited to day_class == hostile; guard disabled on healthy days.

Test period:

October 20–31, 2025 (mixed regime)

December 2–6, 2025 (hostile-heavy regime)

Result: No improvement. Losses persisted on healthy days; December remained strongly negative.

Key finding: Dominant loss class is post-damage entries on healthy days, which this guard cannot address by design.

TWCS evidence:

BKYI (2025-10-27): healthy day, structural damage before entry → same-bar SL; guard inactive.

SLMT (2025-10-23): healthy day, no prior damage → clean TP; unaffected by guard.

Conclusion: Regime-scoped post-damage VWAP reclaim logic is insufficient. Structural damage must override day regime.

Follow-on action: Superseded by POST_DAMAGE_ENTRY_LOCKOUT (v0.8.1.23.0 — Planned), which blocks all post-damage entries regardless of regime.

Notes: Keep code path documented for historical reference only; do not treat as an “active” protection.




POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD — Regime Execution Scope

Guard ID: POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD
Introduced: v0.8.1.19.0
Ledger Update: v0.8.1.21.0 (observability only)

Purpose

Prevent trade entries when price attempts a weak VWAP reclaim after prior structural damage, a pattern shown to produce systematic losses in hostile market conditions.

Current Execution Behavior (as of v0.8.1.21.0)

The guard logic executes whenever a post-damage reclaim setup is evaluated, regardless of day classification.

There is no regime-level gate controlling whether the guard logic runs.

As a result:

On healthy days, if a post-damage reclaim candidate satisfies the guard’s internal conditions, the guard logic executes and blocks the trade.

Healthy day classification does not bypass this guard.

This describes current behavior only and does not imply correctness.

Evidence Summary (v0.8.1.21.0)

Hostile regimes (Dec 2025):

Post-damage reclaim trades were systematically unprofitable.

Guard behavior aligned with loss prevention.

Trend-capable regimes (Oct 2025):

Similar post-damage reclaim patterns occurred.

Outcomes were mixed (both wins and losses).

Losses were not systematic.

No A/B test has yet been performed to determine whether trades blocked on healthy days would have improved or degraded performance.

Known Effective Scope

Hostile days: Guard behavior appears necessary for loss control.

Healthy days: Effect of guard behavior is unknown.

Change Status

No behavior changes implemented in v0.8.1.21.0.

This ledger entry records observed execution scope, not a policy decision.

Planned Experiment (v0.8.1.22.0)

Introduce a regime-level execution gate:

Hostile day:

POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD logic executes unchanged.

Healthy day:

POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD logic does not execute.

No changes to the guard’s internal logic, thresholds, or definitions.

Validation Plan

Re-run the same time-diverse ranges used in v0.8.1.21.0:

2025-12-02 → 2025-12-06 (trap / hostile)

2025-10-20 → 2025-10-31 (trend-capable)

Compare:

trade counts

day-level PnL

drawdown behavior

reappearance (or absence) of December loss patterns

Notes

This guard remains active and unchanged until v0.8.1.22.0 introduces the regime-gated execution experiment.
Guard: Post-Damage Weak VWAP Reclaim Guard
POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD

Introduced: v0.8.1.19.0
Status: ACTIVE (default ON)

Purpose:
Block late, weak VWAP reclaims that occur after structural damage on otherwise healthy days.

Failure Class Addressed:
Trap days with repeated structural damage followed by shallow VWAP reclaims that fail continuation.

Change Type:
Trading logic change (loss-subtraction guard).

Evidence at Introduction:
December 2025 trap regime showed improvement vs baseline when the guard was enabled
(e.g., 2025-12-04: A −41.66 → B +21.29).

Known Risks at Introduction:
Potential opportunity cost on trend-friendly days (October / November regression observed).
Regime sensitivity suspected but not yet measured.

Observability at Introduction:
Limited (block reasons visible in logs only).

Decision at v0.8.1.19.0 Close:
Keep guard ON by default.
Accept potential opportunity cost pending improved observability.

Notes:
This guard is not intended to address momentum exhaustion at highs.
Future work may evaluate regime-gated activation.




-- Historical note: legacy post-damage continuation guard (v0.8.1.12.0–v0.8.1.13.0) ---
v0.8.1.13.0 Change (Observability Only):
When this guard blocks a trade, the system now writes a best-effort JSON snapshot (blocked_candidates) capturing structured context (symbol, time, day_class, continuation count, structural damage state, and guard enablement).
No trading logic, thresholds, or behavior were changed.

Known Side Effects / Limitations:

The blocked_candidates directory reflects only this instrumented guard, not all blocked trades.

Absence of a snapshot does not imply that no trades were blocked by other guards.

Testing / Validation:

Behavior-neutral sanity run confirmed no change in trades or PnL.

Historical hostile range (Nov 2025) confirmed snapshot creation when the guard fired.

JSON contents verified correct and complete.

Notes for Future Review:
Snapshot data will be analyzed in v0.8.1.14.0 to determine whether the guard is saving losses or blocking winners under specific conditions (e.g., healthy vs marginal days) before considering any relaxation or refinement.

Legend
Post-Damage VWAP Reclaim Continuation Guard (v0.8.1.12.0)

Introduced: v0.8.1.12.0
Status: Active (validated)

Purpose:
Block VWAP reclaim entries that occur after structural damage but show no real continuation (single reclaim candle only).

Rule (Summary):
If structural damage is present and the VWAP reclaim passes the existing recovery check, require ≥2 of the prior 3 completed bars to be green and above VWAP. Otherwise, block the entry.

Failure Class Addressed:
Late VWAP reclaims after earlier structural damage with only one reclaim candle and no follow-through (e.g., CYRX 2025-08-06, IHRT/VCIG/MNDR November 2025).

Observed Effect:

Removes clustered stop-loss trades in hostile regimes

Preserves winners and behavior in neutral regimes

Demonstrated PnL improvement without regressions (A/B validated Aug / Oct / Nov 2025)

Scope / Limitations:

Applies only in post-damage contexts

Does not affect clean trend days or non-damage setups

Not a trade-ranking or sizing rule

Notes:
This guard is part of the late-stage loss-subtraction phase. Further guards should only be added if a new, clearly clustered failure class is identified.
Status: ACTIVE | CONDITIONAL | RETIRED | EXPERIMENTAL
## Marginal VWAP Window Acceptance Guard — v0.8.1.11.0

### Purpose
Prevent early marginal-day “first VWAP touch” entries while **preserving legitimate delayed VWAP continuations**.  
This guard refines marginal-day participation from hard suppression to **selective delay**.

### Guard Type
Entry gate (marginal-day only)

### When It Applies
- Scenario **B**
- Day classified as **marginal** by DAY_GATE
- Before first trade of the day (marginal trade allowance)
- Only when entry would otherwise be eligible

### Rule (Operational)
On marginal days, require **VWAP acceptance within a short window** rather than strict consecutive confirmation:
- Evaluate recent completed candles (windowed acceptance)
- Allow entry only after sufficient VWAP acceptance is demonstrated
- Early 09:30 marginal attempts are delayed; later valid continuations may proceed

*(Implementation detail: windowed acceptance replaced strict “i-2 AND i-1 above VWAP” logic from v0.8.1.10.0.)*

### Introduced In
- **v0.8.1.11.0**

### Default State
- **ON**

### Failure Class Blocked
- Early marginal-day junk entries at the open (09:30–09:35) that historically produced full-stop SLs
- “First close above VWAP” marginal entries without prior acceptance

### What It Does NOT Block
- Legitimate delayed VWAP continuations on marginal days
- Healthy-day trading
- Hostile-day suppression (handled by DAY_GATE)

### Observability
- Enable log:
  - `MARGINAL_VWAP_GATE v0.8.1.11.0: enabled=True`
- Rejection log (log-once per symbol/day):
  - `MARGINAL_VWAP_WINDOW_REJECT`
  - Includes hit count, representative bar index, close, VWAP

### A/B Validation Procedure
Compare **v0.8.1.10.0 (A)** vs **v0.8.1.11.0 (B)** using identical ranges:
- August 2025
- October 2025 (out-of-sample)
- November 2025 (hostile regime)

Expected outcome:
- Identical trades, win rate, and PnL (behavior-preserving)
- Presence of early `MARGINAL_VWAP_WINDOW_REJECT` logs in B confirming delay behavior

### Known Side Effects
- Slight delay of marginal entries; does **not** increase trade count
- No profitability impact by design (correctness/stability guard)

### Notes
This guard establishes a **stable baseline** for subsequent profitability work.  
It is intentionally conservative and diagnostic-friendly.
Scope: Entry | Post-Entry | Day-Level | Risk | Execution

Failure Class: The TWCS-confirmed failure pattern this guard addresses

## Guard: Marginal VWAP Acceptance (2-bar pre-confirm) — v0.8.1.10.0
- **Status:** ON by default (Scenario B, marginal days only)
- **Where:** `src/midas_v2/engine/backtester.py` (inserted between `DAY_GATE_FAILED` early reject and the combined entry condition)
- **Trigger scope:** Only when:
  - `require_day_follow_through == True` (DAY_GATE enabled)
  - `close_gt_vwap_count == 1` (marginal day)
  - `day_trade_count < 1` (marginal trade still available)
  - entry otherwise eligible (`position is None`, `pending_entry is None`, `effective_day_gate_failed == False`)
- **Rule:** Reject entry unless the two prior completed candles (i-2 and i-1) are both:
  - green (`close > open`)
  - and closed above VWAP-at-that-bar (VWAP computed incrementally via PV/V using tp=(h+l+c)/3; loop `for k in range(i)` so VWAP(i-1) is computed)
- **Reject reason / log anchor:** `MARGINAL_VWAP_ACCEPT_FAIL` (log-once per date+symbol via `early_reject_logged`)
- **Failure class blocked (TWCS/log-proven):**
  - Early 09:30 marginal “first close above VWAP” entries that repeatedly hit full-stop SL (April: GRI/IBO/NAOV/BON/CNEY class)
- **Known side effects (TWCS-proven):**
  - Can suppress legitimate delayed VWAP acceptance winners (e.g., JNVR 2025-04-07 TP +2.0% was suppressed under strict consecutive requirement)
- **A/B test procedure (canonical):**
  - April 2025:
    - A (v0.8.1.9.0): `run_range_and_summarize.py --start 2025-04-01 --end 2025-04-30 --scenario B` → totals `trades=24 losses=14 PnL=-209.89`
    - B (v0.8.1.10.0): same range → totals `trades=17 losses=9 PnL=-91.27`
    - Loss attribution: removed SLs `{20250401 GRI, 20250404 IBO, 20250408 NAOV, 20250411 BON, 20250424 CNEY}` all blocked at 09:30 by this guard
  - August 2025 (time-diverse cluster):
    - A (v0.8.1.9.0): `trades=18 losses=12 PnL=-251.80`
    - B (v0.8.1.10.0): `trades=11 losses=6 PnL=-70.08`
- **Notes / next action:**
  - v0.8.1.11.0 planned refinement: windowed acceptance (e.g., “2 of last 3”) to preserve early-loss suppression while restoring delayed acceptance winners.

Status: ON by default in v0.8.1.10.0 baseline (Scenario B)


Summary (As of v0.8.1.8.1)

Active Guards:

Confirm-bar stop-violation guard

Post-entry expansion confirmation

DAY_GATE (close-above-VWAP)

Structural damage guard (auto-controlled)

VWAP extension gate

Conditional / Diagnostic:

Microstructure gates

Retired / Fixed:

TP/SL wick-handling backtester bug

Strategic Position:

The guard stack now enforces, in order:

Day quality

Location discipline

Structural integrity

Immediate follow-through

Execution realism

This establishes a clean, explainable base for controlled profitability recovery in subsequent versions.

Guard G-007 — Confirm-Bar Stop-Violation Guard

Introduced: v0.8.1.8.1

Status: ACTIVE

Scope: Execution / Entry

Failure Class: Entries that are already stopped intrabar on the confirmation candle

Rule:

Reject trades where the confirmation candle’s intrabar price action would already violate the stop.

Outcome:

Eliminates execution-invalid entries that cannot succeed in live trading.

Does not materially suppress trades on healthy momentum days.

Notes:

Execution-safety guard, not a profitability or selectivity filter.

Guard G-004 — Post-Entry Expansion Confirmation Gate

Introduced: v0.8.1.7.0

Status: ACTIVE

Scope: Post-Entry

Failure Class: Entries that stall immediately after trigger

Rule:

Require measurable expansion (bps) within N minutes after entry signal

Otherwise cancel the trade

TWCS Evidence:

Many losers failed immediately after entry without expansion

Winners showed early follow-through

Outcome:

Improved trade quality

Reduced marginal, grind-down losses

Conclusion: KEEP — foundational post-entry quality filter

Guard G-003 — DAY_GATE (Close-Above-VWAP Qualifier)

Introduced: v0.8.1.6.0

Status: ACTIVE

Scope: Day-Level

Failure Class: Trading on structurally weak market days

Rule:

Require ≥1 early symbol to close above VWAP

Otherwise block all Scenario B trades

Outcome:

Prevented false-green, low-quality days

Enabled intelligent auto-switching of other guards

Observed Impact (v0.8.1.8.1):

DAY_GATE is the dominant suppressor of trade count on marginal days when
require_close_gt_vwap = True and close_gt_vwap_cnt = 0.

No behavior change was made in v0.8.1.8.1; impact is now fully observable.

Guard G-002 — Structural Damage Guard (Reject Weak VWAP Reclaim)

Introduced: v0.8.1.4.0

Status: ACTIVE (Auto-controlled)

Scope: Entry

Failure Class: Entering after hard red displacement followed by weak reclaim

Rule:

Reject VWAP reclaims that occur after structural damage without real continuation

Control: Auto-enabled via DAY_GATE logic

Outcome:

Blocked multiple TWCS-confirmed losing setups

Preserved August-style momentum days

Guard G-001 — VWAP Extension Gate

Introduced: v0.8.1.1.0

Status: ACTIVE

Scope: Entry

Failure Class: Chasing over-extended moves far above VWAP

Rule:

Reject entries where price exceeds VWAP by more than configured %

Outcome:

Reduced late-extension losses

No material reduction in high-quality winners

Notes: Foundational location-discipline guard

Guard G-006 — Microstructure Gates (Early Experiments)

Introduced: v0.8.1.0.x

Status: CONDITIONAL / DIAGNOSTIC

Scope: Entry Timing

Failure Class: Poor micro-timing

Notes:

Not primary profit drivers yet

Retained for future refinement after structure discipline is complete

Guard G-005 — Post-Entry Expansion (Incorrect TP/SL Evaluation)

Introduced: v0.8.1.7.0

Status: RETIRED (Bug fixed)

Scope: Execution / Backtester Correctness

Failure Class: TP missed due to flattened or mutated bars

Issue:

Position management evaluated TP/SL on mutated bars

Valid wick hits were ignored

Fix:

Preserve true OHLC bars for TP/SL checks

Duplicate-timestamp-safe merge with wick preservation

Outcome:

TCMD and similar cases now correctly register TP

Backtester results are trustworthy again

Notes: This was a correctness bug, not a strategy change