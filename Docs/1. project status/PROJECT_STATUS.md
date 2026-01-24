# PROJECT_STATUS.md

## Midas_V2 — Cumulative Project Status (Authoritative)

> This document is the **single authoritative, cumulative history** of the Midas_V2 project.
> It is **not** a single‑version summary. Each version adds an entry; no prior entries are removed.

---
### Profitability Expectations (Project-Level)

This project prioritizes defensible, repeatable improvement over instant profitability.

Current phase:
- v0.8.1.20.0 completed observability (no profit change expected).
- v0.8.1.21.0 focuses on regime measurement only.
- v0.8.1.22.0 is the earliest version where a justified regime gate may produce visible improvement.

Success is defined as:
- fewer clustered loss days,
- higher win rate in hostile regimes,
- preserved winners in trend-friendly regimes,
- clear A/B separation.

Timeline expectation: ~1–2 focused versions after observability.

## Latest Completed Version

## Alignment Roadmap (active)
v0.8.1.30.0 — ASC_GREEN diagnostic A/B (Scenario B only)

Purpose:
Temporarily disable the ASC_GREEN guard for Scenario B to test whether it was blocking valid Cameron-style continuation entries and causing zero-trade days.

What was tested:

Scenario B only: ASC_GREEN disabled via config flag

A/B comparison against v0.8.1.29.0 on:

Dec 02–06, 2025 (hostile / low-quality regime)

Aug 05–07, 2025 (good momentum regime)

Results:

Dec 02–06:

v0.8.1.29.0 and v0.8.1.30.0 both produced 0 trades

v0.8.1.29.0 showed frequent ASC_GREEN_BLOCK events

v0.8.1.30.0 removed ASC_GREEN_BLOCK, but entries were still prevented by:

POST_DAMAGE_ENTRY_LOCKOUT

STRUCT_DAMAGE_FAIL

Aug 05–07 (v0.8.1.30.0):

Scenario B participated with 2 trades, 50% win rate, −5.32 PnL

Conclusion:
ASC_GREEN was confirmed to be actively blocking candidates, but it is not the primary cause of zero-trade days. Structural damage guards (POST_DAMAGE_ENTRY_LOCKOUT, STRUCT_DAMAGE_FAIL) are the dominant participation bottleneck. This version successfully falsified ASC_GREEN as the main blocker and narrowed the focus of subsequent versions.

Next step (per plan):
Proceed to v0.8.1.31.0, which will scope and narrow post-damage structural lockouts so Scenario B can participate on valid Cameron-style continuation days without re-admitting known loss patterns.
v0.8.1.29.0 (completed)
- Removed false open-time marginal VWAP rejection (i<3).
- Proven not to be the cause of zero trades in Dec 2025.

v0.8.1.30.0 (next)
- Hypothesis: ASC_GREEN is too strict vs successful Cameron projects.
- Plan: Disable ASC_GREEN for Scenario B (A/B test, no other changes).

v0.8.1.31.0 (conditional)
- If v0.8.1.30.0 increases participation without loss blowup:
  - Redesign ASC_GREEN (scope, delay, or soften).

v0.8.1.32.0 (later)
- Validate day-quality scaling (hostile ≠ flat; smaller/fewer instead).

Notes:
- One hypothesis per version.
- Alignment Spec updated only after hypotheses are proven.

v0.8.1.29.0 — PLANNED (Alignment restoration; not implemented yet)

Status: Planned next version (no code changes yet)

Objective (one sentence):
Restore Cameron alignment by fixing a structural mis-implementation where MARGINAL_VWAP_WINDOW_REJECT fires at market open with an empty bar window (i<3, hits=0) and suppresses valid trades even on good momentum days.

Background / evidence

v0.8.1.28.0 correctly fixed execution-time structure enforcement (ascending green candles at pending-entry confirmation).

Validation showed near-zero trade engagement in August 2025 despite good momentum conditions.

Log analysis identified repeated warnings:
MARGINAL_VWAP_WINDOW_REJECT ... ts=09:30 hits=0

Root cause: the marginal VWAP window [i-1,i-2,i-3] is out-of-bounds at market open, making hits=0 unavoidable; the current logic treats this as a hard reject and dedupe hides later meaningful diagnostics.

Planned change (single, narrow fix)

Treat i < 3 as insufficient history for the marginal VWAP window.

Bypass the MARGINAL_VWAP_WINDOW_REJECT in this case:

no rejection

no WARNING log

no dedupe reject key

no marginal-gate telemetry increment

Preserve all existing behavior for i ≥ 3.

Guardrails

Single file only: src/midas_v2/engine/backtester.py

One change only (no refactors, no parameter tuning)

No Copilot-initiated runs or tests

All other guards (ASC_GREEN, VWAP_EXT, POST_DAMAGE locks, DAY_GATE throttle) remain unchanged

Validation plan (required)

Sanity window: 2025-11-18 → 2025-11-22 (Scenario B)

Hostile cluster: 2025-12-02 → 2025-12-06

Good momentum cluster: 2025-08-05 → 2025-08-15

Older cluster: 2025-07-14 → 2025-07-18

Success criteria:

Trade engagement restored on August without reintroducing known loss clusters

≥ +3 pp win rate or +0.2R expectancy or profit factor ≥ 1.2 with positive PnL lift

TWCS confirms elimination of the empty-window failure class

Notes

This entry documents intent only. It must be updated to “Implemented” and linked to the Active Guards Ledger after v0.8.1.29.0 is implemented and validated.




Project Log Entry — v0.8.1.27.0 → v0.8.1.28.0

Summary:
Validation of v0.8.1.27.0 (DAY_GATE throttle) exposed a major logic correctness bug in Scenario B continuation logic.

What was observed:

In the range 2025-11-18 → 2025-11-22, Scenario B produced a losing trade (MAGN, 2025-11-20).

TWCS analysis showed the trade was taken after structural damage, with no ascending green candles in the entry price zone.

The system allowed the trade because it counted “green candles” without enforcing that they were ascending or structurally continuous.

Root cause:

The continuation rule was implemented as “N green candles exist”, rather than
“N ascending green candles on intact structure.”

Green candle counts were not reset after structural damage, allowing continuation signals from a different price zone to qualify an entry.

Conclusion:

This is a logic bug, not a tuning or sizing issue.

DAY_GATE throttle behaved correctly; the failure revealed a missing structure-first continuation guard.

Next action (v0.8.1.28.0):

Enforce ascending green candle continuation for Scenario B.

