Active Guards Ledger
Midas_V2 — Authoritative Reference

Purpose
This ledger documents all currently active structural guards in Midas_V2 so that any future run can be understood, debugged, or A/B tested without reverse-engineering logs or code.

Only guards that are still relevant and present in the codebase are included.
Historical experiments and permanently disabled ideas are intentionally excluded.

🧠 Mental Model (Read This First)

Think of the system in layers:

DAY_GATE → Should we trade today at all?

Structural Guards → Is this setup structurally valid?

Safety / Location Guards → Is this too late or too stretched?

Entry Logic → Do indicators permit entry?

When something looks wrong, always debug top-down in this order.

Guard 1 — Day Follow-Through Gate (DAY_GATE)
What It Does

Determines whether the entire trading day is eligible based on early follow-through across the universe.

If insufficient early strength is detected, no trades are allowed for the day.

Why It Exists (Failure Class)

Prevents trading on:

choppy days

low-continuation days

“nothing is really working” environments

When It Should Be ON

Always ON

This is a core regime filter, not an experimental guard

Example Log Snippets

PASS

DAY_GATE: CHECK enabled=True minutes=20 min_symbols=2 universe=5
DAY_GATE: RULE_COUNTS total=2 close_gt_vwap=1 green_body=1
DAY_GATE: PASSED symbols=2


FAIL

DAY_GATE: CHECK enabled=True minutes=20 min_symbols=2 universe=5
DAY_GATE: RULE_COUNTS total=1 close_gt_vwap=0 green_body=1
DAY_GATE: FAILED symbols=1 reason=insufficient_follow_through


Interpretation

If you see FAILED ... insufficient_follow_through, a 0-trade day is expected and healthy.

Known Side Effects

Entire days with zero trades

Reduced activity in sideways markets

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

Treated as a safety / location guard

How to Toggle

Config key: vwap_extension_gate

Companion key: vwap_extension_max_pct

Example Log Snippets

Check only

[WHY] v0.8.1.1.0 VWAP_EXT: CHECK symbol=LZ time=10:14 entry_price=11.6208 vwap=11.2775 dist_pct=3.04 max_pct=1.5


Blocked

[WHY] v0.8.1.1.0 VWAP_EXT: BLOCKED symbol=LZ time=10:14 entry_price=11.6208 vwap=11.2775 dist_pct=3.04 max_pct=1.5 reason=overextended


Allowed

[WHY] v0.8.1.1.0 VWAP_EXT: CHECK symbol=MRM time=11:39 entry_price=1.7350 vwap=1.9770 dist_pct=-12.24 max_pct=1.5

Known Side Effects

Fewer late-session trades

Missed participation in extreme momentum spikes

Guard 3 — Structural Damage / Weak VWAP Reclaim Guard

(introduced in v0.8.1.4.0)

What It Does

Blocks entries that occur after significant downside structural damage unless price reclaims VWAP with acceptance.

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

How It Works (High Level)

Detects recent structural damage (large red candle)

If damage exists, requires:

last completed candle above VWAP

entry candle above VWAP

Blocks entry if acceptance is missing

When It Should Be ON

Trend-friendly regimes
(e.g. August 2025)

Days with clean early follow-through

When suppressing weak reclaims improves expectancy

When It Should Be OFF

Choppy / mean-reverting regimes
(e.g. July & September 2025)

Days with frequent fake moves and reversals

When trade suppression harms expectancy

Critical rule:
This guard is regime-dependent and must not be treated as always-ON.

How to Toggle

Config key: reject_reclaim_after_damage

Location: config/scenarios.json (Scenario B)

OFF (baseline / A-B testing):

"reject_reclaim_after_damage": false


ON (trend-friendly use):

"reject_reclaim_after_damage": true

Runtime Visibility (Mandatory)

Every run must clearly log the state, e.g.:

STRUCT_DAMAGE v0.8.1.4.0: CONFIG reject_reclaim_after_damage=true

Example Log Snippets

Damage detected

STRUCT_DAMAGE v0.8.1.4.0: detected symbol=SPRU


Blocked (weak reclaim)

STRUCT_DAMAGE v0.8.1.4.0: BLOCKED symbol=SPRU reason=weak_vwap_reclaim


Passed (accepted above VWAP)

STRUCT_DAMAGE v0.8.1.4.0: PASSED symbol=XYZ reason=accepted_above_vwap

Known Side Effects

Reduced trade count

Can block trades that work in choppy regimes

First guard to question when expectancy drops unexpectedly

What Is Not a Guard (Important)

These are entry conditions, not guards:

MACD rising

Green streak

Opening RVOL threshold

EMA / VWAP alignment

They permit entries but do not block days or classes of setups.

🧪 How to A/B Test a Guard (Standard Procedure)

Purpose
Determine whether a guard improves or harms expectancy without changing anything else.

Step 0 — Pick the Right Dates

Always test on identical dates.

Recommended sets:

Targeted failure day (e.g. Aug-08)

Small cluster (3–5 days)

One full month (only after sanity passes)

Step 1 — Run A = Guard OFF

Copilot micro-prompt

Change ONLY config/scenarios.json.
In Scenario B params, set "<GUARD_KEY>" to false.
Do not change any other keys, formatting, or scenarios.


Run

python scripts\run_range_and_summarize.py --start YYYY-MM-DD --end YYYY-MM-DD --scenario B | Tee-Object .\out\logs\A_<GUARD>_OFF.txt

Step 2 — Run B = Guard ON

Copilot micro-prompt

Change ONLY config/scenarios.json.
In Scenario B params, set "<GUARD_KEY>" to true.
Do not change any other keys, formatting, or scenarios.


Run

python scripts\run_range_and_summarize.py --start YYYY-MM-DD --end YYYY-MM-DD --scenario B | Tee-Object .\out\logs\B_<GUARD>_ON.txt

Step 3 — What to Compare (Only These)
Metric	Question
Trades	Did count collapse or normalize?
Win rate	Meaningful change?
Total PnL	Net improvement or harm?
Block logs	Is the guard firing as expected?

Do not tune during testing.

Step 4 — Interpret Results

Keep ON if:

PnL improves materially

Target failure class disappears

Trade suppression is acceptable

Keep OFF if:

PnL worsens

Guard fires constantly without benefit

Make Conditional if:

Results differ by month or regime
(e.g. v0.8.1.4.0 outcome)

Step 5 — Lock the Decision

Record outcome in Release Summary

Update this Active Guards Ledger

Do not re-litigate without new evidence

Quick Debugging Checklist

If results look wrong:

Check DAY_GATE (day may be ineligible)

Check VWAP Extension (late moves blocked)

Check Structural Damage Guard (post-damage suppression)

Ledger Status

Authoritative as of: v0.8.1.4.0

Next expected update: v0.8.1.5.0
(day/regime switch controlling Guard 3)