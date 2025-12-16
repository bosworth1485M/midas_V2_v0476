📘 DOCUMENT 1
Technical Version Summary — v0.8.1.0.6
TWCS Phase 4 – Part 1: 1-Second Microstructure Ingestion & Runner Integration
1. Purpose of This Version

Version v0.8.1.0.6 completes TWCS Phase 4 – Part 1, whose objective was to move TWCS from structural readiness to full microstructure visibility.

Specifically, this version:

Introduces real 1-second Polygon data ingestion

Wires that data cleanly into:

TWCS snapshot JSONs (entry & exit)

TWCS PNG rendering (lower panel)

Integrates 1-second fetching into the standard day/range runner

Preserves all existing strategy, risk, and execution logic (non-invasive)

This version closes the loop between:

Trade decision → indicator state → minute context → second-by-second microstructure

2. New Capabilities Introduced
2.1 Real 1-Second Polygon Data Ingestion

A new ingestion path was implemented to fetch true 1-second OHLCV bars from Polygon for all symbols traded on a given day.

Key properties:

Endpoint: Polygon Aggregates, 1-second resolution

Scope: Full RTH session for each symbol

Output format: CSV files written locally per symbol/day

Output files:

data/samples/sample_1s_YYYY-MM-DD_SYMBOL.csv


Each CSV contains standardized columns:

t, o, h, l, c, v


These files are intentionally parallel to the existing 1-minute CSVs to maintain symmetry in loaders and tooling.

2.2 Polygon API Key Handling (Critical Fix)

A major source of fragility in prior experiments was inconsistent Polygon key handling.

In this version:

fetch_seconds_polygon.py was explicitly aligned to use the same API key loading and request pattern as:

topgappers.py

fetch_minutes_polygon.py

Key characteristics:

.env loading from project root

Explicit stripping of quoted keys

Bearer authorization header

No reliance on RESTClient shortcuts that previously caused “Unknown API Key” failures

This alignment is essential and must be preserved in all future Polygon-related code.

2.3 TWCS Second-Level Loader (Confirmed Compatible)

The existing twcs_second_loader.py (introduced earlier in Phase 3) was validated to be fully compatible with the new 1-second CSVs.

It correctly:

Loads per-symbol 1-second CSVs

Parses timestamps consistently

Filters a precise ±N-second window around entry/exit

Produces:

candles_1s

window_size_1s

idx_from_entry (critical for alignment & plotting)

No changes were required to the loader in this version.

2.4 Automatic Runner Integration (No Manual Steps)

A major ergonomic improvement was made:

1-second fetching is now automatically triggered by the normal day runner

No separate manual script invocation is required

Integration logic:

The day runner checks:

scenario_params["twcs_enabled"] == True


When enabled:

1-minute fetch runs (as before)

1-second fetch runs immediately after

Backtest proceeds normally

Failures in 1-second fetching:

Log warnings

Do not abort the day run

This preserves robustness while eliminating “forgot to fetch seconds” errors.

2.5 TWCS Snapshot JSONs (Entry & Exit)

For each trade, the following are now fully populated:

candles_1m (unchanged)

candles_1s (new, real data)

idx_from_entry correctly spans:

[-window_before_1s ... 0]


Indicator values remain numeric and unchanged

Example confirmed characteristics:

Entry snapshot:

57 seconds of microstructure

Clean alignment to entry timestamp

Exit snapshot:

Independent 1-second window

Correct alignment to exit timestamp

2.6 PNG Rendering with Real Microstructure

The TWCS PNG renderer introduced in v0.8.1.0.5 now displays true second-level price action.

Layout:

Top panel: 1-minute candles

Bottom panel: 1-second candles

Vertical dashed line: entry/exit timestamp

This visual context now enables:

Micro pullback inspection

Wick exhaustion analysis

Momentum continuation vs stall diagnosis

Visual confirmation of indicator signals

3. What Was Explicitly NOT Changed

To preserve safety and interpretability:

❌ No strategy rules changed

❌ No indicator logic changed

❌ No risk sizing logic changed

❌ No execution logic changed

❌ No parameter defaults changed

v0.8.1.0.6 is purely an observability and data-plumbing upgrade.

4. Why This Version Matters

This version unlocks:

Failure-mode analysis grounded in what actually happened second-by-second

Visual confirmation of why trades succeeded or failed

The foundation for:

Indicator overlays

Database ingestion

UI-driven diagnostics

Measurable profitability refinement

Many Cameron-style projects never build this layer cleanly. You now have it.

5. Version Status

v0.8.1.0.6 is complete, validated, and should be tagged and frozen.