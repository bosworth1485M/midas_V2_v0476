v0.8.1.0.7 finer-detail plan

Goal: make each TWCS PNG a self-contained diagnostic artifact (you shouldn’t need to open JSON to understand why the trade fired and what the microstructure looked like).

What stays unchanged

No strategy/risk/indicator logic changes.

No snapshot schema changes (we only read what’s already in trade_snapshot_*_meta.json).

Only modify the TWCS plotter (and if absolutely necessary, a tiny helper inside the plotter module).

A. PNG “Information Architecture” (what appears where)
1) Title block (top, centered)

Format:

"{SYMBOL} – {Entry|Exit} TWCS"

Optional second line: "{DATE} {HH:MM} | Scenario {X} | Trade {trade_id}"

Source fields (from JSON):

symbol, window_type, date, entry_time or exit_time, scenario, trade_id

2) Panel 1 (top): 1-Minute Candles + VWAP overlay

Keep the existing 1-minute candlestick rendering.
Add overlays:

2.1 VWAP line

Draw a horizontal line at indicators.vwap (since it’s a scalar in the snapshot right now).

Label: VWAP 9.63 (2 decimals)

If vwap is missing/null, skip.

2.2 Entry/Exit price line

Draw a horizontal line at:

entry snapshot: “entry price”

exit snapshot: “exit price”

Where to get price:

Prefer explicit entry_price / exit_price if present in JSON.

If not present (likely), derive from the 1-minute candle at index idx_from_entry == 0:

Use that candle’s c (close) as proxy for plotting only.

Label: Entry 9.80 / Exit 10.00

Use a subtle linestyle different from VWAP.

2.3 Optional TP/SL bands (only if values exist)

If snapshot has tp_price/sl_price or tp_pct/sl_pct and an entry price is known:

Draw thin lines for TP and SL.

If not available: skip entirely (don’t recompute risk rules in plotter).

3) Panel 2 (bottom): 1-Second Candles + trade marker (already works)

Keep the existing 1-second rendering.
Add only one enhancement:

3.1 “Window legend”

Show: 1s window: -60s → 0s | N=57

Use: window_before_1s, window_after_1s, window_size_1s

If any missing, show what’s available.

4) Indicator / Context box (top-right of the figure, not inside a panel)

A small text block that reads directly from snapshot["indicators"]:

green_streak: 1

macd_hist: +0.0256

macd_slope: -0.0190

vwap: 9.6271

vwap_slope_bps: +51.8

rvol_open: (blank or n/a if null)

Rules:

Always show the label.

If value is null/missing, print n/a.

Keep fixed order so comparisons are easy.

5) Outcome box (only on Exit TWCS if present)

Exit meta you posted includes:

outcome: "TP"

pnl_raw, pnl_pct

(and possibly mfe, mae later)

So on exit PNG only:

Show Outcome: TP | PnL: +$27.83 (+2.00%)

If fields missing, skip them gracefully.

B. Visual choices that keep it readable

The biggest risk in v0.8.1.0.7 is clutter, so:

Don’t add a third panel (no MACD subplot yet).
v0.8.1.0.7 is “overlay + annotation”, not a dashboard.

Use text blocks + 1–2 lines.
VWAP line + entry/exit line are enough.

Place annotations in the figure margin, not over candles.
Use fig.text(...) or an anchored box in top-right.

Never crash if a field is missing.
Every overlay should be “best effort”.

C. Exact implementation steps (small, safe increments)
Step 1 — Add a “safe getters” layer inside twcs_plotter.py

get_indicator(snapshot, key, default=None)

fmt_float(value, decimals=2, signed=False)

format_time(snapshot) helper to pick entry vs exit time

Step 2 — Add the info box (no chart changes yet)

Implement a function that builds the lines list

Render via ax.text(...) in the top panel corner or fig.text(...) in margin

Test on PHGE entry/exit

Step 3 — Add VWAP overlay (1-minute panel)

If indicators.vwap exists → ax1.axhline(...)

Add label text near the right edge

Step 4 — Add Entry/Exit price line (1-minute panel)

Determine price:

Prefer explicit field if present

Else derive from candles_1m candle where idx_from_entry == 0

Draw ax1.axhline(...) + label

Step 5 — Add exit-only outcome box

Only if window_type == "exit"

Pull outcome, pnl_raw, pnl_pct

Render under indicator box

Step 6 — Add the 1s window legend (bottom panel)

Use window_before_1s, window_after_1s, window_size_1s

Put in bottom-left of the 1s axis

Step 7 — Regression check

Run the same day (2025-08-06) and confirm:

PNGs still render for entry+exit

No exceptions for symbols that have missing fields

Layout still readable at 140 DPI

D. Acceptance criteria for v0.8.1.0.7

v0.8.1.0.7 is “done” when:

Entry and Exit PNGs show:

VWAP line

Entry/Exit price line

Indicator box (with n/a handling)

Exit outcome (TP/SL + pnl) on exit PNGs

Zero regressions:

PNGs still produced automatically

TWCS JSON unchanged

Works even when:

candles_1s is empty

rvol_open is null

outcome fields absent (for entry snapshots)

E. Small optional add-ons (only if it stays clean)

If you want 1 extra “signal” without clutter:

Highlight the trade-time 1-second candle (outline or thicker border)

Or annotate: Trade @ 09:58:00 already implied by vertical line

But I’d keep these optional.