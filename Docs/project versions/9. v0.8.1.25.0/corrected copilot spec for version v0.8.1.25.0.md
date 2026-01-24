COPILOT IMPLEMENTATION SPEC for version v0.8.1.25.0
Execution Correctness Fix — Duplicate Minute Timestamp Canonicalization

BEGIN COPILOT IMPLEMENTATION SPEC

0) One-sentence objective (must match implementation)

Implement a deterministic, correctness-only canonicalization of duplicate minute timestamps so that strategy evaluation and position management use the same OHLCV per timestamp, eliminating POS_MGMT_MISMATCH caused by inconsistent duplicate-bar handling.

1) Strict scope rules (do not violate)

Single change only: canonicalize duplicate timestamps in minute bars before evaluation/position management.

No strategy logic changes (no entry/exit logic changes, no guard behavior changes, no parameter tuning).

No refactors (no new helpers, no moving blocks, no renames outside the new block).

Single file only: src/midas_v2/engine/backtester.py

Copilot must not run commands or run tests.

All new/modified lines must include inline comments containing v0.8.1.25.0 nearby.

2) File to change (exact)

src/midas_v2/engine/backtester.py

No other files.

3) What bug we are fixing (context, not code changes beyond canonicalization)

Minute data can contain duplicate timestamps with conflicting OHLC. Currently:

Strategy/guards iterate raw bars

Position management relies on merged pos_bar_by_ts
This can create evaluation vs position-management OHLC mismatches, causing POS_MGMT_MISMATCH and contaminating SL/TP outcomes.

We fix by canonicalizing duplicates into a single bar per timestamp before both evaluation and pos mgmt, using the same merge policy already used by pos_bar_by_ts:

open = first

high = max

low = min

close = last

volume = sum

vwap = first non-null (keep existing policy)

4) Implementation overview (two insertion points, no other changes)

You must implement the same canonicalization block at two points where minute bars are loaded:

A) Day-gate prepass load

There is a block like:

bars = data.load_minute_bars(sym, date_str)  # v0.8.1.3.0


Immediately after that line, insert the canonicalization block (template below), then proceed unchanged.

B) Main per-symbol backtest load

Inside the main for sym in symbols: processing, there is a line:

bars = data.load_minute_bars(sym, date_str)


Immediately after that line, insert the canonicalization block (same template), then proceed unchanged.

Do not change the existing pos_bar_by_ts duplicate-safe merge block. Leave it as-is.

5) Canonicalization template (paste inline, do not factor out)

Use this exact template at both insertion points (with only the obvious local variable names like sym, date_str, log, bars preserved). Keep it inline.

IMPORTANT UPDATES REQUIRED:

Do NOT drop bars when ts is missing/None. Preserve deterministically with a synthetic key.

Use generic timestamp typing (not str) to avoid mismatch if ts is datetime-like.

Emit a warning when duplicates (or ts-missing bars) are detected.

After canonicalization, replace bars with canonical list preserving first-seen order.

Paste this block exactly (adjust only indentation to match scope):

# v0.8.1.25.0: Canonicalize duplicate minute timestamps BEFORE evaluation and pos mgmt
canon_by_ts: dict[object, Bar] = {}  # v0.8.1.25.0
canon_ts_order: list[object] = []   # v0.8.1.25.0
dup_count_canon = 0                # v0.8.1.25.0
no_ts_count_canon = 0              # v0.8.1.25.0

for b in bars:  # v0.8.1.25.0
    ts = getattr(b, "ts", None)  # v0.8.1.25.0
    if ts is None:  # v0.8.1.25.0
        # v0.8.1.25.0: defensive — keep bar as-is if no timestamp (do NOT drop)
        no_ts_count_canon += 1  # v0.8.1.25.0
        ts = ("__NO_TS__", no_ts_count_canon)  # v0.8.1.25.0

    if ts not in canon_by_ts:  # v0.8.1.25.0
        canon_by_ts[ts] = Bar(  # v0.8.1.25.0
            ts=getattr(b, "ts", None),
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
            ts=getattr(b, "ts", None),
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

To keep existing day-level / per-trade telemetry accurate, in the main per-symbol load only (not the day-gate prepass), immediately after the canonicalization block add:

# v0.8.1.25.0: keep dup-ts telemetry accurate after canonicalization
telemetry["dup_ts_count"] = dup_count_canon  # v0.8.1.25.0


Do not add telemetry to the day-gate prepass (there is no telemetry dict there). Logging is sufficient there.

7) What must NOT change (explicit “do not touch” list)

Do not change any of:

entry conditions

guard logic

stop/TP logic

position sizing

VWAP helpers / indicators

order of evaluation loops

pos_bar_by_ts existing merge logic (leave it untouched)

Do not rename existing variables.

Do not introduce new imports.

Do not create helper functions.

Do not modify logging formats outside the new [DEDUP_TS] v0.8.1.25.0 warnings and the telemetry one-liner.

8) Post-implementation checks (Copilot must not run them)

After code change is saved, the user will run:

Repro days: SLMT (2025-10-23), NFE (2025-11-04)

Confirm zero POS_MGMT_MISMATCH

Confirm presence of [WARN] [DEDUP_TS] v0.8.1.25.0 ... duplicates=... on contaminated days

Re-run broader monthly ranges (Jan 2025, Feb 2025, Dec 2025) and previously tested ranges to ensure behavior is preserved.

Copilot: do not run anything.

9) Success criteria (implementation-level)

The code compiles (no syntax errors).

bars is canonicalized deterministically at both insertion points.

No bars are dropped due to missing timestamps (they remain present via synthetic key).

In main loop, telemetry["dup_ts_count"] reflects dup_count_canon.

No other behavior changes.

END COPILOT IMPLEMENTATION SPEC