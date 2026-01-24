COPILOT IMPLEMENTATION SPEC for version v0.8.1.25.0
Execution Correctness Fix — Duplicate Minute Timestamp Canonicalization

BEGIN COPILOT IMPLEMENTATION SPEC

### Preface (placement-critical)
- Insert the canonicalization block immediately after:
  1) `bars = data.load_minute_bars(sym, date_str)  # v0.8.1.3.0` (day-gate prepass)
  2) `bars = data.load_minute_bars(sym, date_str)` (main per-symbol loop)
- In the main per-symbol loop, add `telemetry["dup_ts_count"] = dup_count_canon` ONLY after the telemetry dict is initialized (telemetry does not exist at the load line).
- Do not modify the existing `pos_bar_by_ts` duplicate-safe merge block.

0) One-sentence objective (must match implementation)

Implement a deterministic execution-correctness canonicalization of duplicate minute timestamps so that strategy evaluation and position management use the same OHLCV per timestamp, eliminating POS_MGMT_MISMATCH caused by inconsistent duplicate-bar handling.

1) Strict scope rules (do not violate)

Single change only: canonicalize duplicate timestamps in minute bars before evaluation and before position management is constructed.

No strategy logic changes (no entry/exit changes, no guard changes, no parameter tuning).

No refactors (no new helpers, no moving blocks, no renames outside the new block).

Single file only: src/midas_v2/engine/backtester.py

Copilot must not run commands or run tests.

All new/modified lines must include inline comments containing v0.8.1.25.0 near any new/changed code so changes are traceable.

2) File to change (exact)

src/midas_v2/engine/backtester.py

No other files.

3) What bug we are fixing (context, not additional behavior changes)

Raw minute data may contain duplicate timestamps with conflicting OHLCV. Currently:

Strategy evaluation / guards iterate the raw bars

Position management relies on merged pos_bar_by_ts

This can produce POS_MGMT_MISMATCH and contaminate SL/TP outcomes when the two streams disagree.

We fix by canonicalizing bars into one bar per timestamp using the same merge policy already used by the pos_bar_by_ts duplicate-safe merge:

open = first open

high = max high

low = min low

close = last close

volume = sum volume

vwap = first non-null vwap (keep current behavior)

4) Implementation overview (two insertion points, no other changes)

You must apply the same canonicalization block at two exact minute-load points.

A) Day-gate prepass load (exact anchor)

Find the line:

bars = data.load_minute_bars(sym, date_str)  # v0.8.1.3.0


Immediately after this line, insert the canonicalization block from Section 5 (template), and then proceed with existing logic unchanged.

Placement requirement:

Insert before any len(bars) checks or indexing (e.g., before if len(bars) <= i_eval:).

B) Main per-symbol backtest load (exact anchor)

Inside the main for sym in symbols: loop, find:

bars = data.load_minute_bars(sym, date_str)


Immediately after this line, insert the canonicalization block from Section 5 (template), and then proceed unchanged.

Important nuance from this file:

The code initializes the per-symbol telemetry = {...} dict after loading bars.

Therefore, do not write telemetry inside the canonicalization block at this insertion point (telemetry does not exist yet).

You will set telemetry in Section 6 at the correct location.

Do not change the existing pos_bar_by_ts duplicate-safe merge block. Leave it as-is.

5) Canonicalization template (paste inline, do not factor out)

Use this template in both insertion points (only indentation may differ).

Critical requirements:

Never drop bars.

If b.ts is missing/None, generate a unique synthetic timestamp AND store it into the new Bar.ts so downstream logic (pos_bar_by_ts) does not collapse all None timestamps into a single key.

Preserve first-seen order.

Merge duplicates using the exact policy described above.

Emit a warning log when duplicates exist (or when synthetic timestamps were generated).

Paste this block exactly:

# v0.8.1.25.0: Canonicalize duplicate minute timestamps BEFORE evaluation and pos mgmt
canon_by_ts: dict[object, Bar] = {}  # v0.8.1.25.0
canon_ts_order: list[object] = []   # v0.8.1.25.0
dup_count_canon = 0                # v0.8.1.25.0
no_ts_count_canon = 0              # v0.8.1.25.0