Require ascending closes (and non-decreasing lows) on intact structure.

Reset continuation immediately after any structural damage.

Validate across multiple regimes:

2025-11-18 → 2025-11-22 (failure reproduction)

2025-12-02 → 2025-12-06 (hostile/choppy)

2025-08-05 → 2025-08-15 (good momentum)

2025-07-14 → 2025-07-18 (time-diverse)

Status:
v0.8.1.27.0 closed as diagnostic success.
v0.8.1.28.0 opened to correct continuation logic.



Project Status Entry — v0.8.1.26.0

Version: v0.8.1.26.0
Theme: Cameron Alignment Reset (Strategic, Not Technical)

Purpose

v0.8.1.26.0 exists to explicitly realign Midas_V2 with the behavior of the most successful Cameron-style trading projects.

This version does not begin with code changes. It begins with a formal correction of strategic drift that had accumulated over prior versions.

Background / What Prompted This Version

Multi-month testing (Oct–Dec 2025) showed that Scenario B — intended to be the Cameron-style baseline — was producing near-zero trades, despite:

Correct execution

Clean data

Proper scenario wiring

Proven ability to trade (e.g., Scenario A executing normally)

Detailed log analysis demonstrated that:

DAY_GATE enforcement had evolved into a hard global kill switch

Hostile or marginal day classification triggered EARLY_REJECT(DAY_GATE_FAILED) at ~09:30

Entire trading days were shut down even when high-quality single-name momentum existed

This behavior does not match successful Cameron projects, which typically:

Scale risk and participation on weak tape

Do not globally shut down trading unless conditions are extreme

Continue to trade A+ single-name setups on mixed tape

The issue was therefore identified as behavioral misalignment, not a bug.

Key Outcome of This Version

This version locks strategic intent by introducing an authoritative document:

CAMERON_ALIGNMENT_PLAN.md

This document now serves as the non-negotiable source of truth for:

What “successful Cameron behavior” means operationally

What Scenario B is intended to be

How future changes must be evaluated and validated

How strategic drift must be detected and corrected

From this point forward:

Guidance must conform to the Alignment Plan

Any contradiction requires an explicit plan revision

Loss-subtraction purity may not silently override Cameron-style participation goals

Explicit Non-Changes in v0.8.1.26.0

No strategy logic changed

No guards added or removed

No parameters tuned

No execution behavior altered

This version is strategic groundwork only.

Forward Plan (Locked)

Per CAMERON_ALIGNMENT_PLAN.md, the next steps are:

v0.8.1.26.0 (this version):
Strategic reset and alignment lock-in (complete)

Next version:
Realign DAY_GATE behavior for Scenario B
(convert from hard block → throttle, Scenario B only, with strict A/B validation)

Why This Entry Matters

This entry exists to ensure that:

The project does not silently drift away from Cameron-style behavior again

Future confusion about “why B doesn’t trade” has a clear historical explanation

Strategic intent is documented independently of version threads or chat context

Status:
🟢 Strategic alignment restored
🟡 Behavioral correction queued (no code yet)
🟢 Project direction clarified and locked
Project Status Update — v0.8.1.25.0 (Execution Correctness)

Version: v0.8.1.25.0
Status: Completed and validated

This version resolved an execution correctness issue caused by duplicate minute timestamps in raw market data. Previously, strategy evaluation and position management could reference different OHLC values for the same minute, resulting in POS_MGMT_MISMATCH and contaminated TP/SL outcomes.

In v0.8.1.25.0, duplicate minute bars are now deterministically canonicalized before use, ensuring that all downstream components (strategy logic, guards, and position management) operate on the same OHLC per timestamp.

Validation results:

Known repro dates (2025-10-23, 2025-11-04) re-tested.

Duplicate timestamps observed (often hundreds per symbol), confirming the fix is exercised.

POS_MGMT_MISMATCH = False in all tested runs.

No execution regressions or flow issues detected.

No changes made to strategy logic, guards, parameters, or scenarios.

Impact:

Backtest results from v0.8.1.25.0 onward are execution-clean and trustworthy.

Any losses observed after this version represent true strategy behavior, not data or execution artifacts.

Next focus:

Continue work on Scenario B only.

Begin TWCS (candle snapshot) analysis of real Scenario B losing trades to identify structural failure modes.

Defer strategy or guard changes until loss patterns are clearly understood via snapshot analysis.

PROJECT_STATUS.md entry — v0.8.1.24.0 (Completed)

v0.8.1.24.0 — Post-Damage VWAP Heal Escape Hatch (single narrow exception on top of v0.8.1.23.0 floor)
Status: Validated and closed
Type: Strategy/guard change (structure-first)
Core change: Added POST_DAMAGE_VWAP_HEAL_ESCAPE to allow a post-damage entry only after VWAP reclaim + 2 consecutive closes above VWAP, entry on the next bar, no new structural damage during the reclaim+confirm window, and one healed attempt per symbol/day. The strict POST_DAMAGE_ENTRY_LOCKOUT remains the default behavior.

Why: TWCS distinguished BKYI-class losers (damage → weak reclaim → no stabilization) from SLMT-class winners (damage → VWAP reclaim → multiple stable closes above VWAP → continuation). v0.8.1.24.0 tests a narrow “structure healed” exception without weakening the floor.

Validation Summary (A/B/C framework)

Versions:

A = v0.8.1.22.0 (no post-damage protection)

B = v0.8.1.23.0 (strict post-damage lockout floor)

C = v0.8.1.24.0 (floor + heal escape hatch)

Sanity days:

2025-10-23 (SLMT):

A: 1 trade → TP (+27.78)

B: 0 trades (blocked)

C: 1 trade → TP (+27.78), with explicit VWAP_HEAL_RECLAIM, VWAP_HEAL_READY, POST_DAMAGE_HEAL_ENTRY_ALLOWED logs and allow_i=confirm2_i+1.

2025-10-27 (BKYI):

A: 2 trades → 2 SL (includes BKYI same/near-same-bar failure)

C: 0 trades; BKYI remains blocked (no POST_DAMAGE_HEAL_ENTRY_ALLOWED).

Familiar ranges:

2025-10-20 → 2025-10-31:

A: 7 trades, PnL −56.18

B: 0 trades, PnL 0.00

C: 1 trade, PnL +27.78 (restores healed winner; does not re-admit loss cluster).

2025-11-03 → 2025-11-07:

A: 3 trades, PnL +21.20

B: 0 trades, PnL 0.00

