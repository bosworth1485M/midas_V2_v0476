DOCUMENT 2
Handover Document — v0.8.1.0.7 (and v0.8.1.0.8 Preview)
Current State (Start of v0.8.1.0.7)

At the start of v0.8.1.0.7, the system has:

Real 1-second TWCS data

Correct alignment to trades

JSON + PNG output per trade

Stable runner integration

No regressions

The system can now see the trade in detail.
The next step is to understand it faster.

v0.8.1.0.7 — Indicator Overlays & Visual Context
Objective

Enhance TWCS PNGs so that numeric indicators are visually contextualized, eliminating the need to mentally correlate numbers with price action.

Scope of v0.8.1.0.7

This version will focus exclusively on PNG enhancements, not strategy logic.

Planned Enhancements:

VWAP Overlay

Plot VWAP line on the 1-minute panel

Use existing VWAP values already computed

Optional slope annotation (bps)

Entry/Exit Annotation

Clear marker for entry price

Optional TP / SL horizontal lines

MACD Context (Lightweight)

Small histogram inset or annotation

Use existing macd_hist values

No recomputation required

Indicator Text Block

Render key indicator values directly on the PNG:

green_streak

macd_hist

macd_slope

vwap

vwap_slope_bps

This turns the PNG into a self-contained diagnostic artifact.

v0.8.1.0.8 — Database Ingestion (Recommended Next)

After v0.8.1.0.7, the logical next step is persistence and analysis.

Recommended Scope for v0.8.1.0.8

Ingest TWCS snapshots into a relational database

Store:

Trade metadata

Indicators

Snapshot file paths

Enable:

Query-driven failure analysis

UI exploration

Cross-trade pattern detection

This version should not modify trading logic — only storage and retrieval.

Versioning Guidance

v0.8.1.0.6 → Microstructure ingestion

v0.8.1.0.7 → Visual understanding

v0.8.1.0.8 → Analytical understanding

Do not collapse these — the separation is what keeps the system stable.