BEGIN SPEC FOR v0.8.1.0.7 — TWCS PNG OVERLAYS (DETAILED)

Goal:
Make each TWCS PNG “self-explanatory” by overlaying trade context + indicator values directly on the image.

This is VISUALIZATION ONLY.
Do NOT change trading logic, indicator computations, snapshot schema, sizing, or risk logic.
Only modify the plotter so it reads existing fields from snapshot JSON and draws overlays/annotations.

All new/modified lines MUST include inline comment:  # v0.8.1.0.7

Files:
- MODIFY ONLY: src/midas_v2/plotting/twcs_plotter.py
- DO NOT modify any other file.

------------------------------------------------------------
0) Current Inputs / Snapshot Contract (READ-ONLY)
------------------------------------------------------------

The plotter receives a snapshot dict (already parsed from trade_snapshot_*_meta.json).
Expect some or all of these keys to exist:

Top-level:
- symbol (str)
- scenario (str)
- trade_id (str)
- date (str "YYYY-MM-DD")
- window_type (str "entry" or "exit")
- entry_time (str "YYYY-MM-DD HH:MM") [entry snapshots]
- exit_time (str "YYYY-MM-DD HH:MM") [exit snapshots]
- candles_1m (list[dict]) with fields: t,o,h,l,c,v,idx_from_entry,(others)
- candles_1s (list[dict]) with fields: t,o,h,l,c,v,idx_from_entry
- window_before_1m, window_after_1m, window_size_1m (int)
- window_before_1s, window_after_1s, window_size_1s (int)
- indicators (dict) which may contain:
    - green_streak (int)
    - vwap (float)
    - vwap_slope_bps (float)
    - macd_hist (float)
    - macd_slope (float)
    - rvol_open (float or null)

Exit-only fields (may exist on exit snapshots):
- outcome (str "TP" or "SL" etc)
- pnl_raw (float)
- pnl_pct (float)
- mfe (float or null)
- mae (float or null)

IMPORTANT:
- Some snapshots may be missing indicators or have null values.
- candles_1s may be empty.
- Plotter must NEVER crash if any field is missing.

------------------------------------------------------------
1) Layout Requirements
------------------------------------------------------------

Keep the existing 2-panel layout:

- Top axis: 1-minute candles
- Bottom axis: 1-second candles
- Existing vertical trade-time line stays (entry/exit marker)

Do NOT add a third panel.
Do NOT add new dependencies.

Keep output format identical:
- PNG output path unchanged
- DPI unchanged (keep existing setting)
- Headless (Agg) unchanged

------------------------------------------------------------
2) Add Helper Functions (inside twcs_plotter.py)
------------------------------------------------------------

Add small helper functions to keep overlay code clean:

(A) Safe dict getters:
    def _safe_get(d, key, default=None):  # v0.8.1.0.7
        ...

(B) Safe indicator getter:
    def _get_ind(snapshot, key, default=None):  # v0.8.1.0.7
        return snapshot.get("indicators", {}).get(key, default)

(C) Formatting helpers:
    def _fmt_float(x, decimals=2, signed=False):  # v0.8.1.0.7
        - If x is None: return "n/a"
        - If signed: prefix + for positive numbers
        - Return formatted string

(D) Determine trade clock time string:
    def _trade_time_str(snapshot):  # v0.8.1.0.7
        - If window_type == "entry": use snapshot["entry_time"]
        - If window_type == "exit": use snapshot["exit_time"]
        - Else: fallback "n/a"

(E) Determine trade price for labeling (best-effort):
    def _trade_price(snapshot, fallback="close_1m_idx0"):  # v0.8.1.0.7
        Prefer, in order:
        1) snapshot.get("entry_price") or snapshot.get("exit_price") if present
        2) candle in candles_1m where idx_from_entry == 0 -> use its "c"
        3) if not found, return None

This function is for plotting labels only; do NOT alter strategy.

(F) Axis annotation helper:
    def _annotate_box(fig, text_lines, x=0.985, y=0.98):  # v0.8.1.0.7
        - Place a text box in figure coordinates (fig.text)
        - Right-aligned, top-aligned
        - Use a small semi-transparent bbox
        - Keep readable font size

------------------------------------------------------------
3) Title Block (Figure-level)
------------------------------------------------------------

Add a clear title at the top of the figure:

Line 1:
    "{SYMBOL} — {ENTRY|EXIT} TWCS"

Line 2 (smaller):
    "{DATE}  {HH:MM}  |  Scenario {SCEN}  |  Trade {trade_id}"

Sources:
- symbol, window_type, date, scenario, trade_id, entry_time/exit_time