C: 1 trade, PnL −35.00 (NFE). This outcome was later flagged as execution/data contaminated due to duplicate timestamps + POS_MGMT_MISMATCH (see below). Strategy logic remains structurally correct.

Key Conclusions

v0.8.1.24.0 meets the primary hypothesis:

Restores SLMT-class healed winners

Preserves BKYI-class loss suppression

Escape hatch triggers are rare and explainable.

No evidence of regression toward v0.8.1.22.0 behavior.

Known Issue Discovered During v0.8.1.24.0 Testing (Correctness)

An existing execution-correctness bug in backtester.py can contaminate outcomes when raw minute data contains duplicate timestamps:

Example: NFE 2025-11-04 had duplicate 15:05 rows with conflicting OHLC, producing POS_MGMT_MISMATCH and an unreliable same-bar SL on a hatch trade.

SLMT 2025-10-23 also shows POS_MGMT_MISMATCH.

Quantified across C runs so far: 3 trades total, 2 affected (NFE, SLMT).

Action: Fix deferred to v0.8.1.25.0 as a single-change execution-correctness version (canonicalize minute bars before evaluation + position management). v0.8.1.24.0 strategy conclusions remain valid; PnL is treated as provisional until correctness fix lands.

Next planned version: v0.8.1.25.0 — deterministic minute-bar de-duplication/canonicalization (execution correctness only).
v0.8.1.23.0 — Status Entry (PROJECT_STATUS.md)

Status: ✅ Completed and validated

Summary:
Introduced a strict post-damage entry lockout that permanently blocks all intraday entries for a symbol once structural damage occurs, regardless of day regime. This version successfully removed a dominant loss class (post-damage entries leading to same-bar or near-immediate stop-outs) across multiple sanity days, contiguous October 2025 ranges, and a December 2025 loss-heavy day.

Key findings:

Post-damage entries were confirmed as a primary source of losses.

Enforcing a structure-first lockout eliminated these losses deterministically.

The lockout is intentionally strict and also blocks some historical winners, confirming that opportunity restoration must be selective and structure-aware.

Validation performed:

Single-day A/B tests: 2025-10-23, 2025-10-27 (BKYI), 2025-12-05

Contiguous range A/B: 2025-10-20 → 2025-10-31

Additional exploratory ranges confirmed low participation under strict lockout

TWCS analysis identified a clear structural distinction between post-damage losers and rare post-damage winners

Conclusion:
v0.8.1.23.0 establishes a robust safety floor. It is not intended to be a tradable strategy by itself, but a proven loss-subtraction layer upon which controlled, TWCS-justified exceptions can be tested.

Next version:
v0.8.1.24.0 — test a narrow VWAP-heal escape hatch (VWAP reclaim + 2 confirmation closes, entry on next bar), validated against v0.8.1.22.0 and v0.8.1.23.0 across familiar and unfamiliar ranges, with mandatory TWCS review of all admitted trades.

Project Status Entry — v0.8.1.22.0 (Closed) → v0.8.1.23.0 (Planned)

v0.8.1.22.0 — Regime-scoped post-damage VWAP reclaim (hostile-only) — CLOSED

Objective: Test whether restricting POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD to hostile days improves outcomes.

Method: Time-diverse testing on identical datasets (Oct 20–31, 2025 and Dec 2–6, 2025), plus TWCS analysis.

Result: Rejected. Losses persisted on healthy days; regime scoping did not address the dominant failure class.

Key finding: The dominant loss mode is post-damage entries on healthy days, not hostile-day reclaims.

Evidence: TWCS comparison of BKYI (2025-10-27, healthy day, post-damage grind reclaim → same-bar SL) vs SLMT (2025-10-23, healthy day, no prior damage → clean TP).

Conclusion: Structural damage must override day regime. Regime-only guards are insufficient.

Next Version: v0.8.1.23.0 — Structure-first post-damage entry lockout (Planned)

Hypothesis: Once structural damage occurs for a symbol, blocking all subsequent entries that day (regardless of regime) will reduce clustered losses without removing legitimate winners.

Planned change (single structural rule): After structural damage is detected, enforce a per-symbol same-day entry lockout (no continuation exceptions in this version).

Validation plan: Strict A/B testing (A = baseline commit, B = lockout guard), sanity checks on BKYI and SLMT days, followed by October and December range runs.

Status: Ready to implement.


v0.8.1.21.0 — Regime-Level Observability (Complete)

Status: Complete and closed
Scope: Observability only (no behavior changes)

Purpose

Determine whether the POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD logic should execute on healthy trading days, or whether it should only execute on hostile days, by adding day-level telemetry that records when post-damage reclaim behavior occurs and how it performs across regimes.

What was added

A REGIME_SUMMARY block printed exactly once per trading day

Summary reconciles with:

Trade Cards

per-day results CSVs

range totals

Summary includes:

day classification (healthy / marginal / hostile)

closed trades, TP/SL, win rate, realized PnL

aggregated block counts (structural damage, post-damage reclaim, VWAP extension, marginal VWAP gate)

minutes since last structural damage at entry (explicit 60-bar lookback)

data quality indicators

No strategy logic, guard logic, or parameters were modified.

Critical clarification (current behavior)

There is no regime-level gate on POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD.

As implemented today:

On healthy days, if a post-damage reclaim candidate satisfies the guard’s internal conditions, the guard logic executes and blocks the trade.

Healthy day classification does not bypass this guard.

This version does not claim those blocked trades would have been profitable.

Evidence collected

Tested across time-diverse regimes using identical configuration:

Trap / hostile regime: 2025-12-02 → 2025-12-06

Post-damage reclaim behavior was systematically unprofitable.

Range result: -83.64 PnL (6 trades, 33% win rate).

Trend-capable regime: 2025-10-20 → 2025-10-31

Similar post-damage patterns occurred.

Outcomes were mixed (both wins and losses).

Losses were not systematic.

Conclusion enabled (not yet implemented)

POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD behavior appears necessary in hostile regimes.

Its effect on healthy days is unknown and requires direct testing.

This supports running an experiment where the guard does not execute on healthy days.

Next step

v0.8.1.22.0 will introduce a single behavior change:

Guard executes on hostile days only

Guard does not execute on healthy days

No other logic changes

This change will be evaluated using the same December and October ranges.
v0.8.1.20.0 — Trade Card Completion (Observability Milestone)

Completed Trade Card implementation with truthful, diagnostic output (ASCII-only).

Trade Cards now expose:

accurate position & risk context (risk_usd, risk/share, qty)

realized Day PnL before trade (scenario-level)

