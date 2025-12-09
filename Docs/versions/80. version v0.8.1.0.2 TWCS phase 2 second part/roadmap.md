Got it — I’ll treat this as your master technical roadmap going forward.
I’ll keep it version-per-thread friendly, file-level detailed, and tightly aligned with profitability.

Below is the detailed technical roadmap for Midas_V2, from where you are now (v0.8.1.0.2) through the major phases (TWCS, UI, DB, sizing, catalyst, profitability loop).

You do not need to do all of this now — this is the long-term blueprint.

🧭 Global Principles (Always in Force)

One version per thread

v0.8.1.0.3 = one ChatGPT thread, one coherent change set.

Only fully wired features

No half-logic, no dangling flags. Each version must “close the loop”.

Use the tool stack

Copilot for Python & scripts

Claude for UI & readability passes

Local website for knobs

TWCS for candles & context

DB for analysis & profitability

Never optimize without visibility

TWCS + graphics + DB first

Filters & sizing only after you can see and measure.

🧱 Current State (v0.8.1.0.2 Recap)

TWCS entry/exit snapshots include:

candles_1m

green_streak

vwap

vwap_slope_bps

macd_hist

macd_slope

rvol_open (schema, null)

Main files touched in v0.8.1.0.2:

src/midas_v2/indicators/twcs_indicators.py (new)

src/midas_v2/engine/backtester.py (TWCS indicator wiring)

src/midas_v2/indicators/__init__.py (cleaned)

Everything is stable. TWCS indicator layer is done.

🔜 Phase 2 → Phase 3: 1-Second Candles (TWCS Phase 3)
🎯 v0.8.1.0.3 — 1-Second Loader (Data Layer Only)

Goal: Add a safe 1-second loader for TWCS (no wiring into backtester yet).

New file

src/midas_v2/dataio/twcs_second_loader.py

load_twcs_second_window(symbol, date_str, target_time_str, window_before_seconds=60, window_after_seconds=0, csv_root=None) -> (candles_1s, meta)

Responsibilities

Locate CSV:
data/samples/sample_1s_{date_str}_{symbol}.csv

Read 1s rows, filter within [target - N sec, target + M sec]

Return list of dicts:

{
  "t": "2025-08-06T09:58:07",
  "o": ...,
  "h": ...,
  "l": ...,
  "c": ...,
  "v": ...,
  "idx_from_entry": int_seconds_offset
}


On missing file, parse errors, etc:

log [WARN] v0.8.1.0.3: ...

return ([], {"window_size_1s": 0, ...})

never raise

Files touched in v0.8.1.0.3

Added:

src/midas_v2/dataio/twcs_second_loader.py

Unchanged:

backtester, scripts, indicators, UI, DB

Tests

Import module in REPL

Call load_twcs_second_window with:

existing CSV (when you later generate it)

non-existing CSV → should warn but not crash

🎯 v0.8.1.0.4 — Wire 1s into Backtester (TWCS + Snapshots Only)

Goal: Attach candles_1s to entry/exit snapshots.

Files to modify

src/midas_v2/engine/backtester.py

Changes

In entry TWCS block:

After candles_1m:

from midas_v2.dataio.twcs_second_loader import load_twcs_second_window

candles_1s, window_meta_1s = load_twcs_second_window(
    symbol=sym,
    date_str=date_str,
    target_time_str=entry_time_iso,
    window_before_seconds=60,
    window_after_seconds=0,
)


Store:

"candles_1s": candles_1s,
"window_size_1s": window_meta_1s["window_size_1s"],
"window_before_1s": window_meta_1s["window_before_1s"],
"window_after_1s": window_meta_1s["window_after_1s"],


Mirror the same logic for:

TP exit block

SL exit block

No changes

No strategy logic changes

Indicators unchanged

UI unchanged

DB unchanged

Tests

Run a single day with backtester

Confirm snapshots now include candles_1s

On days without 1s CSV: snapshots show empty list and non-zero meta, but no crashes.

🖼 Phase 3: Candle Graphics & Visual Insight
🎯 v0.8.1.0.5 — PNG Renderer for 1m/1s Windows

Goal: Generate PNGs from TWCS JSON (1m + 1s) for visual analysis.

New module

src/midas_v2/tools/plot_twcs.py

Functions

plot_twcs_window_1m(snapshot_meta, out_path: Path) -> None

plot_twcs_window_1s(snapshot_meta, out_path: Path) -> None

Inputs:

snapshot_meta: loaded from trade_snapshot_entry_meta.json or exit meta

uses:

candles_1m or candles_1s

indicators (for annotations: entry line, VWAP, etc.)

Outputs:

PNG files:

out/YYYYMMDD/B/SYMBOL/snapshots/TRADE/entry_1m.png
out/YYYYMMDD/B/SYMBOL/snapshots/TRADE/entry_1s.png
...

Minimal wiring for this version

optional script:

scripts/plot_twcs_day.py

loops over one date and scenario B

for each trade snapshot, calls plot_twcs_window_*

Files touched

Added:

src/midas_v2/tools/plot_twcs.py

scripts/plot_twcs_day.py

