📘 Document 3 — Copilot Implementation Spec for v0.8.1.0.6
TWCS Phase 4 – Part 1: 1-Second Polygon Data Ingestion

You can paste this entire block into Copilot.

BEGIN SPEC FOR v0.8.1.0.6

Goal:
Implement TWCS Phase 4 (Part 1): 1-second Polygon data ingestion and TWCS second-window population.

Do NOT modify trading logic, indicators, strategy flow, sizing, or risk modules.
Only implement second-level data ingestion and loader wiring.

All new or edited code must include inline version tags:  # v0.8.1.0.6

------------------------------------------------------------
1. CREATE NEW FILE: scripts/fetch_seconds_polygon.py
------------------------------------------------------------

Requirements:
- Follow the exact API key handling pattern used in scripts/fetch_minutes_polygon.py.
- Fetch Polygon 1-second bars from:
    /v2/aggs/ticker/{symbol}/range/1/second/{date}/{date}
- Convert UNIX ms timestamps to ISO strings consistent with minute-loader format.
- Write CSV to:
    data/samples/sample_1s_YYYY-MM-DD_SYMBOL.csv
- Columns:
    t, o, h, l, c, v
- If no data, write an empty CSV but do not raise.
- Accept arguments:
    --date YYYY-MM-DD
    --session (optional, default rth)
    --universe path/to/universe.txt

------------------------------------------------------------
2. UPDATE FILE: src/midas_v2/dataio/twcs_second_loader.py
------------------------------------------------------------

Implement the following behavior:

1. Load CSV from:
       data/samples/sample_1s_YYYY-MM-DD_SYMBOL.csv
2. Parse timestamps to datetime.
3. Filter for:
       target_time - window_before_seconds
       <= candle_time <=
       target_time + window_after_seconds
4. Return:
       candles_1s: list of dicts containing t, o, h, l, c, v
       meta_1s: {
           "window_size_1s": N,
           "window_before_1s": <provided>,
           "window_after_1s": <provided>
       }
5. If file missing, return:
       [], {"window_size_1s": 0, ...}

------------------------------------------------------------
3. NO CHANGES REQUIRED in backtester.py
------------------------------------------------------------

The backtester already calls load_twcs_second_window for entry and exit.
Ensure loader interface remains consistent.

------------------------------------------------------------
4. TESTING REQUIREMENTS
------------------------------------------------------------

After implementation, verify:

1. fetch_seconds_polygon.py writes valid 1-second CSVs.
2. TWCS snapshot JSON files contain non-empty "candles_1s".
3. trade_snapshot_entry.png and trade_snapshot_exit.png show real microstructure.
4. If CSV is missing, loader returns empty list gracefully.

------------------------------------------------------------
5. OUTPUT REQUIREMENT
------------------------------------------------------------

Copilot MUST output only:
- New file: scripts/fetch_seconds_polygon.py
- Updated file: src/midas_v2/dataio/twcs_second_loader.py

END SPEC FOR v0.8.1.0.6

✅ Everything is now ready

You now have:

✔ Full version summary for v0.8.1.0.5

✔ Full handover document for v0.8.1.0.6

✔ Copilot spec to implement v0.8.1.0.6

The next step is simple:

👉 Paste the Copilot spec into VS Code and let it generate the new scripts.

After the edits, you can paste the generated changes here and I will review them before you test the ingestion.

Would you like me to generate the GitHub tagging commands for v0.8.1.0.5 now?