truthful guard status (no hardcoded values)

post-damage diagnostics (last damage time, minutes since damage, block counts)

exit diagnostics (TP/SL reason, R-multiple, bar evidence)

hold time in minutes and bars

data-quality flags (duplicate timestamps, position mismatch, missing 1s data)

Verified accounting correctness:

Trade Card PnLs reconcile to per-day and range totals.

Winrate and totalPnL calculations confirmed correct.

No trading logic changes in this version.

Results observed (unchanged behavior):

2025-12-04: +21.29 (2W / 1L)

2025-12-05: −104.93 (0W / 3L)

Range: −83.64, 33.33% winrate

Outcome: losses are now explainable without TWCS or raw logs.

Next step: v0.8.1.21.0 to add day-level regime measurement (REGIME_SUMMARY) to evaluate whether the post-damage guard should be regime-gated.

Project Status Update — v0.8.1.18.0 (Closed)
v0.8.1.19.0 — Post-Damage Weak VWAP Reclaim Guard
Implemented a narrow guard to block late, weak VWAP reclaims after structural damage on healthy days.
A/B testing showed clear improvement on December trap-heavy days (e.g., 2025-12-04), with TWCS-confirmed loss removal.
Regression testing across October and November showed modest PnL regression without new failure modes, indicating regime sensitivity.
The guard is retained as a loss-subtraction mechanism; momentum-exhaustion losses at extended highs remain out of scope.
Added human-readable console TRADE CARD output at entry and exit, showing symbol, scenario, rules applied, risk calculation, exact settings, and realized PnL.
This improves on-screen validation and regression review without changing trading logic.

v0.8.1.18.0 completed an analysis-only investigation into December 2025 losses in Scenario B using TWCS-based evidence. The analysis confirmed that December losses occur on healthy-classified days (close_gt_vwap_cnt ≥ 2), ruling out marginal-day participation as the primary cause.

TWCS review identified two distinct failure classes:

Primary (dominant): post-damage weak VWAP reclaims — entries taken after intraday structural damage where the VWAP reclaim is late and lacks real continuation (confirmed via WHLR 2025-12-05 and PLRZ 2025-12-04).

Secondary (non-dominant): momentum exhaustion at highs — late-in-leg continuation entries that immediately stall or reject (confirmed via JFBR and PAVS on 2025-12-05).

The primary loss driver is structural and repeatable, making it a valid target for loss subtraction. Version v0.8.1.18.0 is now closed with sufficient evidence to proceed.

Next version: v0.8.1.19.0 — introduce a single, narrow guard to reject weak VWAP reclaims occurring after structural damage on otherwise healthy days. Momentum exhaustion handling is explicitly out of scope for the next version.

Project Summary — v0.8.1.16.0 (Closed)
v0.8.1.17.0 — Regime Participation Policy Test (Negative Result)

This version tested whether December 2025 loss clustering in Scenario B was caused by over-participation on marginal days, using a stop-after-1-loss policy applied only when close_gt_vwap_cnt == 1. The policy was implemented safely, with full observability and baseline parity confirmed. Extensive December testing (Dec 2–6, Dec 1–20 scan, and multiple single-day classifications) showed that all loss clusters occurred on healthy-classified days (close_gt_vwap_cnt ≥ 2). Marginal days either produced no trades or did not exhibit loss clustering. Conclusion: marginal-day over-participation is not the dominant December failure mode; the hypothesis is rejected. No guards were added, removed, or modified.

v0.8.1.16.0 conclusively tested whether a “late VWAP re-push after stall” executed-loss pattern recurred frequently enough to justify a new guard. Across targeted November ranges and loss-dense December stress tests (8+ SL trades reviewed), no additional occurrences were found beyond the original two cases. The pattern is rare and non-systematic; no entry logic changes or new guards are justified. Losses are driven by regime conditions rather than structural entry flaws. The project now advances to v0.8.1.17.0 to address regime-aware trade frequency control as the next highest-impact improvement.
v0.8.1.15.0 — Executed-Loss Diagnosis (No Code Changes).
This version performed a rigorous, TWCS-based analysis of executed SL trades to determine whether losses were caused by failing guards or normal trade risk. Multiple loss clusters were rerun with full guard diagnostics captured (stderr → runlogs). Two distinct loss classes were identified: (A) a rare, plausible entry-structure weakness (late VWAP re-push after stall; 2 examples), and (B) structurally valid continuations that still failed (normal risk; ≥3 examples). Guard behavior was validated as correct and aggressive, with no contradictions found. No enforcement or parameter changes were made; findings are carried forward to continue diagnosis in v0.8.1.16.0.

v0.8.1.14.0 — Blocked-Trade Diagnostic Analysis (No Code Changes)

v0.8.1.14.0 analyzed the blocked-trade JSON diagnostics introduced in v0.8.1.13.0 to evaluate whether the Post-Damage VWAP Reclaim Continuation Guard was harming profitability. Historical ranges (Apr 2025, Jul 2025, Nov 2025) were re-run, and all November blocked candidates were matched against actual executed trades. Results showed that most blocks were profit-neutral, no blocked trades were demonstrated to be missed winners, and a small number of cases were undetermined but lacked evidence of harm. Conclusion: the guard appears mostly profit-neutral and remains unchanged. This version is analysis-only and is now closed.
v0.8.1.13.0 (diagnostics-only): Instrumented the post-damage VWAP reclaim continuation guard to write a tiny, best-effort JSON snapshot whenever a trade is blocked by POST_DAMAGE_CONTINUATION_BLOCK, capturing symbol, timestamp, day classification, continuation strength, structural-damage context, and guard enablement state. The change is fully behavior-neutral (no logic, thresholds, or config changes), validated on both neutral and hostile ranges, and provides the first persistent dataset for analyzing whether this guard is preventing losses or unintentionally blocking profitable trades.

v0.8.1.12.0 — Post-Damage VWAP Continuation Guard (Validated)

Status: Complete and validated (A/B tested across Aug / Oct / Nov 2025).

Summary:
Introduced a post-damage VWAP reclaim continuation requirement to block single-candle reclaims after structural damage. This removed a proven loss class while preserving all existing correct behavior.

Results:

August 2025: −1 trade, +34.96 PnL improvement

October 2025: No change (behavior preserved)

November 2025: −3 trades, +42.03 PnL improvement

Aggregate improvement across tested months: +76.99 PnL, winners preserved, no regressions.

