📘 Document 2 — Handover Document for v0.8.1.0.6
TWCS Phase 4 – Part 1: 1-Second Data Ingestion
1. Purpose of v0.8.1.0.6

Now that PNG rendering is in place, the next step is to populate the 1-second candle data that the renderer is prepared to display.

This is TWCS Phase 4, whose goals are:

Fetch real Polygon 1-second bars for all symbols in the universe

Store them as standardized local CSVs

Ensure correct timestamp alignment with TWCS windows

Extend the 1-second TWCS loader to return real candles

Populate candles_1s in entry/exit snapshots

Produce PNGs with actual microstructure, not blank lower panels

Prepare the system for DB ingestion and failure-mode analysis

This version remains non-invasive—still no changes to strategy logic or sizing.

2. Required Modules / Files
2.1 New fetch script

Add:

scripts/fetch_seconds_polygon.py


This script will:

Read universe for a given date

Retrieve 1-second bars from Polygon’s /v2/aggs/ticker/TICKER/range/1/second endpoint

Save to:

data/samples/sample_1s_YYYY-MM-DD_SYMBOL.csv


Follow the same API key pattern as existing minute-fetcher

Write consistent column names: t, o, h, l, c, v

2.2 Extend TWCS second-level loader

Modify:

src/midas_v2/dataio/twcs_second_loader.py


to:

Load the new 1-second CSV

Filter the window ±60 seconds around trade timestamp

Return candles_1s and metadata

Return an empty list gracefully if no file exists

2.3 Ensure correct timestamp formats

PNGs expect:

ISO timestamp strings (e.g., "2025-08-06T09:58:00")

Loader should convert UNIX ms → ISO consistent with 1-minute loader

2.4 Update backtester hook

Backtester already calls:

entry_candles_1s, entry_meta_1s = load_twcs_second_window(...)


and similarly for exits.

Once 1-second ingestion works, no code change is required here.

3. Validation Requirements

After implementation:

✔ Test on a known multi-entry date

(e.g., 2025-08-06, Scenario B)

Expect:

1-second CSV files created

TWCS snapshot JSONs show non-empty candles_1s list

PNG lower panel displays:

True OHLC microstructure

Vertical trade marker aligned to the right second

✔ Check performance

Ensure that fetching 1-second bars is efficient

Consider caching or trimming data later if needed

4. What This Version Enables

Once 1-second data is present:

You can visually see micro-breakouts, fakeouts, reclaim strength

You can evaluate:

wick exhaustion

volume climax

microstructure divergences

This becomes a massive accelerant to identifying rule improvements

Later DB queries will report:

“SL trades had weak 1s microstructure at entry.”

“TP trades had strong 1s continuation.”

This is the foundation of the profitability analysis loop.

5. Out of Scope for v0.8.1.0.6

These belong to later versions:

DB ingestion

UI Failure-Mode Viewer

Indicator overlays on PNG

Support/resistance micro-panels

Adaptive microstructure gates

v0.8.1.0.6 focuses strictly on data ingestion + correct display.

6. Completion Criteria

Version v0.8.1.0.6 is complete when:

Real 1s data appears in TWCS snapshot JSON

Real 1s candles appear in PNGs

No regressions occur in minute-level TWCS

Performance remains acceptable

The same backtest day runs cleanly as before