Unchanged:

backtester (no automatic PNG yet)

UI, DB

🎯 v0.8.1.0.6 — Optional: Auto-generate PNGs Post-Backtest

Goal: After a successful backtest run, auto-generate PNGs for all trades of that day.

Files modified

scripts/run_day_simple.py or scripts/run_range_and_summarize.py

Behavior

After backtest + summary:

Optionally call plot_twcs_day.py for that date

Controlled by a flag:

--plot-twcs or config flag

Tests

Run single-day backtest with plotting ON

Confirm PNGs generated and no crashes if some snapshots are missing candles_1s.

🗄 Phase 4: Relational Database Integration
🎯 v0.8.2.0 — Basic DB Schema & Writer

Goal: Define DB schema & write basic TWCS + trades into DB.

New modules

src/midas_v2/db/schema.py

src/midas_v2/db/connection.py

src/midas_v2/db/write_trades.py

src/midas_v2/db/write_twcs.py

Schema (SQLite or Postgres; SQLite recommended at first)

trades table:

date, symbol, scenario, entry_time, exit_time, side, qty, pnl_raw, pnl_pct, outcome, etc.

twcs_entry table:

trade_id, symbol, date, time, indicators JSON, etc.

twcs_exit table:

same for exit

Later:

candles_1m / candles_1s in separate tables or JSON blob

Scripts

scripts/init_db.py:

Creates DB with tables.

scripts/import_twcs_to_db.py:

Scans out/YYYYMMDD/B/.../snapshots/*.json, writes to DB.

Files touched

Added:

DB modules + scripts

Unchanged:

backtester, indicators, UI (for this version)

🎯 v0.8.2.1 — Add Basic DB Query Tools

Goal: Ability to query trades vs indicators.

New scripts

scripts/query_trades_by_indicator.py

Example queries:

“TP vs SL where vwap_slope_bps > 30”

“TP vs SL where macd_hist > 0 and green_streak >= 2”

scripts/report_indicator_stats.py

Outputs distribution of indicators for winners vs losers.

At this point, you start having evidence-based insight into which thresholds matter.

🧠 Phase 5: Momentum Score & Profitability Filters
🎯 v0.8.3.0 — Implement momentum_score in TWCS

Goal: Add a single momentum_score field to TWCS snapshots based on existing indicators.

File to modify

src/midas_v2/indicators/twcs_indicators.py

Changes

Add helper:

def compute_momentum_score(indicators: Dict[str, Any]) -> float:
    ...


Called at end of build_twcs_indicators:

indicators["momentum_score"] = compute_momentum_score(indicators)

No strategy logic change yet

This version only provides the score for analysis / DB.

Tests

Run PHGE, MYGN, COMM

Check that momentum_score for PHGE TP > MYGN SL.

🎯 v0.8.3.1 — Add DB columns for momentum_score

Schema changes:

Add momentum_score_entry, momentum_score_exit fields in twcs_entry/twcs_exit.

Update write_twcs.py to persist them.

Use DB to analyze profit vs momentum_score.

🎯 v0.8.3.2 — Add Simple Momentum Filter (Experimental, A/B)

Goal: Begin experimental filters (A/B tested, not default).

File to modify

src/midas_v2/strategy/filters.py (new or existing helper)

Behavior (scenario B experimental branch):

Only allow trades where:

momentum_score_entry >= 60

IMPORTANT

In this version:

Keep filter behind a scenario flag or configuration (e.g., Scenario B_momentum).

Use range tests & DB to compare with unfiltered baseline.

📊 Phase 6: UI Integration (midas-ui)
🎯 v0.8.4.x — Display Indicators & Scores in UI

Files in UI repo: midas-ui/

Key components

src/pages/MidasLocalRunnerUI.tsx

src/components/TradeList.tsx (or equivalent)

src/components/TradeDetails.tsx

Features

For each trade:

Show summarised indicators (green_streak, vwap_slope, macd_hist, momentum_score).

Filters:

e.g., slider: “minimum momentum_score”.

Future

Display PNGs inside UI:

<img src="file://.../entry_1m.png" /> style (or via backend proxy).

Let you visually cross-check indicators vs candles.

🧪 Phase 7: Adaptive Sizing & Catalyst Intelligence

Once the above layers are in place:

Use DB + TWCS indicators + momentum_score to:

Increase size on A+ setups

Reduce/skip C-grade setups

Later integrate:

Catalyst scoring

News-based filters

Opening RVOL gates (wired into TWCS as real numbers)

This is where you directly chase profitability curves.

✅ Memory & Preferences

I’ve stored in memory that:

You prefer detailed, technical, file-level summaries for each version.

You want roadmaps that explicitly list:

Which files will be created

Which modules will be changed

Which scripts will be touched

How this ties into profitability, UI, and DB

I will continue using this style for all future version summaries and handovers.

If you’d like, the very next tiny step we can do (in practice) is:

Create a combined “Version Handover Template” for you to paste at the top of each new thread (v0.8.1.0.3, v0.8.1.0.4, etc.), including:

Short narrative summary

File-level change log

Active roadmap slice

Next 3 small tasks