Conclusion:
Loss subtraction behaved exactly as intended. The system is now in late-stage loss subtraction, with remaining losses becoming more heterogeneous.

Next Version:
v0.8.1.13.0 — diagnostics-only release to add blocked-candidate visibility (TWCS-lite) without changing trading behavior.

<!-- BEGIN INSERT: PROJECT_STATUS v0.8.1.11.0 LATEST COMPLETED VERSION -->

## Latest Completed Version: v0.8.1.11.0 — Windowed Marginal VWAP Acceptance (Selective Delay)

### Purpose
Refine marginal-day VWAP acceptance from **hard suppression** to **selective delay**, so early 09:30 marginal junk is still blocked while **legitimate delayed VWAP continuations** are restored.  
This version is a **correctness and stability refinement**, not a profitability upgrade.

---

### What Changed (Software)
- **Single-file change only:** `src/midas_v2/engine/backtester.py`
- Replaced strict marginal requirement (“i-2 AND i-1 must both be above VWAP”) with a **windowed acceptance rule** (“2 of last 3 completed candles”).
- Behavior:
  - Early marginal attempts are **delayed**, not permanently suppressed.
  - Later valid continuations may proceed once acceptance forms.
- Added explicit observability:
  - `MARGINAL_VWAP_GATE v0.8.1.11.0: enabled=True`
  - Structured log-once rejection:
    - `MARGINAL_VWAP_WINDOW_REJECT`
    - Includes hits, representative bar index, close, and VWAP.
- **No config changes, no helpers, no refactors, no changes to exits/TP/SL/sizing.**

---

### Validation (A/B) — Sanity Range
**2025-08-04 → 2025-08-08 (Scenario B)**

- A (v0.8.1.10.0):  
  Trades=3, Win%=66.67%, PnL=+20.87
- B (v0.8.1.11.0):  
  Trades=3, Win%=66.67%, PnL=+20.87

Result: **Identical behavior; no regression.**

---

### Validation (A/B) — Full Month Ranges (Time-Diverse)

#### August 2025
- A (v0.8.1.10.0):  
  Trades=11, Win%=45.45%, PnL=−70.08
- B (v0.8.1.11.0):  
  Trades=11, Win%=45.45%, PnL=−70.08

#### October 2025 (Out-of-Sample)
- A (v0.8.1.10.0):  
  Trades=16, Win%=50.00%, PnL=−55.80
- B (v0.8.1.11.0):  
  Trades=16, Win%=50.00%, PnL=−55.80

#### November 2025 (Hostile Regime)
- A (v0.8.1.10.0):  
  Trades=21, Win%=42.86%, PnL=−167.72
- B (v0.8.1.11.0):  
  Trades=21, Win%=42.86%, PnL=−167.72

**Conclusion:** v0.8.1.11.0 is conclusively **behavior-preserving across regimes**.

---

### Marginal VWAP Gate Activity
- ~50 `MARGINAL_VWAP_WINDOW_REJECT` events per month across Aug / Oct / Nov.
- Rejects occur almost exclusively at early session times.
- No evidence of late-day over-blocking.

This confirms the change delays marginal entries without suppressing valid later trades.

---

### TWCS Findings (Dominant Remaining Loss Class)
TWCS inspection identified a repeatable loss pattern **not addressed by marginal-day logic**:

- **CYRX — 2025-08-06**
- **CNEY — 2025-05-07**

Both show:
- Prior structural damage earlier in the session.
- Later VWAP reclaim that is technically valid.
- **Only a single reclaim candle**, with no continuation.
- Immediate stall and full-stop SL.

Cameron-style interpretation:
> *“One green candle after damage is not strength.”*

---

### Conclusions
v0.8.1.11.0 successfully:
- Fixes marginal VWAP over-suppression.
- Preserves all prior correct behavior.
- Adds high-quality observability.
- Establishes a **stable, trusted baseline**.

Profitability is unchanged by design; remaining losses are now **structural and explainable**, not regime-driven.

---

### Next Planned Version (Hypothesis Only)
**v0.8.1.12.0 — Post-Damage VWAP Reclaim Continuation**

Introduce exactly one new structural guard:
- **After structural damage, require real continuation (≥2 green closes above VWAP) before entry.**

Goal: remove a proven dominant loss class (CYRX/CNEY-type trades) while preserving all existing correct behavior.

<!-- END INSERT: PROJECT_STATUS v0.8.1.11.0 LATEST COMPLETED VERSION -->

START / END markers (copy everything between)
<!-- BEGIN INSERT: PROJECT_STATUS v0.8.1.10.0 LATEST COMPLETED VERSION -->

## Latest Completed Version: v0.8.1.10.0 — Marginal VWAP Acceptance (2-bar pre-confirm)

### Purpose
Refine marginal-day trading so Scenario B only enters a marginal-day trade after VWAP acceptance has already been demonstrated by **two prior completed candles** (i-2 and i-1) that are both **green** and **closed above VWAP**, filtering “first close above VWAP” marginal junk while preserving hostile/healthy behavior.

### What Changed (Software)
- **Single-file change only:** `src/midas_v2/engine/backtester.py`
- Inserted a new marginal-day guard **between**:
  - the existing `DAY_GATE_FAILED` early-reject block, and
  - the combined entry condition that calls `strat.should_enter(bars, i)`
- Guard runs **only** when all are true:
  - `require_day_follow_through == True` (DAY_GATE enabled)
  - `close_gt_vwap_count == 1` (marginal day)
  - `day_trade_count < 1` (marginal trade still available)
  - entry otherwise eligible (`position is None`, `pending_entry is None`, `effective_day_gate_failed == False`)
- VWAP computed **incrementally (PV/V)** using `tp=(h+l+c)/3` and cumulative sums; loop bound uses `for k in range(i)` to ensure VWAP for i-1 is computed.
- Rejection uses **log-once** keying and reason:
  - `MARGINAL_VWAP_ACCEPT_FAIL`
  - then `continue` (skip entry attempt)
- **No config changes, no helpers, no refactors, no changes to exits/TP/SL/sizing.**

