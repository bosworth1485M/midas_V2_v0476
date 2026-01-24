BEGIN COPILOT IMPLEMENTATION SPEC — v0.8.1.21.0 — “REGIME_SUMMARY telemetry (observability-only, no behavior change, DO NOT RUN)”

IMPORTANT: DO NOT EXECUTE ANY COMMANDS
- Do not run range runner, backtests, or any Python commands.
- Only modify code as specified and stop.

Version intent (one sentence)
- Add a single end-of-day REGIME_SUMMARY line so we can decide if the v0.8.1.19.0 post-damage guard should be regime-gated using simple, explainable signals.

Scope / Files
- Primary edit: src/midas_v2/engine/backtester.py
- Do NOT touch strategies, configs, scenarios, runners, or risk manager.

Non-negotiable constraints
- Observability only. Do NOT change:
  - entry/exit decisions
  - guard logic or thresholds
  - sizing
  - TP/SL
  - max trades per symbol
- No refactors. Keep code changes minimal and local.

Background
- v0.8.1.20.0 Trade Cards now expose per-symbol:
  - last_damage_ts, last_damage_idx
  - count_struct_damage_blocks
  - count_post_damage_weak_reclaim_blocks
  - count_vwap_ext_blocks
  - count_marginal_vwap_gate_blocks
  - minutes_since_damage_at_entry (computed for executed trades)
- We need a day-level summary that aggregates these so regime gating can be evaluated without manual scanning.

What to implement

A) Aggregate telemetry across symbols (per day)
1) Ensure per-symbol telemetry objects already exist (from v0.8.1.20.0).
2) Create per-day aggregator variables (reset at start of each trading day / day run):
   - day_struct_damage_blocks_total = 0
   - day_post_damage_weak_reclaim_blocks_total = 0
   - day_vwap_ext_blocks_total = 0
   - day_marginal_vwap_gate_blocks_total = 0
   - day_dup_ts_total = 0
   - day_pos_mgmt_mismatch_total = 0
   - day_missing_1s_total = 0
   - day_trades_executed = 0
   - day_trades_tp = 0
   - day_trades_sl = 0
   - day_minutes_since_damage_at_entry_list = []  (ints only)
   Add inline comment “v0.8.1.21.0” near these initializations.

3) At the end of processing each symbol, add that symbol’s telemetry to the day totals:
   - day_struct_damage_blocks_total += telemetry["count_struct_damage_blocks"]
   - day_post_damage_weak_reclaim_blocks_total += telemetry["count_post_damage_weak_reclaim_blocks"]
   - day_vwap_ext_blocks_total += telemetry["count_vwap_ext_blocks"]
   - day_marginal_vwap_gate_blocks_total += telemetry["count_marginal_vwap_gate_blocks"]
   - day_dup_ts_total += telemetry["dup_ts_count"]
   - day_pos_mgmt_mismatch_total += (1 if telemetry["pos_mgmt_mismatch_occurred"] else 0)
   - day_missing_1s_total += (1 if telemetry["missing_1s_csv"] else 0)
   Add inline comment “v0.8.1.21.0”.

B) Collect executed-trade “minutes since damage at entry”
We want a day-level distribution of “minutes_since_damage_at_entry” ONLY for executed trades (not blocked attempts).

1) In the entry-card printing call sites (immediate entry and confirmed entry), after minutes_since_damage_at_entry is computed (or returned), append it to day_minutes_since_damage_at_entry_list if it is an int.
- If minutes_since_damage is computed inside _print_trade_card_entry and not returned, then:
  - Compute the same minutes_since_damage_at_entry in the caller (where entry_idx and telemetry["last_damage_idx"] are available) and append it there.
- Do NOT change any logic; only compute for logging.
- Add inline comment “v0.8.1.21.0”.

2) Also increment day_trades_executed on each executed entry (in exactly one place per trade).
- Easiest: increment where a position is created or where results CSV is written for a trade.
- Ensure it increments exactly once per trade.
- Add inline comment “v0.8.1.21.0”.

C) Capture day TP/SL counts from existing exit handling
1) When a trade exits TP, increment day_trades_tp.
2) When a trade exits SL, increment day_trades_sl.
- Do this in the TP exit and SL exit sections where outcome is already known.
- Add inline comment “v0.8.1.21.0”.

D) Print a single REGIME_SUMMARY line once per day
At the very end of the day run (after all symbols processed and after results are saved), print one summary block with ASCII-only formatting.

Required format (example; exact values vary):
================================================================================
REGIME_SUMMARY v0.8.1.21.0 | date=2025-12-05 | scenario=B | class=healthy
- universe_symbols=5
- trades_executed=3 tp=0 sl=3 winrate=0.00
- day_pnl_realized=-104.93
- blocks_total: struct_damage=8 post_damage_weak_reclaim=1 vwap_ext=0 marginal_vwap_gate=0
- minutes_since_damage_at_entry: count=3 min=9 p50=12 max=114
- data_quality: dup_ts_total=0 pos_mgmt_mismatch_symbols=0 missing_1s_symbols=3
================================================================================

Implementation details
1) universe_symbols should be the count of symbols actually processed that day (after trimming).
2) day_pnl_realized should be the same value already used in summaries (realized PnL for the day).
   - Do NOT recompute from scratch if a day_pnl variable already exists; reuse it.
3) winrate = tp / trades_executed (safe divide).
4) minutes_since_damage summary:
   - Only include integers in the list.
   - Compute min and max if list non-empty.
   - Compute p50 (median) using a simple sort; no external libs required.
   - If list empty, print “count=0” and omit min/p50/max or print N/A.
5) data_quality:
   - missing_1s_symbols should count how many symbols had missing_1s_csv True (NOT number of times warning printed).
   - pos_mgmt_mismatch_symbols should count how many symbols had pos_mgmt_mismatch_occurred True.
6) ASCII only (“- ” bullets). No Unicode.

Inline version comments
- Any added/changed code must include an inline comment containing “v0.8.1.21.0”.

DO NOT RUN tests
- Do not execute any commands. User will validate via their standard range runner capture.

Acceptance criteria (user will validate)
- Running an existing day/range produces exactly one REGIME_SUMMARY block per day for scenario B.
- The REGIME_SUMMARY values match visible Trade Card telemetry and the printed day totals.
- No changes in trading outcomes, entries, exits, or CSV results.

END COPILOT IMPLEMENTATION SPEC — v0.8.1.21.0