Cameron Alignment Plan

Project: Midas\_V2
Status: Authoritative Strategy Document
Created: v0.8.1.26.0 planning phase
Purpose: Prevent strategic drift and explicitly align Midas\_V2 with the behavior of the most successful Cameron-style trading projects.





Addition jan 21 2026



Definition: Ascending Green Candle Continuation



In this project, “green candle continuation” means ascending green candles on intact structure, not merely the presence of green candles.



A valid continuation requires that:



Each qualifying candle is green (close > open) and has a real body (meets green\_body\_min).



The sequence of candles is ascending:



each candle closes higher than the previous one, and



lows do not overlap downward.



All candles in the sequence belong to the same continuous price structure.



Any structural damage (e.g., major red displacement or breakdown) resets the continuation count; green candles occurring after damage do not qualify until structure is rebuilt.



Trades are permitted only when this ascending continuation is present.



This does not change strategy intent — it simply makes explicit what successful Cameron-style trading already assumes.





1. Purpose of This Document

This document exists to lock the strategic intent of the Midas\_V2 project.

It defines:

What “successful Cameron-style behavior” means in operational terms

What Scenario B is intended to be

How future changes must be evaluated

How to prevent silent drift toward objectives that conflict with Cameron-style success

This document is not:

A changelog

A release note

A technical spec

A version thread summary

It is a navigation chart, not a logbook.

If there is ever disagreement or confusion about direction, this document is the source of truth.

2. North Star (Non-Negotiable Goal)

Midas\_V2 must emulate the behavior and outcomes of the most successful Cameron-style trading projects.

This explicitly means:

Productive participation in strong single-name momentum

Selectivity without paralysis

Risk scaling on weak tape instead of global shutdown

Structural discipline without eliminating opportunity

Any change that moves the system away from this behavior must be explicitly documented as a trade-off, not silently adopted.

3. Definition: “Successful Cameron-Style Project”

A system qualifies as “Cameron-aligned” only if it exhibits the following behaviors in practice, not just in theory.

3.1 Trade Frequency Expectations

Trades multiple times per month under normal market conditions

Does not routinely experience multi-week zero-trade periods

Accepts that some days will have zero trades, but not entire months

3.2 Tape Interaction Philosophy

Weak or mixed tape → reduced risk and/or reduced trade count

Strong tape → normal participation

Tape weakness should throttle, not silence, the system

3.3 Entry Philosophy

Strong single-name momentum can justify a trade even when the broader tape is mixed

Entry quality is prioritized over global regime purity

VWAP context, volume, and continuation strength are core signals

3.4 Loss Subtraction Philosophy

Known loss classes must be blocked

Structural damage must be respected

Loss subtraction must not eliminate participation entirely

Safety mechanisms must not become de-facto global kill switches

4. Scenario B: Canonical Intent
   4.1 What Scenario B Is Intended to Be

Scenario B is intended to be:

The primary Cameron-style baseline

A productive, disciplined momentum trader

Selective, but not inert

Structure-first, not regime-first

Scenario B is not intended to be:

A rare-event or “perfect day only” strategy

A regime-filter that trades once per quarter

A proof-of-purity system that sacrifices participation

5. Identified Strategic Drift (Root Cause)

Through multi-month empirical testing (Oct–Dec 2025), the following divergence was proven:

5.1 Observed Behavior

Scenario B frequently produced 0 trades across entire weeks and months

This occurred despite:

Clean execution

Correct data

Correct scenario wiring

5.2 Proven Root Cause

DAY\_GATE enforcement acted as a hard global kill switch

Hostile or marginal day classification triggered:

EARLY\_REJECT(DAY\_GATE\_FAILED) at 09:30

Elimination of all participation for the day

This behavior is not consistent with successful Cameron projects

This is a behavioral misalignment, not a bug.

6. Alignment Methodology (How We Fix Drift)
   6.1 One-Change-Per-Version Rule

Each version may introduce only one primary behavioral change

Bundling multiple conceptual changes is not allowed

This preserves attribution and trust

6.2 Mandatory A/B Validation

Every alignment change must be validated with:

Sanity cluster

Small window where prior behavior is clearly deficient

Protection cluster

Time-diverse window to detect regressions

Immediate TWCS review of all losses

Success must meet at least one:

≥ +3 percentage points win rate

≥ +0.2R expectancy

Profit Factor ≥ 1.2 with positive PnL delta

7. Alignment Roadmap (Authoritative)
   7.1 v0.8.1.26.0 — DAY\_GATE Realignment (Root Fix)

Type: ALIGNMENT
Hypothesis:
Scenario B under-trades because DAY\_GATE consequences enforce global shutdown. Converting DAY\_GATE from hard block to throttle will restore Cameron-like participation without reintroducing known loss classes.

Change Scope (Scenario B only):

Preserve:

Day classification logic

Follow-through detection

Telemetry and logging

Change:

Remove global EARLY\_REJECT on DAY\_GATE failure

Replace with:

Reduced max trades and/or

Reduced risk on hostile/marginal days

Explicit Non-Changes:

No MACD changes

No RVOL changes

No VWAP changes

No TP/SL changes

No refactors

Validation:

Sanity: 2025-11-18 → 2025-11-22

Protection: Older, time-diverse cluster

TWCS review of every loss

7.2 v0.8.1.27.0 — Classic B Entry Envelope (Conditional)

Type: ALIGNMENT
Precondition: Only if Scenario B still under-trades after v0.8.1.26.0

Hypothesis:
Entry-level strictness (RVOL, rise\_bars, MACD confirmation) may exceed classic Cameron baseline.

Change:

Relax exactly one entry lever

Selection based on empirical evidence from v0.8.1.26.0

7.3 v0.8.1.28.0 — Cameron-Style Trade Management

Type: ALIGNMENT
Precondition: Stable entry frequency and acceptable loss profile

Candidate Changes (one only):

Breakeven stop logic

Partial profit taking

No entry logic changes allowed in this version.

8. Explicit Guardrails

The following are not allowed without updating this document:

Silent redefinition of Scenario B purpose

Treating loss minimization as higher priority than participation

Adding global kill switches without explicit alignment justification

Recommending “leave it as-is” when behavior contradicts Cameron norms

9. Change Control Rules (Binding)

Any future recommendation must be labeled as:

ALIGNMENT – moves behavior closer to successful Cameron projects

SAFETY – blocks a proven loss class

OBSERVABILITY – explains behavior without changing it

If a recommendation improves SAFETY but degrades ALIGNMENT, that trade-off must be explicitly stated.

If guidance contradicts this document, the document must be revised first.

10. Final Statement of Intent

This document exists to ensure that:

Strategic intent is explicit

Drift is detectable

Trust is grounded in structure, not reassurance

Midas\_V2 evolves toward real Cameron-style success, not theoretical purity

If this document is followed, Scenario B will not silently become inert again.

End of Cameron Alignment Plan

