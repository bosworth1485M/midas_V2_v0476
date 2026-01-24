Document 4 — Active Guards Ledger (Updated)
Midas_V2 — Authoritative Reference

Authoritative as of: v0.8.1.5.0
Next planned update: v0.8.1.6.0 (DAY_GATE close_gt_vwap requirement)

Purpose

This ledger documents all currently active structural and regime guards in Midas_V2 so that any run can be understood, debugged, or A/B tested without reverse-engineering logs or code.

Only guards that are:

present in the codebase, and

relevant to current trading behavior

are included.

Historical experiments and permanently disabled ideas are intentionally excluded.

Mental Model (Read This First)

Always debug top-down:

DAY_GATE → Should we trade today at all?

Structural Guards → Is this setup structurally valid?

Safety / Location Guards → Is this too late or too stretched?

Entry Logic → Do indicators permit entry?

If results look wrong, start at layer 1.

Guard 1 — Day Follow-Through Gate (DAY_GATE)
What It Does

Determines whether the entire trading day is eligible based on early follow-through across the universe.

If insufficient early strength is detected, no trades are allowed for the day.

Why It Exists (Failure Class)

Prevents trading on:

choppy days

low-continuation environments

“nothing is really working” regimes

When It Should Be ON

Always ON

DAY_GATE is a core regime filter, not an experimental guard.

Current Behavior (v0.8.1.5.0)

A day may PASS when:

passed_symbols >= min_symbols

Passes may occur via:

close_gt_vwap

or green_body

This allows green-body-only days to be tradable.

Planned Behavior (v0.8.1.6.0)

A day may PASS only if:

existing DAY_GATE conditions are met
AND

close_gt_vwap_count >= 1

Effect:

Green-body-only days become non-tradable

At least one VWAP-accepted symbol is required

This is a day-quality upgrade, not an entry-level change.

Example Log Snippets

PASS

DAY_GATE: CHECK enabled=True minutes=20 min_symbols=2 universe=5
DAY_GATE: RULE_COUNTS total=2 close_gt_vwap=1 green_body=1
DAY_GATE: PASSED symbols=2


FAIL

DAY_GATE: CHECK enabled=True minutes=20 min_symbols=2 universe=5
DAY_GATE: RULE_COUNTS total=1 close_gt_vwap=0 green_body=1
DAY_GATE: FAILED symbols=1 reason=insufficient_follow_through

Known Side Effects

Entire days with zero trades (expected and healthy)

Reduced participation in sideways markets

Guard 2 — VWAP Extension Gate
What It Does

Blocks entries that are too far extended above VWAP, preventing late or euphoric buys.

Why It Exists (Failure Class)

Prevents:

chasing parabolic moves

buying into mean-reversion zones

late-day emotional entries

When It Should Be ON

Always ON

This is a safety / location guard, not a regime filter.

How to Toggle

Config key: vwap_extension_gate

Companion key: vwap_extension_max_pct

Example Log Snippets

Check

[WHY] v0.8.1.1.0 VWAP_EXT: CHECK symbol=LZ time=10:14 entry_price=11.6208 vwap=11.2775 dist_pct=3.04 max_pct=1.5


Blocked

[WHY] v0.8.1.1.0 VWAP_EXT: BLOCKED symbol=LZ time=10:14 entry_price=11.6208 vwap=11.2775 dist_pct=3.04 max_pct=1.5 reason=overextended

Known Side Effects

Fewer late-session trades

Missed participation in extreme momentum spikes

Guard 3 — Structural Damage / Weak VWAP Reclaim Guard

(introduced v0.8.1.4.0)

What It Does

Blocks entries after significant downside structural damage unless price reclaims VWAP with acceptance.

Prevents false strength entries where indicators pass but structure is already broken.

Why It Exists (Failure Class)

Derived from TWCS diagnosis of:

SPRU — 2025-08-08 @ 11:14

Pattern:

strong red displacement (true damage)

green candles follow but never accept above VWAP

entry occurs anyway → fast loss

Key insight:

Green candles after damage are not strength unless VWAP is reclaimed with acceptance.

How It Works (High-Level)

Detects recent structural damage (large red candle)

If damage exists, requires:

last completed candle above VWAP

entry candle above VWAP

Blocks entry if acceptance is missing

When It Should Be ON

Trend-friendly regimes (e.g. August 2025)

Days with clean early follow-through

When suppressing weak reclaims improves expectancy

When It Should Be OFF

Choppy / mean-reverting regimes (e.g. May, July, September)

Days with frequent fake moves and reversals

When trade suppression harms expectancy

Critical rule:
This guard is regime-dependent and must not be treated as always-ON.

How It Is Controlled (v0.8.1.5.0)
Base config (Scenario B)
"reject_reclaim_after_damage": false

Day-level auto-switch
"auto_struct_damage_from_day_gate": true


Auto-enable rule:

DAY_GATE passes
AND

close_gt_vwap_count >= 1

Runtime Visibility (Mandatory)

Every run logs:

STRUCT_DAMAGE v0.8.1.5.0: CONFIG
base=<true/false>
auto_mode=<true/false>
day_gate_pass=<true/false>
close_gt_vwap_cnt=<int>
effective=<true/false>
reason=<string>

Known Side Effects

Reduced trade count on strong days

Can block trades that work in hostile regimes
→ First guard to question when expectancy drops unexpectedly

What Is Not a Guard (Important)

These are entry conditions, not guards:

MACD rising

Green streak

Opening RVOL threshold

EMA / VWAP alignment

They permit entries but do not block days or setup classes.

Standard Guard A/B Testing Procedure (Locked)

Pick identical dates (target failure day → small cluster → month)

Run A = guard OFF (config only)

Run B = guard ON (config only)

Compare:

trades

win rate

total PnL

block logs

Record outcome in:

Release Document

This Active Guards Ledger

Do not re-litigate without new evidence

Ledger Status

Authoritative as of: v0.8.1.5.0

Next planned change:

v0.8.1.6.0 — DAY_GATE requires close_gt_vwap_count >= 1