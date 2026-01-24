COPILOT RESTORE SPEC — Reapply v0.8.1.23.0 POST_DAMAGE_ENTRY_LOCKOUT exactly (no other changes)

Goal
Recreate exactly the v0.8.1.23.0 behavior change in src/midas_v2/engine/backtester.py:
Once structural damage occurs for a symbol intraday, block all subsequent entries for that symbol that day (regardless of regime), including BOTH entry paths (normal entry attempt and pending_entry confirmation). Add enable log, WHY logs, and append-only day summary counter.

Scope / constraints
- Single file only: src/midas_v2/engine/backtester.py
- No refactors, no helpers, no new modules
- No config changes
- Do not modify existing guards other than inserting this new guard
- Do not change the structural damage definition already used in the file: red bar with body_fraction >= 0.60
- Must apply to BOTH entry paths: normal should_enter path and pending_entry confirmation path
- Must be deterministic and loggable
- Add version-tagged inline comments near new code: v0.8.1.23.0

Required behavior
A) Continuous per-symbol damage tracking (RTH bars):
- For each symbol, track damage_first_idx and damage_first_ts as the FIRST bar index/time where a structural damage bar occurs.
- Structural damage bar is: bar.c < bar.o AND body_fraction >= 0.60 where body_fraction = abs(c-o)/max(h-l,1e-9)
- This tracking must run continuously each bar, even if no entry is being considered.

B) Entry lockout (hard gate)
- If damage_first_idx is not None AND damage_first_idx < i, then block any entry attempt for that symbol at bar i, regardless of day_class.
- Must block in BOTH places:
  1) normal entry attempt path (where should_enter_now/allow_new_trade_now are used)
  2) pending_entry confirmation path (inside confirmed branch before position is created)

C) Timing rule
- Post-damage means strictly after damage: block only if damage_first_idx < i (do not block when damage_first_idx == i).

D) Logging
1) At run start add:
   log.info("POST_DAMAGE_ENTRY_LOCKOUT v0.8.1.23.0: enabled=True")

2) When blocking (log once per symbol per day):
   log.warning("[WHY] v0.8.1.23.0 POST_DAMAGE_ENTRY_LOCKOUT symbol=... day_class=... entry_ts=... entry_i=... damage_ts=... damage_i=... source=normal|pending_confirm")
   Use a per-symbol-per-day latch so it doesn’t spam.

E) Counters / summaries (append-only)
- Add per-symbol telemetry counter:
  telemetry["count_post_damage_entry_lockout_blocks"] += 1
  (initialize this key in the telemetry dict)
- Add a day-level counter:
  day_post_damage_entry_lockout_blocks_total = 0
  increment it each time the lockout blocks an entry (normal or pending_confirm).
- Append the day total to REGIME_SUMMARY blocks_total without changing existing keys/format:
  add post_damage_entry_lockout=<value> to the same blocks_total line (append-only).

Placement instructions (do NOT get wrong)
1) Enable log: place near the other guard enable logs at the top of run_backtest (where STRUCT_DAMAGE/CONFIRM_BAR_GUARD/MARGINAL_VWAP_GATE logs exist).

2) Per-symbol init: inside the symbol loop (for sym in symbols), initialize:
   damage_first_idx = None
   damage_first_ts = None
   post_damage_lockout_logged = False

3) Continuous damage tracking: inside the per-bar loop, early (before entry logic), update damage_first_idx/ts when first damage is seen.

4) Pending_entry confirmation block: in the confirmed==True path, AFTER CONFIRM_BAR_STOP_VIOLATION check and BEFORE qty/position is created, insert lockout check:
   if damage_first_idx is not None and damage_first_idx < i:
       log (source=pending_confirm) once per symbol/day
       increment telemetry counter and day counter
       pending_entry = None
       continue

5) Normal entry attempt path: right before the code would proceed to create pending_entry/position (after should_enter_now is computed and entry eligibility checks), add lockout check:
   if damage_first_idx is not None and damage_first_idx < i:
       log (source=normal) once per symbol/day
       increment telemetry counter and day counter
       continue

Do not change any other logic.
Do not modify existing formatting or logs beyond these additions.

End spec
