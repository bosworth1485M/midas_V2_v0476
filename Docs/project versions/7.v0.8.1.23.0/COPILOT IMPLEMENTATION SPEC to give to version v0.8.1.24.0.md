COPILOT IMPLEMENTATION SPEC — v0.8.1.24.0
Post-Damage VWAP Heal Escape Hatch (2-bar confirmation; enter next bar; 1 attempt per symbol/day)

High-level purpose (one sentence)
Extend v0.8.1.23.0 POST_DAMAGE_ENTRY_LOCKOUT with ONE narrow exception: after structural damage, allow a long entry only when VWAP has been reclaimed AND then proven via 2 consecutive 1-minute confirmation closes above VWAP (reclaim bar does NOT count), with no new structural-damage bars during the reclaim+confirmation window; entry is allowed only starting on the NEXT bar after the 2nd confirmation close, and only one healed attempt per symbol per day.

Scope / constraints (DO NOT VIOLATE)
- Single file only: src/midas_v2/engine/backtester.py
- No refactors, no helpers, no new modules
- No config/schema changes
- Do not change the existing structural damage definition (reuse exactly what v0.8.1.23.0 uses: red bar with body_fraction >= 0.60)
- Keep v0.8.1.23.0 POST_DAMAGE_ENTRY_LOCKOUT behavior as the default safety floor
- Add exactly ONE behavior change: the escape hatch described here
- RTH-only for this feature (ignore premarket damage/reclaim/confirmation)
- Preserve all existing correct behavior outside the escape hatch
- Deterministic + fully observable in logs

IMPORTANT CODE REALITY (MUST FOLLOW)
- The existing POST_DAMAGE_ENTRY_LOCKOUT block currently uses `continue` to skip entries. You MUST REPLACE/WRAP that lockout block so the escape hatch can override it. Do NOT add a second check later (it will never run).

Key definitions (must match exactly)
- Structural damage bar: existing definition (red and body_fraction >= 0.60).
- VWAP used for this feature (“vwap_i”):
  - Prefer vwap_i = bar.vwap if it exists and is > 0.
  - Otherwise compute vwap_i incrementally inside the per-bar loop using the same approach used elsewhere:
    typical = (bar.h + bar.l + bar.c)/3; running_pv += typical*bar.v; running_v += bar.v; vwap_i = running_pv/running_v if running_v>0 else None.
  - If vwap_i is None or <= 0, treat close_above_vwap as False for this feature (fail closed).
- VWAP reclaim bar: first RTH bar after damage_first_idx is set where close > vwap_i.
- VWAP confirmation close: an RTH bar strictly AFTER reclaim where close > vwap_i.
- Two consecutive confirmation closes: two back-to-back RTH bars after reclaim with close > vwap_i.
- Confirmation reset rule (MANDATORY): any bar with close <= vwap_i resets confirm_count=0 regardless of candle color.
- No new structural damage during reclaim+confirmation: from reclaim bar through the second confirmation bar (inclusive), there must be zero structural damage bars.
- Entry timing: allow entry only starting on the bar AFTER the second confirmation bar closes (never on reclaim bar; never on confirmation bars).
- One healed attempt per symbol/day: once an escape-hatch entry is actually taken, do not allow any additional escape-hatch entries for that symbol that day.

Where to implement (placement rules)
- Reuse the existing per-symbol v0.8.1.23.0 state: damage_first_idx, damage_first_ts, post_damage_lockout_logged, and lockout counters.
- Apply the escape hatch to BOTH entry paths:
  1) normal entry attempt path (should_enter_now-based)
  2) pending_entry confirmation path (confirmed entry)
- For both paths: if POST_DAMAGE_ENTRY_LOCKOUT would block, evaluate escape hatch; only block if escape hatch is NOT allowed.

New per-symbol state (minimal; no helpers)
Initialize once per symbol/day (near other v0.8.1.23.0 per-symbol vars):
- reclaim_idx = None
- confirm_count = 0
- heal_window_damage_seen = False
- heal_ready_idx = None   (index of the 2nd confirmation bar when heal becomes ready)
- post_damage_heal_attempt_used = False
- (for VWAP calc fallback only) running_pv = 0.0 ; running_v = 0.0

Escape hatch logic (exact, step-by-step)
This feature is relevant only after damage_first_idx is set (damage occurred earlier today).

A) Continuous tracking (must run on every bar, not only when should_enter_now is True)
On each bar i:
1) Update vwap_i for this feature:
   - If bar.vwap exists and >0, use it.
   - Else update running_pv/running_v and compute vwap_i as running_pv/running_v if running_v>0.
2) If damage_first_idx is None:
   - Do nothing for escape hatch state (keep reclaim_idx=None, confirm_count=0, heal_ready_idx=None).
3) If damage_first_idx is not None:
   - close_above_vwap = (vwap_i is not None and vwap_i>0 and bar.c > vwap_i)
   - is_struct_damage_bar_i = (bar.c < bar.o and body_fraction(bar) >= 0.60) using the existing damage definition