### Validation (A/B) — April 2025
**A (v0.8.1.9.0 baseline)**
```powershell
cd "C:\Users\boydp\Desktop\version v0.8.1.9.0"; python scripts\run_range_and_summarize.py --start 2025-04-01 --end 2025-04-30 --scenario B *>&1 | Tee-Object -FilePath ".\out\auto\B_runlog_20250401_20250430_A_v0.8.1.9.0.txt"


Totals: [B] trades=24, wins=10, losses=14, winrate=41.67%, totalPnL=-209.89

B (v0.8.1.10.0)

cd "C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working"; python scripts\run_range_and_summarize.py --start 2025-04-01 --end 2025-04-30 --scenario B *>&1 | Tee-Object -FilePath ".\out\auto\B_runlog_20250401_20250430_B_v0.8.1.10.0.txt"


Totals: [B] trades=17, wins=8, losses=9, winrate=47.06%, totalPnL=-91.27

Deep Dive (April) — Losses Removed by New Guard

Removed SLs present in v0.8.1.9.0 but absent in v0.8.1.10.0 (all were full-stop SLs around −35):

20250401|GRI pnl=-34.88

20250404|IBO pnl=-34.99

20250408|NAOV pnl=-34.74

20250411|BON pnl=-34.96

20250424|CNEY pnl=-34.97

Each was confirmed blocked by MARGINAL_VWAP_ACCEPT_FAIL at 09:30, and none traded later that day in v0.8.1.10.0.

Validation (A/B) — August 2025 (time-diverse cluster)

A (v0.8.1.9.0 baseline)

cd "C:\Users\boydp\Desktop\version v0.8.1.9.0"; python scripts\run_range_and_summarize.py --start 2025-08-01 --end 2025-08-31 --scenario B *>&1 | Tee-Object -FilePath ".\out\auto\B_runlog_20250801_20250831_A_v0.8.1.9.0.txt"


Totals: [B] trades=18, wins=6, losses=12, winrate=33.33%, totalPnL=-251.80

B (v0.8.1.10.0)

cd "C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working"; python scripts\run_range_and_summarize.py --start 2025-08-01 --end 2025-08-31 --scenario B *>&1 | Tee-Object -FilePath ".\out\auto\B_runlog_20250801_20250831_B_v0.8.1.10.0.txt"


Totals: [B] trades=11, wins=5, losses=6, winrate=45.45%, totalPnL=-70.08

TWCS Confirmation (Important Nuance)

TWCS confirmed JNVR 2025-04-07 was a legitimate marginal continuation (+2.0% TP; entry 10:13 → exit 10:14), but it was suppressed by the strict “i-2 AND i-1 must both be above VWAP” requirement. This validates the direction of the guard while proving the strict consecutive condition can be overly brittle.

Conclusion

v0.8.1.10.0 materially reduces marginal-day losses across regimes (April and August), primarily by blocking early 09:30 “first-VWAP-touch” marginal entries that were full-stop SLs in baseline. However, it can also suppress legitimate delayed VWAP acceptance winners, motivating a single refinement next.

Next Planned Version (Hypothesis Only)

v0.8.1.11.0 — Windowed marginal VWAP acceptance (e.g., “2 of last 3 candles”) to preserve early-loss suppression while restoring delayed acceptance winners (JNVR-type).

<!-- END INSERT: PROJECT_STATUS v0.8.1.10.0 LATEST COMPLETED VERSION -->



v0.8.1.9.0 — Marginal-Day Participation (Allow 1 Trade Max) + Strict A/B + TWCS Diagnosis
Purpose

v0.8.1.9.0 introduces exactly one profit-affecting policy change: on marginal days (where DAY_GATE produces close_gt_vwap_cnt == 1), Scenario B may take at most one completed trade for the entire day, while preserving existing behavior on:

hostile days (close_gt_vwap_cnt == 0) → still 0 trades

healthy days (close_gt_vwap_cnt >= 2) → unchanged trading behavior

This version exists to test whether marginal days sometimes contain one legitimate opportunity, without reopening hostile-day tail risk.

What Changed

Marginal-Day Trade Cap (Day-Level Policy)
Added a day-scoped counter day_trade_count and enforced:

if the day is marginal (close_gt_vwap_cnt == 1) and day_trade_count < 1, allow entry logic to proceed

once a trade finalizes (TP or SL) and day_trade_count == 1, all further entries for that day are suppressed
day_trade_count increments only at trade finalization (TP/SL), not at signal time.

Entry Enforcement Uses effective_day_gate_failed (Code Reality Fix)
Because entry was previously hard-gated behind not day_gate_failed, v0.8.1.9.0 introduced an effective_day_gate_failed override on marginal days (only while day_trade_count < 1) so the “one allowed marginal trade” is actually possible.
Hostile and healthy day behavior remains unchanged.

Observability (Log-Once, Parse-Safe)
Added / preserved log-once signals that make marginal participation auditable:

MARGINAL_DAY_ELIGIBLE when the marginal override is active

MARGINAL_DAY_TRADE_CAP_REACHED when the cap blocks further entries
Day-class summary logs remain the primary way to identify hostile/marginal/healthy days.

Log-Once Latching Correction (Minor Fix Within Version)
Separated the marginal log-once latches so MARGINAL_DAY_ELIGIBLE and MARGINAL_DAY_TRADE_CAP_REACHED can both appear independently (previously one latch could suppress the other).

Version Consistency & Scope Discipline

Only src/midas_v2/engine/backtester.py was modified. 

PROJECT_STATUS

No changes to:

strategy logic / indicators

TP/SL values

sizing / RiskManager

DAY_GATE computation rules or thresholds

existing guards (structural damage, VWAP extension, confirm-bar guard)

Validation & Evidence

Validation followed the standardized workflow using the range runner with log capture:

Healthy-day safety check (behavior preserved)
2025-07-18 (healthy, close_gt_vwap_cnt >= 2) produced identical behavior between baseline and v0.8.1.9.0.

Hostile-day safety checks (behavior preserved)
2025-07-21 and 2025-07-22 (hostile, close_gt_vwap_cnt == 0) produced 0 trades in both versions.

Wide-range A/B stress test (April 2025)
April 2025 was run as a full-month A/B range to ensure the feature activates only on marginal days and remains bounded by the 1-trade cap.

TWCS-first diagnosis (required when behavior differs)
TWCS review confirmed marginal participation can yield both:

a marginal-day SL example (GRI 2025-04-01)

a marginal-day TP example (JNVR 2025-04-07)
This established that marginal days contain both low- and high-quality opportunities, motivating a single structural refinement in the next version.

Profitability Impact (Explicit)

This version can introduce additional losses relative to baseline because it intentionally allows one trade on marginal days where the baseline often took none. The change is bounded by design (max 1 completed trade/day on marginal days).
TWCS evidence shows both upside (JNVR-type continuation) and downside (GRI-type early reclaim), so profitability improvement is not assumed; it must be verified via A/B and TWCS.

Conclusions

v0.8.1.9.0 successfully:

enabled limited marginal-day participation exactly as intended (max 1 completed trade/day)

preserved hostile-day suppression and healthy-day behavior

produced auditable logs for eligibility/cap events

demonstrated via TWCS that marginal days require an additional structural discriminator to avoid low-quality entries

Next Planned Version

v0.8.1.10.0 — Marginal-Day Entry Requires Prior Closes Above VWAP
Add exactly one structural refinement on marginal days so entries occur only after price has already closed above VWAP for multiple completed candles prior to entry, while keeping the 1-trade cap and preserving all other correct behavior.

v0.8.1.8.2 — Day-Level Diagnostics (DAY_GATE_SUMMARY) + Stability Patch

Purpose

v0.8.1.8.2 completes the diagnostic phase started in v0.8.1.8.1 by making day-level gating outcomes explicitly observable, so 0-trade days can be explained immediately and future profit-oriented policy changes can be evaluated causally.

This version is primarily observability (plus one minimal stability fix discovered during validation). It does not attempt profitability recovery.

What Changed

DAY_GATE_SUMMARY (Day-Level Observability)
Added a single day-level summary log emitted once per trading day and scenario after DAY_GATE and structural-damage auto-switch finalization and before per-symbol trading begins.
The summary includes the final day-level state used downstream, including:

enabled (require_day_follow_through)

gate_minutes, min_symbols

close_gt_vwap_cnt

require_close_gt_vwap

day_gate_failed
This makes day classification (hostile/marginal/healthy) auditable without scanning per-symbol logs.

Logging Correctness Fix (Single-Record Guarantee)
Corrected an embedded newline in the summary log format string so the DAY_GATE_SUMMARY is emitted as a single log record (parse/grep safe).

Runtime Stability Fix (Schema Drift Guard)
Fixed a discovered runtime crash:
AttributeError: 'StrategyParams' object has no attribute 'post_entry_expansion_gate'
by using a safe fallback check:
getattr(strat.p, "post_entry_expansion_gate", False)
This preserves behavior when present and fails closed when absent, preventing day-run failures.

Version Consistency & Scope Discipline

Only src/midas_v2/engine/backtester.py was modified.

No changes to:

strategy logic / indicators

entry/exit rules

TP/SL values

sizing / RiskManager logic

DAY_GATE evaluation rules or thresholds

Validation & Evidence

Validation was performed using the standardized workflow (range runner with log capture):

Single-day verification (healthy control):
python scripts\run_range_and_summarize.py --start 2025-07-18 --end 2025-07-18 --scenario B *>&1 | Tee-Object ...
Observed: healthy day classification (close_gt_vwap_cnt=3, day_gate_failed=False) and runner summary stats:
B: TP=2 SL=1 Win%=66.67

July regime observations confirmed:

close_gt_vwap_cnt=0 days are hostile (trade suppression is explainable)

close_gt_vwap_cnt=1 days are marginal (structurally distinct from hostile and a candidate for limited participation policy)

Profitability Impact (Explicit)

This version does not change strategy behavior and therefore is not a profitability upgrade.
Its value is that profitability work can now be conducted safely because day-level suppression is explicit and auditable.

Conclusion

v0.8.1.8.2 completes the day-level diagnostics milestone: every day is now classifiable via a single authoritative summary log, and validation runs are stable and auditable. This establishes the baseline needed to pursue controlled profit recovery.

Next planned version

v0.8.1.9.0 — Marginal-Day Participation Policy (A/B tested)
Introduce exactly one profit-affecting change: on marginal days (close_gt_vwap_cnt==1), allow exactly one trade (first valid signal), while leaving hostile days suppressed and healthy days unchanged. This must be validated via extensive A/B testing over wide date ranges using run_range_and_summarize.py with output logs captured for comparison.
v0.8.1.8.1 — Execution Safety & Full Rejection Observability
Purpose

v0.8.1.8.1 extends the execution correctness foundation established in v0.8.1.7.1 by addressing two remaining structural issues:

Execution-invalid entries that appear valid in bar-based backtests but would be instantly stopped in live trading.

Silent trade suppression, where trades (including entire days) were filtered without explicit explanation.

This version focuses on execution safety and explainability, not profitability.

What Changed

Confirm-Bar Stop-Violation Guard (Execution Safety)
Trades are now rejected if the confirmation candle itself violates the stop intrabar.
This prevents structurally invalid entries that cannot succeed in live execution but previously passed backtests.

Explicit EARLY_REJECT Logging (Observability)
All early trade rejections are now logged with a [WHY] EARLY_REJECT line, including:

DAY_GATE failures

Structural damage rejection

Missing VWAP conditions

Risk limits (daily loss, max trades per symbol)

Log-Once Latching
EARLY_REJECT logs are emitted once per symbol per reason per day, preventing log spam while preserving diagnostic value.

Contextual Details Added
Rejection logs include contextual fields (e.g., DAY_GATE parameters, counters, flags) using existing variables only, enabling precise diagnosis of suppression causes.

Version Consistency & Scope Discipline

All version stamps updated to v0.8.1.8.1

strategy.py was explicitly restored to its pre-version state

No strategy logic, thresholds, indicators, exits, or sizing were changed

Validation & Findings

Validation was performed across three time-diverse regimes:

April 2025 (hostile)
Low trade counts due to structural damage and confirm-bar violations — expected and correct.

July 2025 (marginal)
Zero-trade days were shown to be caused primarily by DAY_GATE (require_close_gt_vwap=True with close_gt_vwap_cnt=0), not by the confirm-bar guard.

August 2025 (healthy)
Trades remained present; DAY_GATE passed; no regression observed.

These tests confirm that:

The confirm-bar stop guard does not globally suppress trading.

DAY_GATE is the dominant trade suppressor on marginal days.

All suppression behavior is now explicit, deterministic, and explainable.

Profitability Impact (Explicit)

Profitability remains lower than desired in v0.8.1.8.1.
This is an unwanted side effect of conservative, safety-first controls introduced to ensure execution correctness and transparency — not a strategy defect or bug.

With execution correctness and observability now established, profitability recovery becomes a controlled next step, not a blind optimization exercise.

Conclusion

v0.8.1.8.1 completes the execution safety and observability phase of Midas_V2.
It establishes a trustworthy, diagnosable system state in which future profit-oriented changes can be evaluated safely and causally.

**v0.8.1.7.1 — Execution Correctness Hotfix (TP outcomes must never lose money)**

### What changed

This version is a **pure execution-correctness hotfix**.  
No strategy logic, indicators, gates, or parameters were changed.

1. **Confirm-Time TP/SL Rebase (Critical Fix)**

   * Root cause: TP/SL targets were sometimes computed at signal-time, while the actual entry price was finalized later at confirm-time (`entry = bar.c`).
   * This could produce invalid relationships (e.g. `tp < entry`) and lead to **TP-labeled trades with negative PnL**.
   * Fix:
     * TP/SL are now **recomputed at confirm-time entry creation** using `strat.targets(entry)`.
     * A `[WHY] TP_SL_REBASE` audit log records old vs new TP/SL for full traceability.
   * Outcome: TP/SL are always correctly aligned to the final entry price.

2. **Outcome ↔ PnL Invariant Enforcement (Safety Net)**

   * Added hard correctness invariants at trade close:
     * TP with `pnl < 0` → relabeled as `ERR_TP_NEG_PNL`
     * SL with `pnl > 0` → relabeled as `ERR_SL_POS_PNL`
   * PnL values are **never modified**.
   * Entry/TP/SL prices are **never rewritten** at close.
   * Any violation emits a loud `[WHY] OUTCOME_PNL_MISMATCH` log.
   * This guarantees impossible outcomes can never silently corrupt analytics again.

3. **TWCS Outcome Consistency Fix**

   * Previously, CSV results and TWCS snapshots could disagree (e.g. CSV says `ERR_*`, TWCS still shows `TP` or `SL`).
   * Fix:
     * A single `outcome` variable is now computed.
     * That same value is written to:
       * results CSV (`symbol,outcome,pnl`)
       * TWCS snapshot metadata (`outcome_label`)
   * Outcome: TWCS visuals and CSV analytics are now always consistent.

4. **Out-of-Scope Code Removal (Non-Functional Cleanup)**

   * Removed unused, Copilot-introduced helpers:
     * `SimpleTradeSummary`
     * `format_simple_trade_calcs(...)`
   * These were verified unused and out-of-scope for a correctness hotfix.
   * No runtime behavior was changed by this cleanup.

### Validation & Evidence

All validation was **human-run**, not automated.

* Structural safety:
  * Python AST parse clean
  * Exactly one `_normalize_strategy_params` definition
  * No unused helper remnants
* Known-bad days re-run under v0.8.1.7.1:
  * 2025-04-01 (ICCT)
  * 2025-08-20 (NBY)
  * 2025-08-29 (MOVE)
  * 2025-09-10 (WLDS)
* Global invariant scans across regenerated results:
  * `TP_but_negative_pnl = 0`
  * `SL_but_positive_pnl = 0`
  * `ERR_outcomes = 0`

This confirms the bug was fixed **at the source**, not masked.

### Conclusions

* **Execution correctness is now restored and trustworthy.**
* Win rate, expectancy, drawdown, and TWCS diagnostics are now analytically valid again.
* This fix is **prerequisite infrastructure** for any further profitability or strategy work.
* No further action is required for this version.

### Next planned version

**v0.8.1.8.0 — Entry Selectivity & Loss-Side Control**

* With execution correctness restored, focus returns to strategy-level loss reduction.


**v0.8.1.7.0 — Post‑Entry Expansion Confirmation + TP/SL Correctness Fix**

### What changed

1. **Post‑Entry Expansion Confirmation Gate (kept)**

   * Added a post‑entry confirmation window requiring minimum forward expansion (bps) within a short window.
   * Purpose: filter weak continuations that pass entry but fail to follow through.
   * Result: materially improved trade quality on days with momentum; reduced false positives.

2. **Critical Backtester Bug Fix (kept)**

   * Fixed TP/SL evaluation using flattened or mutated bars during position management.
   * Root cause: duplicate timestamps and/or evaluation‑stage bar mutation caused wicks to be lost.
   * Fix:

     * Preserve provider bars for TP/SL checks.
     * Duplicate‑timestamp‑safe merge that **preserves true highs/lows** (max high / min low).
     * Position management now evaluates TP/SL against wick‑correct bars.
   * Outcome: previously missed TPs (e.g., TCMD 2025‑08‑05) now correctly recorded.

### Evidence

* Re‑runs after fix show:

  * **2025‑08‑05**: TP correctly hit (TCMD).
  * **2025‑08‑06**: Multiple clean TPs.
  * Prior failure cases now behave as expected.

### Conclusions

* **Post‑entry expansion confirmation is a net positive and should remain ON.**
* **Backtester fix is correctness‑critical and must never be reverted.**
* Remaining losses are now *strategy‑related*, not data or accounting errors.

### Next planned version

**v0.8.1.8.0 — Entry Selectivity & Loss‑Side Control**

* Focus on reducing weak‑day participation rather than adding new indicators.

---

## Version History (Cumulative)

### v0.8.1.6.x — Day‑Level Gating & Structural Guards

* Introduced DAY_GATE logic to filter hostile sessions.
* Added auto‑enable structural damage guard based on day quality.
* Reduced participation on false green days.

### v0.8.1.5.x — Structural Damage Guard

* Rejected weak VWAP reclaim after significant damage.
* Guard designed to be reversible and diagnostic.

### v0.8.1.4.x — VWAP Strength & Extension Controls

* Added VWAP extension caps to avoid chasing overextended entries.
* Improved win consistency during trend days.

### v0.8.1.3.x — Stop‑Loss & Risk Tightening Experiments

* Tested SL tightening.
* Neutral to slightly negative; changes rolled back.

### v0.8.1.0.x — TWCS (Trade‑With‑Candle‑Snapshots) Foundation

* Introduced TWCS snapshots (minute + 1s context).
* Enabled visual diagnosis of failure modes.
* TWCS explicitly *diagnostic*, not a trade filter.

---

## Active Guards (See ACTIVE_GUARDS_LEDGER.md)

* Structural damage rejection (auto‑mode via DAY_GATE)
* VWAP extension cap
* Post‑entry expansion confirmation

---

## Dominant Remaining Failure Classes

* Weak momentum days still allow some low‑expectancy entries.
* Late‑day chop where expansion confirmation passes but continuation stalls.

---

## Explicitly Rejected Ideas

* Indicator stacking for its own sake
* Microstructure gates as hard filters (reserved for later diagnostic use)
* Catalyst expansion before baseline stability

---

## Guiding Principles (Permanent)

* **Structure beats indicators.**
* **Correctness before optimization.**
* **One structural change per version.**
* **TWCS validates fixes before promotion.**

---

*End of cumulative project status.*
