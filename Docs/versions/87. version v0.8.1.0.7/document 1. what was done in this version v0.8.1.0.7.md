DOCUMENT 1
Midas\_V2 v0.8.1.0.7 — Detailed Technical Summary, Analysis, and Findings

Version intent:
v0.8.1.0.7 completes the transition from data capture to human-grade diagnostic analysis by making every TWCS artifact visually self-explanatory and suitable for systematic failure analysis.

This document is intentionally detailed so that:

a future version thread

a future collaborator

or future you
can reconstruct exactly what changed, exactly what was learned, and exactly why v0.8.1.0.8 exists.

1. Code Changes in v0.8.1.0.7 (Exact Scope)
   1.1 Scripts modified

Exactly one production file was modified:

src/midas\_v2/plotting/twcs\_plotter.py



No other scripts were changed.

1.2 What changed in twcs\_plotter.py

The plotter was extended from “price-only visualization” to full diagnostic rendering, using only existing snapshot fields.

New helper functions added

(all lines tagged # v0.8.1.0.7)

\_safe\_get(...)

Null-safe dictionary access

\_get\_ind(...)

Safe indicator extraction from snapshot

\_fmt\_float(...)

Consistent numeric formatting + signed values

\_trade\_time\_str(...)

Entry vs exit timestamp resolution

\_trade\_price(...)

Best-effort price derivation (explicit price → idx\_from\_entry==0 close)

\_annotate\_box(...)

Figure-level annotation blocks (non-intrusive)

These helpers exist only to render information already computed elsewhere.

Plot enhancements (no layout change)

The existing two-panel layout was preserved:

Top panel → 1-minute candles

Bottom panel → 1-second candles

Vertical trade-time marker retained

No third panel was added.

1.3 New visual overlays (read-only)
On the 1-minute panel:

VWAP line

Drawn from snapshot\["indicators"]\["vwap"]

Entry / Exit price line

Derived from snapshot data only

Optional legend only if overlays present

Figure-level annotation boxes:

Indicator box (always present)

green\_streak

macd\_hist

macd\_slope

vwap

vwap\_slope\_bps

rvol\_open

Outcome box (exit snapshots only)

outcome (TP / SL)

pnl\_raw

pnl\_pct

mfe / mae (when present)

1-second panel:

Window legend

window\_before\_1s

window\_after\_1s

window\_size\_1s

All overlays:

degrade gracefully

never crash

never recompute indicators

never infer strategy logic

1.4 Output stability

PNG format unchanged

DPI unchanged (140)

No bbox\_inches="tight"

No figure size expansion

No path changes

This guarantees visual comparisons across versions remain valid.

2. New Capabilities Enabled by v0.8.1.0.7

After this version, each TWCS PNG is a complete diagnostic artifact.

For any trade, the PNG alone answers:

Where was price relative to VWAP?

Was VWAP rising or flattening?

How strong was MACD at the moment of entry?

Did green candles have conviction?

What did the 1-second tape do immediately before entry?

How did price behave immediately after entry?

Why did the exit occur (TP vs SL)?

This removed the need to:

cross-reference logs

read JSON manually

mentally align indicators with candles

3. Detailed Visual Analysis Performed (2025-08-06, Scenario B)

We intentionally analyzed a single controlled day to avoid noise.

Trades analyzed:

PHGE — TP (+2.0%)

MYGN — SL (−2.5%)

AIMD — SL (−2.5%)

CYRX — SL (−2.5%)

Each trade was reviewed using:

Entry TWCS PNG

Exit TWCS PNG

Snapshot metadata

4. Trade-by-Trade Findings
   4.1 PHGE — Winner (TP)

Visual characteristics:

VWAP slope: positive

Entry price: above VWAP but not extended

MACD: mixed (hist positive, slope slightly negative)

Green streak: weak

1-second tape:

stable

orderly

no stall

no compression

Conclusion:

PHGE succeeded because microstructure was supportive and entry was not late, even though indicators were imperfect.

4.2 MYGN — Loser (SL)

Visual characteristics:

VWAP slope: marginal positive → flips negative

MACD: barely positive

Green streak: meets rule

1-second tape:

overlapping bars

chop

no expansion phase

hesitation immediately before entry

Conclusion:

MYGN failed because entry occurred into stalled microstructure with no impulse.

4.3 AIMD — Loser (SL)

Visual characteristics:

VWAP slope: strongly positive

MACD: positive and rising

Green streak: very strong (5)

1-second tape:

busy

“worked”

no decisive expansion

price drifted, not launched

Conclusion:

Strong indicators did not compensate for weak microstructure. Entry timing was late.

4.4 CYRX — Loser (SL)

Visual characteristics:

VWAP slope: positive at entry

MACD: strong

Green streak: acceptable

1-second tape:

compression

overlapping prints

impulse already occurred earlier

entry after exhaustion

Conclusion:

CYRX failed due to late continuation entry into compressed tape.

5. Confirmed Dominant Failure Mode (High Confidence)

After four independent trades:

Scenario B fails primarily when entries are taken without a recent 1-second expansion phase, even when all indicator and VWAP rules pass.

Key points:

3 out of 3 losers shared this signature

The winner did not

Indicator strength was not sufficient

VWAP slope alone was not sufficient

Microstructure timing was decisive

This failure mode was not reliably detectable before v0.8.1.0.7.

6. Why v0.8.1.0.7 Is Complete and Frozen

v0.8.1.0.7 achieved:

Full microstructure visibility

Self-contained diagnostic artifacts

Reliable failure-mode discovery

Zero behavioral contamination

Any further changes in this version would:

mix diagnosis with treatment

break experimental discipline

Therefore:

v0.8.1.0.7 should be tagged, frozen, and never modified.



7\. Why v0.8.1.0.8 Exists



The analysis directly motivates one—and only one—next experiment:



Test whether requiring a recent 1-second expansion phase removes the dominant loss bucket.



That experiment belongs exclusively in the next version.



If you want, next I can:



tighten DOCUMENT 2 and 3 to the same audit depth, or



produce a final v0.8.1.0.7 tag message that references this document line-by-line.



Just tell me how far you want to go.