If any are missing, degrade gracefully (use "n/a" placeholders).

------------------------------------------------------------
4) Overlays on the 1-minute Panel (Top axis)
------------------------------------------------------------

4.1 VWAP Overlay Line (scalar)
- If indicators.vwap exists and is numeric:
    - draw a horizontal line at y=vwap across the top axis
    - label near right edge: "VWAP {vwap:.2f}"
- If missing/null: skip.

4.2 Entry/Exit Price Line
- Determine trade_price via _trade_price()
- If trade_price exists:
    - draw a horizontal line at y=trade_price
    - label near right edge:
        - "Entry {price:.2f}" if entry
        - "Exit  {price:.2f}" if exit
- If missing: skip.

4.3 Optional TP/SL levels (ONLY if present in snapshot)
- If snapshot includes tp_price/sl_price, draw thin horizontal lines with labels.
- If snapshot includes tp_pct/sl_pct AND trade_price exists:
    - compute tp_price = trade_price*(1+tp_pct/100)
    - compute sl_price = trade_price*(1-sl_pct/100)
  BUT ONLY if those values are already stored in snapshot; if not present, do NOT compute.
(Prefer explicit tp_price/sl_price if available; otherwise skip.)

IMPORTANT: Do NOT infer strategy settings or recompute TP/SL from configs here.

------------------------------------------------------------
5) Bottom Panel (1-second axis) Legend + Marker Confirmation
------------------------------------------------------------

5.1 Keep existing 1-second candle plotting exactly as-is.

5.2 Add a small legend text in the bottom-left of the 1s axis:

Example:
    "1s window: -60s → 0s | N=57"

Use:
- window_before_1s, window_after_1s, window_size_1s
If missing, show what is available, e.g. "1s window: N=0" or "1s window: n/a".

Do NOT clutter the panel.

------------------------------------------------------------
6) Indicator Annotation Box (Figure-level, top-right)
------------------------------------------------------------

Render a compact text box showing key values:

Always include labels in this order:
- green_streak: <int or n/a>
- macd_hist: <signed float 4dp or n/a>
- macd_slope: <signed float 4dp or n/a>
- vwap: <float 4dp or n/a>
- vwap_slope_bps: <signed float 1dp or n/a>
- rvol_open: <float 2dp or n/a>

Rules:
- Read from snapshot["indicators"]
- If key missing or value is None: print "n/a"
- Use _fmt_float helpers
- Keep stable ordering so comparisons across trades are easy

Place the box in figure coordinates (not inside candles) so it never blocks price action.

------------------------------------------------------------
7) Exit-only Outcome Box (Figure-level, below indicator box)
------------------------------------------------------------

If window_type == "exit":
- If outcome exists: include "Outcome: TP" or "Outcome: SL"
- If pnl_raw exists: include "PnL: +$27.83"
- If pnl_pct exists: include "(+2.00%)"
- If mfe/mae exist and non-null: include "MFE: ..." / "MAE: ..."

If any field missing, omit that line; never crash.

This box must be visually smaller than the main indicator box and must not overlap the title.

------------------------------------------------------------
8) Robustness / Failure Isolation
------------------------------------------------------------

- If candles_1s is empty: still render PNG, show "N=0" window legend.
- If candles_1m is empty: still render PNG with text boxes (but likely no candles).
- If indicators dict missing: still render PNG; show all indicator values as "n/a".
- Any exception inside overlay code must NOT prevent PNG generation.
  Wrap overlays in try/except and log a warning, but allow the base chart to save.

------------------------------------------------------------
9) Testing Instructions (Manual)
------------------------------------------------------------

After implementing, test on the known working day/trade:

- Run:
    python scripts/run_range_and_summarize.py --start 2025-08-06 --end 2025-08-06 --scenario B

Then inspect:
- out/20250806/B/PHGE/snapshots/PHGE_2025-08-06_0958/trade_snapshot_entry.png
- out/20250806/B/PHGE/snapshots/PHGE_2025-08-06_0958/trade_snapshot_exit.png

Confirm:
- VWAP line visible on top axis
- Entry/Exit price line visible on top axis
- Indicator box visible with real values
- Exit outcome box visible with TP/SL and pnl
- 1s window legend visible on bottom axis
- No regressions: PNGs still generated for all trades

------------------------------------------------------------
10) Output Constraint
------------------------------------------------------------

Copilot MUST output ONLY the modified file:
- src/midas_v2/plotting/twcs_plotter.py

No other files changed.
No new dependencies.

END SPEC FOR v0.8.1.0.7 — TWCS PNG OVERLAYS (DETAILED)