for b in bars:  # v0.8.1.25.0
    ts = getattr(b, "ts", None)  # v0.8.1.25.0

    if ts is None:  # v0.8.1.25.0
        # v0.8.1.25.0: defensive — keep bar as-is if no timestamp (do NOT drop)
        # v0.8.1.25.0: assign a unique synthetic ts AND store it into Bar.ts to avoid later key-collapsing
        no_ts_count_canon += 1  # v0.8.1.25.0
        ts = f"__NO_TS__{no_ts_count_canon}"  # v0.8.1.25.0

    if ts not in canon_by_ts:  # v0.8.1.25.0
        canon_by_ts[ts] = Bar(  # v0.8.1.25.0
            ts=ts,       # v0.8.1.25.0
            o=b.o,
            h=b.h,
            l=b.l,
            c=b.c,
            v=b.v,
            vwap=b.vwap
        )
        canon_ts_order.append(ts)  # v0.8.1.25.0
    else:
        # v0.8.1.25.0: merge duplicate timestamp using same policy as pos_bar_by_ts
        dup_count_canon += 1  # v0.8.1.25.0
        prev = canon_by_ts[ts]  # v0.8.1.25.0
        canon_by_ts[ts] = Bar(  # v0.8.1.25.0
            ts=ts,                    # v0.8.1.25.0
            o=prev.o,                 # first open
            h=max(prev.h, b.h),       # max high
            l=min(prev.l, b.l),       # min low
            c=b.c,                    # last close
            v=(prev.v or 0) + (b.v or 0),  # sum volume
            vwap=prev.vwap if prev.vwap is not None else b.vwap  # first non-null vwap
        )

if dup_count_canon > 0 or no_ts_count_canon > 0:  # v0.8.1.25.0
    log.warning(  # v0.8.1.25.0
        "[WARN] [DEDUP_TS] v0.8.1.25.0 symbol=%s date=%s duplicates=%d no_ts=%d",
        sym, date_str, dup_count_canon, no_ts_count_canon
    )

# v0.8.1.25.0: Replace bars with canonicalized list preserving first-seen order
bars = [canon_by_ts[ts] for ts in canon_ts_order]  # v0.8.1.25.0

6) Telemetry correctness requirement (main per-symbol loop ONLY)

Because canonicalization happens before the existing pos_bar_by_ts duplicate counter, the old dup_count inside pos_bar_by_ts may become 0 even when duplicates existed.

To keep telemetry accurate in this codebase:

In the main per-symbol loop, locate the existing telemetry initialization block:

telemetry = {
    ...
    "dup_ts_count": 0,
    ...
}


Immediately after this telemetry dict is created, add:

# v0.8.1.25.0: keep dup-ts telemetry accurate after canonicalization (pos_bar_by_ts may now see 0)
telemetry["dup_ts_count"] = dup_count_canon  # v0.8.1.25.0


Do not add telemetry writes in the day-gate prepass (telemetry dict does not exist there).

7) What must NOT change (explicit do-not-touch list)

Do not change any of:

entry conditions

guard logic

stop/TP logic

position sizing

VWAP helpers / indicators

order of evaluation loops

existing pos_bar_by_ts duplicate-safe merge logic

any logging formats except the new [DEDUP_TS] v0.8.1.25.0 warning line

Do not rename existing variables.

Do not create helper functions.

Do not add imports.

8) Post-implementation validation (Copilot must not run)

User will run:

Repro days: SLMT (2025-10-23), NFE (2025-11-04)

Verify zero POS_MGMT_MISMATCH

Verify [WARN] [DEDUP_TS] v0.8.1.25.0 ... appears on contaminated days

Re-run previously tested ranges plus monthly ranges (Jan 2025, Feb 2025, Dec 2025)

Confirm v0.8.1.24.0 strategy behavior is preserved

Copilot must not run anything.

9) Success criteria (implementation-level)

Code compiles (no syntax errors).

Canonicalization occurs at both minute-load points.

No bars are dropped.

ts=None bars receive unique synthetic Bar.ts values (defensive correctness).

In main loop, telemetry reflects dup_count_canon.

No other behavior changes.

END COPILOT IMPLEMENTATION SPEC