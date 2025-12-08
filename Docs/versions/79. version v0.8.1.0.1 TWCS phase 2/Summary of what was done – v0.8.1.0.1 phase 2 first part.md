1) Summary – Midas_V2 v0.8.1.0.1

TWCS Phase 2 – Part 1 (1-Minute Candle Windows)

1. Version & Goal

Project: Midas_V2 – Cameron-style small-cap gap-and-go system.

Version: v0.8.1.0.1

Phase: TWCS Phase 2 – Part 1 (populate candles_1m in entry/exit snapshots).

Goal of this version:

Take the TWCS scaffolding from v0.8.1.0.0 (directories + metadata only) 

1. what was done this version

Populate 1-minute candle windows around each trade’s entry and exit, using the existing minute CSVs.

Keep everything non-invasive: no change to entries, exits, sizing, or PnL.

2. Files Touched in v0.8.1.0.1
2.1 New / updated module: src/midas_v2/dataio/twcs_minute_loader.py

Purpose: Provide a safe, read-only helper to load a 1-minute TWCS window for a given symbol/date/time.

Key behavior:

Public API:

def load_twcs_minute_window(
    symbol: str,
    date_str: str,
    target_time_str: str,
    window_before: int = 10,
    window_after: int = 0,
    csv_root: Path | None = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:


CSV source:

Defaults to: data/samples/sample_{date_str}_{symbol}.csv
e.g. data/samples/sample_2025-08-01_MWYN.csv.

Time parsing:

Handles:

Full datetimes like YYYY-MM-DD HH:MM[:SS]

ISO strings like YYYY-MM-DDTHH:MM:SS[Z]

Time-only strings "HH:MM" (e.g. 09:30) by combining with date_str → YYYY-MM-DD HH:MM.

All timestamps are normalized to naive datetimes (no tzinfo) so they compare cleanly to entry/exit times.

Window rules (Phase 2, Part 1 defaults):

window_before = 10, window_after = 0

For entry:

Bars from target - 10 minutes up to target inclusive.

For exit:

Bars from target - 10 minutes up to target inclusive.

Returned list is sorted ascending by time.

Returned structure:

candles_1m: list of dicts like:

{
  "t": "2025-08-01T10:06:00",
  "o": 1.23,
  "h": 1.30,
  "l": 1.20,
  "c": 1.28,
  "v": 123456,
  "body_pct": 0.6,
  "upper_wick_pct": 0.2,
  "lower_wick_pct": 0.2,
  "is_green": true,
  "is_doji": false,
  "idx_from_entry": 0
}


window_meta:

{
  "window_size_1m": len(candles_1m),
  "window_before_1m": window_before,
  "window_after_1m": window_after,
}


Safety:

On missing CSV, parse error, or no matching minute bar:

Logs [WARN]/[ERR] v0.8.1.0.1: ...

Returns ([], {"window_size_1m": 0, ...})

Never raises out of the helper → TWCS can’t break the backtest.

2.2 Backtester integration: src/midas_v2/engine/backtester.py

Goal: Use load_twcs_minute_window inside the existing TWCS entry/exit hooks.

Key changes:

Import:

from midas_v2.dataio.twcs_minute_loader import load_twcs_minute_window  # v0.8.1.0.1


Entry TWCS hook:

When a new position is opened and twcs_enabled is True:

We already compute:

trade_id = f"{sym}_{date_str}_{entry_time_minute}"
entry_time_iso = ...
position["trade_id"] = trade_id
position["entry_time_iso"] = entry_time_iso


Now we also call:

candles_1m, window_meta_1m = load_twcs_minute_window(
    symbol=sym,
    date_str=date_str,
    target_time_str=entry_time_iso,
    window_before=10,
    window_after=0,
)


entry_meta is built with:

"candles_1m": candles_1m,
"window_size_1m": window_meta_1m.get("window_size_1m", 0),
"window_before_1m": window_meta_1m.get("window_before_1m", 10),
"window_after_1m": window_meta_1m.get("window_after_1m", 0),
"candles_1s": [],
"indicators": {},


Then twcs.save_entry_snapshot(snapshot_dir, entry_meta) as before.

All wrapped in try/except so TWCS failures cannot affect trading.

Exit TWCS hooks (TP & SL):

On exit (TP or SL), with twcs_enabled:

We compute:

raw_trade_id = position.get("trade_id") if isinstance(position, dict) else None
exit_time_iso = bar.ts

# v0.8.1.0.1: Normalize trade_id_for_twcs for exit snapshots.
if raw_trade_id:
    trade_id_for_twcs = str(raw_trade_id)
else:
    trade_id_for_twcs = f"{sym}_{date_str}_{exit_time_iso.replace(':', '')}"


This trade_id_for_twcs is used both for:

twcs.build_snapshot_dir(...)

exit_meta["trade_id"]

We call:

candles_1m_exit, window_meta_1m_exit = load_twcs_minute_window(
    symbol=sym,
    date_str=date_str,
    target_time_str=exit_time_iso,
    window_before=10,
    window_after=0,
)


exit_meta includes:

"candles_1m": candles_1m_exit,
"window_size_1m": window_meta_1m_exit.get("window_size_1m", 0),
"window_before_1m": window_meta_1m_exit.get("window_before_1m", 10),
"window_after_1m": window_meta_1m_exit.get("window_after_1m", 0),
"candles_1s": [],
"indicators": {},
"mfe": mfe_value,
"mae": mae_value,
"pnl_raw": pnl_raw,
"pnl_pct": pnl_pct,
"outcome": outcome_label,


Again, all inside try/except → no impact on trading behavior.

3. Validation – What We Ran & What We Saw

Command:

python scripts\run_range_and_summarize.py --start 2025-08-01 --end 2025-08-01 --scenario B


Output:

Same trades (MWYN, NAMM, BTAI, PHLT entry-only) and same PnL as pre-TWCS runs.

Snapshot files created under:

out\20250801\B\<SYMBOL>\snapshots\<TRADE_ID>\
    trade_snapshot_entry_meta.json
    trade_snapshot_exit_meta.json  (for trades with exits)


Example: MWYN entry snapshot:

candles_1m: 11 bars from 09:56 → 10:06 (10 minutes before + entry bar).

idx_from_entry: -10 .. 0, with 0 at the entry bar.

Geometry & flags: body_pct, upper_wick_pct, lower_wick_pct, is_green, is_doji all populated sensibly.

Example: MWYN exit snapshot:

candles_1m: 11 bars from 09:59 → 10:09 (10 minutes before + exit bar).

idx_from_entry: -10 .. 0, with 0 at the exit bar.

pnl_raw, pnl_pct, outcome unchanged vs pre-TWCS runs.

Conclusion: v0.8.1.0.1 successfully adds 1-minute TWCS windows without altering strategy behavior.

4. Git Commands for v0.8.1.0.1

When you’re happy with tests, you can tag and push:

git add -A
git commit -m "v0.8.1.0.1: TWCS Phase 2 Part 1 (1m windows for entry/exit snapshots)"
git tag -a v0.8.1.0.1 -m "v0.8.1.0.1: TWCS Phase 2 Part 1 complete"
git push
git push --tags