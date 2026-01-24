COPILOT IMPLEMENTATION SPEC — v0.8.1.24.0

Post-Damage VWAP Heal Escape Hatch
(2-bar confirmation; enter next bar; 1 attempt per symbol/day)

High-level purpose (one sentence)

Extend v0.8.1.23.0 POST_DAMAGE_ENTRY_LOCKOUT with one narrow exception:
after structural damage, allow a long entry only when VWAP has been reclaimed and then proven stable via two consecutive 1-minute confirmation closes above VWAP (reclaim bar does not count), with no new structural-damage bars during the reclaim+confirmation window; entry is allowed only on the bar after the 2nd confirmation close, and only one healed attempt per symbol per day.

Scope / constraints (DO NOT VIOLATE)

Single file only: src/midas_v2/engine/backtester.py

No refactors

No helpers

No new modules

No config / schema changes

Do not change the structural-damage definition
(reuse exactly what v0.8.1.23.0 uses: red bar with body_fraction >= 0.60)

Keep v0.8.1.23.0 POST_DAMAGE_ENTRY_LOCKOUT as the default safety floor

Add exactly ONE behavior change: the escape hatch described here

RTH-only for this feature (ignore all premarket damage/reclaim/confirmation)

Preserve all existing correct behavior outside the escape hatch

Deterministic and fully observable in logs

IMPORTANT CODE REALITY (MUST FOLLOW)

⚠️ This is mandatory

The existing POST_DAMAGE_ENTRY_LOCKOUT block in v0.8.1.23.0 uses continue to skip entries.

You MUST REPLACE / WRAP that block so the escape hatch can override it.

❌ Do not add a second check later in the file

❌ Do not add a parallel guard

✅ The escape hatch must be evaluated inside the existing lockout decision

If this rule is violated, the escape hatch will never execute.

Key definitions (must match exactly)
Structural damage bar

Existing definition from v0.8.1.23.0

Red bar AND body_fraction(bar) >= 0.60

VWAP used for this feature (vwap_i)

Prefer bar.vwap if present and > 0

Else compute incrementally inside the per-bar loop using the existing style:

typical = (bar.h + bar.l + bar.c) / 3
running_pv += typical * bar.v
running_v  += bar.v
vwap_i = running_pv / running_v  if running_v > 0 else None


If vwap_i is None or <= 0, treat close_above_vwap = False

VWAP reclaim bar

First RTH bar after damage_first_idx where close > vwap_i

VWAP confirmation close

Any RTH bar strictly after reclaim where close > vwap_i

Two consecutive confirmation closes

Two back-to-back RTH bars after reclaim with close > vwap_i

Confirmation reset rule (MANDATORY)

Any bar with close <= vwap_i → confirm_count = 0
(candle color does not matter)

No new structural damage during heal window

From reclaim bar through the second confirmation bar (inclusive)

Zero structural-damage bars allowed

Entry timing

Entry allowed only on the bar AFTER the second confirmation bar

Never on reclaim bar

Never on confirmation bars

Attempt limit

One healed attempt per symbol per day

Where to implement (placement rules)

Reuse existing per-symbol v0.8.1.23.0 state:

damage_first_idx

damage_first_ts

post_damage_lockout_logged

existing lockout counters

Apply the escape hatch to both entry paths:

Normal entry attempt (should_enter_now)

Pending-entry confirmation path

If POST_DAMAGE_ENTRY_LOCKOUT would block:

Evaluate escape hatch

Block only if escape hatch is NOT allowed

New per-symbol state (minimal; no helpers)

Initialize once per symbol/day near other v0.8.1.23.0 state:

reclaim_idx = None

confirm_count = 0

heal_window_damage_seen = False

heal_ready_idx = None

post_damage_heal_attempt_used = False

VWAP fallback only:

running_pv = 0.0

running_v = 0.0

Escape hatch logic (exact, step-by-step)
A) Continuous tracking (runs on every bar)

Compute vwap_i (see definitions)

If damage_first_idx is None:

Do nothing (reset heal state)

Else:

close_above_vwap = (vwap_i is not None and vwap_i > 0 and bar.c > vwap_i)

is_struct_damage_bar_i = existing damage definition

Reclaim detection

If reclaim_idx is None AND close_above_vwap:

reclaim_idx = i

reset confirmation state

Track damage during heal window

If reclaim_idx is not None AND i >= reclaim_idx AND structural damage:

heal_window_damage_seen = True

Confirmation counting

If reclaim_idx is not None AND i > reclaim_idx:

If close_above_vwap: confirm_count += 1

Else: confirm_count = 0

Window failure (MANDATORY)

If heal_window_damage_seen:

abandon heal window

reset all heal state

Heal readiness

If confirm_count >= 2 AND heal_ready_idx is None:

heal_ready_idx = i

B) Escape hatch allowed condition

escape_hatch_allowed_at_i is True only if all are true:

damage_first_idx is not None

damage_first_idx < i

post_damage_heal_attempt_used is False

heal_ready_idx is not None

i == heal_ready_idx + 1

heal_window_damage_seen is False

C) REQUIRED: Replace / wrap existing lockout (normal entry)

If POST_DAMAGE_ENTRY_LOCKOUT would block:

If escape_hatch_allowed_at_i:

Allow entry to proceed

When trade is actually created:

post_damage_heal_attempt_used = True

increment day_post_damage_heal_entries_allowed_total

log [WHY] v0.8.1.24.0 POST_DAMAGE_HEAL_ENTRY_ALLOWED ...

Else:

Keep existing lockout behavior unchanged

D) REQUIRED: Pending-entry confirmation path

Apply identical logic when a pending entry would confirm:

If escape hatch allowed:

allow confirmation

mark attempt used

log source=pending_confirm

Else:

preserve existing block behavior

Logging / observability (MANDATORY)

Add grep-friendly logs:

Once per run:

POST_DAMAGE_VWAP_HEAL_ESCAPE v0.8.1.24.0: enabled=True


Reclaim detected (once per symbol/day):

[WHY] v0.8.1.24.0 VWAP_HEAL_RECLAIM symbol=... ts=... reclaim_i=...


Heal ready (once per symbol/day):

[WHY] v0.8.1.24.0 VWAP_HEAL_READY symbol=... reclaim_i=... confirm2_i=...


Entry allowed:

[WHY] v0.8.1.24.0 POST_DAMAGE_HEAL_ENTRY_ALLOWED symbol=... entry_i=... source=normal|pending_confirm

Counters / summaries

Preserve all existing counters

Add:

day_post_damage_heal_entries_allowed_total

Append to existing REGIME_SUMMARY totals without renaming fields

Premarket handling (MANDATORY)

Escape hatch logic is RTH-only

Premarket bars must not set reclaim / confirmation state

Validation instructions (HUMAN — NO CODE)

Run identical ranges through:

v0.8.1.22.0 — unprotected

v0.8.1.23.0 — strict lockout

v0.8.1.24.0 — escape hatch

Required checks

BKYI 2025-10-27 remains blocked

SLMT 2025-10-23 allowed only after true heal

Same-bar / next-bar SLs must not increase vs v0.8.1.23.0

HARD REJECTION CRITERIA

If any of the following occur, reject the version:

BKYI-class false reclaims reappear

Same-bar or next-bar stop-outs increase vs v0.8.1.23.0

Escape-hatch trades cannot be justified by TWCS structure

END SPEC — v0.8.1.24.0