4) Reclaim detection:
   - If reclaim_idx is None and close_above_vwap is True:
       reclaim_idx = i
       confirm_count = 0
       heal_window_damage_seen = False
       heal_ready_idx = None

5) Track damage-in-window:
   - If reclaim_idx is not None and i >= reclaim_idx and is_struct_damage_bar_i is True:
       heal_window_damage_seen = True

6) Confirmation counting (reclaim bar does NOT count):
   - If reclaim_idx is not None and i > reclaim_idx:
       If close_above_vwap is True: confirm_count += 1
       Else: confirm_count = 0

7) Window failure and restart (MANDATORY):
   - If heal_window_damage_seen is True:
       abandon current heal window:
         reclaim_idx = None
         confirm_count = 0
         heal_window_damage_seen = False
         heal_ready_idx = None
       A new reclaim must occur to restart evaluation.

8) Heal readiness:
   - If reclaim_idx is not None AND confirm_count >= 2 AND heal_ready_idx is None:
       set heal_ready_idx = i  (this i is the 2nd confirmation bar)

B) Escape hatch decision (applies when lockout would block)
Define escape_hatch_allowed_at_i as:
- damage_first_idx is not None and damage_first_idx < i
- post_damage_heal_attempt_used is False
- heal_ready_idx is not None
- i == heal_ready_idx + 1   (entry only on next bar after proof)
- reclaim_idx is not None (should be by construction)
- heal_window_damage_seen is False

C) REQUIRED: Replace/Wrap existing lockout behavior (normal entry path)
Locate the existing v0.8.1.23.0 POST_DAMAGE_ENTRY_LOCKOUT block (it currently logs and continues).
REPLACE it with logic:
- If lockout condition is met:
    - If escape_hatch_allowed_at_i is True:
        - allow the entry attempt to proceed (do NOT continue)
        - set post_damage_heal_attempt_used = True at the moment the trade is actually taken (position created OR pending_entry created; match your flow)
        - log [WHY] v0.8.1.24.0 POST_DAMAGE_HEAL_ENTRY_ALLOWED ...
        - increment day counter post_damage_heal_entries_allowed
    - Else:
        - keep the existing lockout behavior (log-once, increment lockout counters, continue)

D) REQUIRED: Apply same logic to pending_entry confirmation path
In the pending_entry confirmation block, there is already a v0.8.1.23.0 lockout check after CONFIRM_BAR_STOP_VIOLATION.
Modify it so:
- If damage_first_idx < i and pending would confirm:
    - If escape_hatch_allowed_at_i is True:
        - allow confirmation to proceed (do NOT clear pending_entry; do NOT continue)
        - set post_damage_heal_attempt_used = True at the moment the position is created
        - log [WHY] v0.8.1.24.0 POST_DAMAGE_HEAL_ENTRY_ALLOWED ... source=pending_confirm
        - increment day counter post_damage_heal_entries_allowed
    - Else:
        - keep existing block behavior: log, counters, pending_entry=None, continue

Logging / observability (mandatory)
Add grep-friendly logs with version tags:
1) Enable log once per run:
   log.info("POST_DAMAGE_VWAP_HEAL_ESCAPE v0.8.1.24.0: enabled=True")
2) Reclaim detected (log-once per symbol/day):
   [WHY] v0.8.1.24.0 VWAP_HEAL_RECLAIM symbol=... ts=... reclaim_i=...
3) Heal ready (confirm_count hits 2; log-once per symbol/day):
   [WHY] v0.8.1.24.0 VWAP_HEAL_READY symbol=... ts=... reclaim_i=... confirm2_i=...
4) Entry allowed via escape hatch (log-once per symbol/day):
   [WHY] v0.8.1.24.0 POST_DAMAGE_HEAL_ENTRY_ALLOWED symbol=... day_class=... entry_ts=... entry_i=...
   details=reclaim_i=... confirm2_i=... allow_i=confirm2_i+1 source=normal|pending_confirm

Counters / summaries (append-only)
- Keep existing lockout counters unchanged.
- Add day_post_damage_heal_entries_allowed_total = 0 (day-level)
- Increment it each time the escape hatch actually allows an entry (normal or pending-confirm).
- Append to REGIME_SUMMARY blocks_total without renaming/reformatting existing fields.

Premarket handling (mandatory)
- Escape hatch tracking is RTH-only. Do not let premarket bars set reclaim_idx/confirm_count/heal_ready_idx.

Validation instructions (human; no code)
Testing must be run in three versions on identical ranges:
- v0.8.1.22.0 baseline
- v0.8.1.23.0 strict lockout
- v0.8.1.24.0 escape hatch
Required checks:
- BKYI 2025-10-27 remains blocked (escape hatch must NOT allow it)
- SLMT 2025-10-23 is allowed ONLY if reclaim + 2 confirmations occur and entry is on the next bar
- Same-bar and next-bar stop-outs must not increase vs v0.8.1.23.0; if they do, reject

END SPEC
