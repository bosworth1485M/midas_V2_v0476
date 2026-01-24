COPILOT IMPLEMENTATION SPEC for v0.8.1.23.0
Title: Structure-first post-damage entry lockout (per-symbol, same-day) — Option 1 (strict)

HIGH-LEVEL PURPOSE (one sentence)
- Once structural damage is detected for a symbol intraday, block ALL subsequent entries for that symbol for the rest of the day (regardless of day_class).

SINGLE BEHAVIOR CHANGE (ONLY)
- Add a new guard: POST_DAMAGE_ENTRY_LOCKOUT.
- If structural damage has occurred earlier in the day for a symbol, any later entry attempt for that symbol must be rejected (no continuation exceptions in this version).

FILE SCOPE (HARD)
- Modify ONLY: src/midas_v2/engine/backtester.py
- No other files, no configs, no scripts.

ABSOLUTE PROHIBITIONS (HARD)
- Do NOT add imports.
- Do NOT refactor or reorder large blocks.
- Do NOT change existing guards, thresholds, sizing, TP/SL, strategy logic, or scenario defaults.
- Do NOT change any existing log messages except by adding NEW log lines for this guard.
- If you cannot comply exactly, STOP and make no changes.

WHERE TO IMPLEMENT (ANCHORS YOU MUST USE)
In run_backtest(), inside the per-symbol loop and per-bar loop where entry decisions are made.

1) Locate the existing “structural damage” detection logic that sets telemetry keys:
   - telemetry["last_damage_idx"]
   - telemetry["last_damage_ts"]
   and/or logs like:
   - "STRUCT_DAMAGE v0.8.1.4.0: detected"
   This logic already defines the project’s structural damage candle rule.

2) Locate the section where entry conditions are computed once and reused:
   - should_enter_now = strat.should_enter(bars, i)
   - allow_new_trade_now = risk.allow_new_trade()
   and then later:
   - if (not effective_day_gate_failed) and position is None and pending_entry is None and should_enter_now and allow_new_trade_now:
     (final entry / pending-entry creation)

Your new guard must be inserted AFTER should_enter_now / allow_new_trade_now are computed, and BEFORE the final entry block that would create pending_entry or position.

DATA MODEL / STATE (MINIMAL)
Add per-symbol state variables initialized once per symbol (just after telemetry is created for that symbol):
- damage_seen = False
- damage_first_idx = None
- damage_first_ts = None
- damage_lockout_logged = False  (log-once latch per symbol/day)

How to update damage_seen:
- Each time structural damage is detected (using the existing structural damage rule), set:
  - if not damage_seen: damage_seen=True and record first idx/ts
  - Always keep telemetry["last_damage_idx"] / ["last_damage_ts"] as-is if already used.

Important: Do NOT create a new structural damage detector. Reuse the same condition already used for STRUCT_DAMAGE / telemetry["last_damage_*"].

NEW GUARD: POST_DAMAGE_ENTRY_LOCKOUT v0.8.1.23.0 (STRICT)
When evaluating an entry attempt (i.e. before entering, while position is None and pending_entry is None):

IF:
- damage_seen is True
AND
- should_enter_now is True
AND
- allow_new_trade_now is True
AND
- position is None
AND
- pending_entry is None

THEN:
- Block the entry attempt immediately (continue loop).
- Emit ONE warning log per symbol/day (log-once), with:
  - version tag v0.8.1.23.0
  - reason POST_DAMAGE_ENTRY_LOCKOUT
  - symbol
  - candidate ts (bar.ts)
  - day_class
  - damage_first_ts / damage_first_idx
  - last_damage_ts / last_damage_idx (from telemetry if present)

Example (exact wording may vary but MUST contain these fields):
[WHY] v0.8.1.23.0 POST_DAMAGE_ENTRY_LOCKOUT symbol=BKYI ts=11:17 day_class=healthy damage_first_ts=11:12 damage_first_idx=... last_damage_ts=... last_damage_idx=...

Telemetry counter:
- Add (or extend) telemetry dict with:
  telemetry["count_post_damage_entry_lockout_blocks"] = 0
- Increment it each time the guard blocks an entry attempt.

Also add a per-day aggregator similar to existing REGIME_SUMMARY totals:
- day_post_damage_entry_lockout_blocks_total (initialize before symbol loop)
- after each symbol finishes, accumulate:
  day_post_damage_entry_lockout_blocks_total += telemetry["count_post_damage_entry_lockout_blocks"]
- include it in REGIME_SUMMARY output under blocks_total (add field, do not remove existing fields).

IMPORTANT: This guard is independent of day_class. It must apply even on healthy days, which is the point of the version.

NO CONTINUATION EXCEPTIONS (STRICT)
- Do NOT allow any “strong continuation” bypass in v0.8.1.23.0.
- Any post-damage entry is blocked.

ACCEPTANCE CHECK (MUST PASS)
- Diff is confined to backtester.py.
- No new imports.
- Existing behavior remains unchanged when no structural damage occurs.
- When damage occurs before an entry attempt, the entry attempt is blocked with one [WHY] log line (log-once per symbol/day).
- SLMT-style winner that occurs without prior damage remains allowed.
- BKYI-style loser that enters after prior damage is blocked.

A/B VALIDATION PLAN (YOU run; not Copilot)
Baseline (A):
- Commit: 1e48efb

B (this version):
- After Copilot edits, commit as v0.8.1.23.0

Step 1: Sanity days (small set)
- 2025-10-23 (SLMT winner) — must still trade
- 2025-10-27 (BKYI loser day) — post-damage entry should be blocked with POST_DAMAGE_ENTRY_LOCKOUT log
- 2025-12-05 (Dec hostile day) — confirm behavior/logging

Step 2: Range tests (time-diverse)
- Oct: 2025-10-20 -> 2025-10-31, scenario B
- Dec: 2025-12-02 -> 2025-12-06, scenario B

Commands (example)
python scripts\run_range_and_summarize.py --start 2025-10-20 --end 2025-10-31 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251020_20251031_v0.8.1.23.0.txt
python scripts\run_range_and_summarize.py --start 2025-12-02 --end 2025-12-06 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251202_20251206_v0.8.1.23.0.txt

END COPILOT IMPLEMENTATION SPEC