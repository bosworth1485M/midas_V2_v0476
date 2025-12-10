📘 Document 1 — Version Summary for v0.8.1.0.5
TWCS Phase 3 – Part 3: PNG Rendering Integration
1. Purpose of this Version

Version v0.8.1.0.5 completes TWCS Phase 3 (Part 3) by enabling visual rendering of TWCS snapshots.
The primary goal was to produce entry and exit PNG files showing:

1-minute candle windows

1-second candle windows (empty until Phase 4 ingestion is completed)

Trade-timestamp markers

Optional indicator overlays in future versions

This version is non-invasive:
No trading logic, strategy behavior, sizing logic, execution logic, or risk logic was altered.

2. Technical Achievements
2.1 Added new plotting module

A new file was created:

src/midas_v2/plotting/twcs_plotter.py


This module:

Uses Matplotlib in headless mode (matplotlib.use("Agg"))

Provides plot_twcs_snapshot(snapshot, out_path)

Renders:

Top panel: 1-minute OHLC candles

Bottom panel: 1-second OHLC candles

Vertical trade-entry or trade-exit line

Titles indicating snapshot type (“Entry TWCS” / “Exit TWCS”)

Handles cases where 1-second data is missing (Phase 4 will populate these)

Saves PNG files at 140 DPI

Includes full error isolation (failures do not break backtesting)

2.2 Integrated plotter into backtester

The backtester was modified to:

Import the plotter

Add a new runtime flag:

plot_twcs_flag = bool(scenario_params.get("plot_twcs", False))


Generate PNGs immediately after writing TWCS metadata:

Files created:

trade_snapshot_entry.png
trade_snapshot_exit.png


These appear in the same directory as snapshot JSONs.

2.3 Updated Scenario Configuration

Scenario B now contains:

"twcs_enabled": true,
"plot_twcs": true


twcs_enabled → controls snapshot creation

plot_twcs → controls PNG creation

Both flags were successfully validated during testing.

2.4 Validation & Smoke Testing

Full backtest runs without PNGs → passed

Full backtest runs with PNGs → passed

Entry and exit PNGs were generated successfully

1-minute candles displayed correctly

1-second candles panel shows “No candle data” (expected until next version)

No regression in trading logic

No changes to risk, sizing, strategy, or scanner behavior

TWCS metadata remained correct and complete

3. What This Version Enables

This version enables:

Visual inspection of trade context

Groundwork for 1-second microstructure analysis

The DB + UI failure-mode viewer (planned for later versions)

A tighter diagnostic loop:
Numbers → PNGs → DB queries → rule improvements

This is a critical milestone toward profitability refinement.

4. What Is Not Included in This Version

Kept for future versions:

1-second data ingestion from Polygon

Indicator overlays on PNGs (VWAP line, MACD histogram)

UI integration of PNG viewer

Storing PNG paths in DB

DB ingestion layer

Multi-snapshot indicator evolution

These belong to v0.8.1.0.6 and beyond.

5. Version Status

v0.8.1.0.5 is complete, tested, stable, and ready to be tagged.