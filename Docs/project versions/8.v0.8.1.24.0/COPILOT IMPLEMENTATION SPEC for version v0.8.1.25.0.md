COPILOT IMPLEMENTATION SPEC — v0.8.1.25.0
Title: Deterministic minute-bar de-duplication to eliminate POS_MGMT_MISMATCH
Strict rule: Copilot must NOT run any commands, tests, or ranges. Implementation only.

High-level purpose (one sentence)
Implement a deterministic per-symbol/per-day minute bar canonicalization step that merges duplicate timestamps into a single canonical bar before any strategy evaluation or position management occurs, so bar (evaluation) and pos_bar_by_ts[bar.ts] (position management) always refer to the same OHLC, eliminating POS_MGMT_MISMATCH while preserving all existing trading logic.

0) COPILOT SAFETY RULES (MANDATORY)


DO NOT run any commands (no python ..., no range runner, no tests, no grep, no shell).


DO NOT attempt to execute the repo in any way.


DO NOT open terminals or invoke scripts.


Your job is code edits only, nothing else.


If you need to “verify,” verification means static inspection only (reading the file) and ensuring no syntax errors are introduced.

1) Hard constraints (DO NOT VIOLATE)


Single file only: src/midas_v2/engine/backtester.py


No refactors (no moving blocks, no renaming large sections, no formatting sweeps)


No strategy behavior changes (entries/exits/guards unchanged except outcomes on previously contaminated duplicate-ts data)


No config changes


No new dependencies


No new modules


Do not remove existing logs, counters, or telemetry fields


Add minimal new logs only if essential, and label them v0.8.1.25.0


Add inline comments near new/modified code including the version string v0.8.1.25.0



2) Proven bug (context you must preserve)


Raw minute CSVs can contain duplicate timestamps with conflicting OHLC (e.g., NFE 2025-11-04 has two 15:05 rows).


Current backtester merges duplicates only into pos_bar_by_ts (position mgmt), while evaluation uses raw bars[i], triggering POS_MGMT_MISMATCH.


The mismatch detector compares (bar.o, bar.h, bar.l, bar.c) vs (pos_bar.o, pos_bar.h, pos_bar.l, pos_bar.c) and logs mismatch. Do not change this detector.



3) Where to change (exact anchors)
There are two places where minute bars are loaded and then used downstream. You must canonicalize bars immediately after each load.
A) Day-gate prepass load (v0.8.1.3.0)
Anchor line:
bars = data.load_minute_bars(sym, date_str)  # v0.8.1.3.0

Immediately after this line, insert the canonicalization block described in Section 4.
B) Main per-symbol backtest load
Anchor line:
bars = data.load_minute_bars(sym, date_str)

Immediately after this line (and before building pos_bar_by_ts and before for i in range(len(bars)):), insert the canonicalization block described in Section 4.

4) Canonicalization policy (MUST MATCH existing pos_bar_by_ts merge)
When merging duplicates by timestamp ts, use this exact rule:


Open: keep the first open (prev.o)


High: max(prev.h, b.h)


Low: min(prev.l, b.l)


Close: use the last close (b.c)


Volume: sum volumes (prev.v or 0) + (b.v or 0)


VWAP: keep first non-null vwap (prev.vwap if prev.vwap is not None else b.vwap


This is the same policy already used in the existing pos_bar_by_ts “Duplicate-safe merge” block.

5) Implementation details (DO EXACTLY; no helper function)
Requirement: No helper function
Implement the canonicalization inline in both locations. Do not create new helper functions.
Canonicalization block (template)
Insert this block (adapt variable names only if needed). Include inline comment # v0.8.1.25.0.
Key requirements:


Preserve first-seen timestamp order (do not sort).


Replace bars with canonical bars list.


Track how many duplicates were merged (dup_count_canon).


Log a warning only when duplicates exist.


Template:
# v0.8.1.25.0: Canonicalize duplicate minute timestamps BEFORE evaluation and pos mgmt
canon_by_ts: dict[str, Bar] = {}
canon_ts_order: list[str] = []
dup_count_canon = 0

for b in bars:
    ts = getattr(b, "ts", None)
    if ts is None:
        # v0.8.1.25.0: defensive — keep bar as-is if no timestamp
        continue
    if ts not in canon_by_ts:
        canon_by_ts[ts] = Bar(ts=b.ts, o=b.o, h=b.h, l=b.l, c=b.c, v=b.v, vwap=b.vwap)
        canon_ts_order.append(ts)
    else:
        dup_count_canon += 1
        prev = canon_by_ts[ts]
        canon_by_ts[ts] = Bar(
            ts=b.ts,
            o=prev.o,
            h=max(prev.h, b.h),
            l=min(prev.l, b.l),
            c=b.c,
            v=(prev.v or 0) + (b.v or 0),
            vwap=prev.vwap if prev.vwap is not None else b.vwap
        )

if dup_count_canon > 0:
    log.warning("[WARN] [DEDUP_TS] v0.8.1.25.0 symbol=%s date=%s duplicates=%d", sym, date_str, dup_count_canon)

# v0.8.1.25.0: Replace bars with canonicalized list preserving first-seen order
bars = [canon_by_ts[ts] for ts in canon_ts_order]

Important note


Do NOT remove the existing pos_bar_by_ts merge block. After this fix, it should see few/no duplicates, but keep it unchanged to avoid refactors.



6) Expected effect (behavioral intent)
After this change:


Evaluation uses canonical bars:


bar = bars[i] uses canonical bars


strat.should_enter(bars, i) sees canonical bars




Position management uses canonical bars (via pos_bar_by_ts built from canonical bars)


Therefore POS_MGMT_MISMATCH should drop to zero on duplicate-ts days.


This is an execution correctness fix, not a strategy tweak.

7) Forbidden changes (explicit)


Do NOT change entry/exit logic


Do NOT change any guard thresholds or conditions


Do NOT change the POS_MGMT_MISMATCH detector block


Do NOT change how pos_bar_by_ts.get(bar.ts, bar) is used


Do NOT change CSV loader modules or other files


Do NOT add unit tests or run-time scripts (Copilot must not run anything)



8) Static verification only (no execution)
After editing, perform only static verification:


ensure file still parses (no missing parentheses/indentation)


ensure Bar is in scope where used (it already is for pos_bar_by_ts)


ensure sym and date_str are in scope in both insertion locations (they are in both loops)


No runtime checks.

END COPILOT IMPLEMENTATION SPEC — v0.8.1.25.0