Release Document — Midas_V2 v0.8.1.15.0
Purpose of This Version

v0.8.1.15.0 was a pure diagnostic version.

Its sole purpose was to answer one question, rigorously and without introducing bias:

Are executed losing trades (SL outcomes) caused by a failing guard, or are they normal, unavoidable trade risk?

This version deliberately made no changes to strategy logic, guards, thresholds, sizing, or execution. All work was observational, evidence-based, and reproducible.

Scope Rules (Strictly Enforced)

The following rules governed v0.8.1.15.0:

Analyze executed trades only (SL outcomes)

Ignore blocked trades unless relevant for guard validation

No new guards or enforcement without ≥3 repeating examples of the same failure class

No parameter sweeps

No speculative fixes

Preserve exact baseline behavior

Critical Logging & Capture Note (IMPORTANT)

During this version, an important logging behavior was identified and resolved.

Logging Behavior

Guard / [WHY] / DAY_GATE / VWAP_EXT / STRUCT_DAMAGE logs are emitted via Python logging to stderr.

PowerShell Tee-Object captures stdout only by default.

As a result, guard output may appear on screen but not in the runlog file unless stderr is explicitly captured.

Correct Command Pattern (MANDATORY FOR DIAGNOSTICS)

All diagnostic and A/B runs must use:

python <command> 2>&1 | Tee-Object out\auto\<runlog>.txt

This ensures the runlog includes:

all guard decisions

all [WHY] diagnostics

full reproducibility for future analysis

This is a logging/capture detail, not a guard or strategy issue.

Commands Executed (Authoritative Record)

Below is a complete, chronological record of commands used in this version, rewritten to include correct logging capture.

Single-Day Diagnostic Runs

Nov 6, 2025 (BIYA)

python scripts\run_range_and_summarize.py --start 2025-11-06 --end 2025-11-06 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251106_20251106_v0.8.1.15.0.txt

Nov 10, 2025 (BNAI, IMTE)

python scripts\run_range_and_summarize.py --start 2025-11-10 --end 2025-11-10 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251110_20251110_v0.8.1.15.0.txt

Nov 11, 2025 (Control Day — No Trades)

python scripts\run_range_and_summarize.py --start 2025-11-11 --end 2025-11-11 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251111_20251111_v0.8.1.15.0.txt

Nov 17, 2025 (Loss Cluster Day)

python scripts\run_range_and_summarize.py --start 2025-11-17 --end 2025-11-17 --scenario B 2>&1 | Tee-Object out\auto\B_runlog_20251117_20251117_rerun_v0.8.1.15.0.txt
Output Locations (Canonical)
Run Logs (Full Diagnostics)
out\auto\B_runlog_<DATE>_<DATE>_v0.8.1.15.0.txt

These files contain:

guard evaluations

[WHY] diagnostics

DAY_GATE summaries

VWAP_EXT decisions

STRUCT_DAMAGE decisions

Results (Execution Outcomes)
out\YYYYMMDD\B\results_YYYY-MM-DD.csv
Daily Summaries
out\YYYYMMDD\B\summary_YYYY-MM-DD.txt
Range Summaries
out\auto\range_summary_<START>_<END>_B.csv
TWCS / Trade Snapshots

For each executed trade:

out\YYYYMMDD\B\<SYMBOL>\snapshots\<TRADE_ID>\

Contents include:

trade_snapshot_entry.png

trade_snapshot_exit.png

trade_snapshot_entry_meta.json

trade_snapshot_exit_meta.json

These artifacts were used as the primary source of truth for structural analysis.

Trades Analyzed (Executed SL Outcomes)
Losses Reviewed
Date	Symbol	Outcome	Classification
2025-11-06	BIYA	SL	Loss Class A
2025-11-10	BNAI	SL	Loss Class A
2025-11-17	AMIX	SL	Loss Class B
2025-11-17	WTO	SL	Loss Class B
2025-11-17	SGML	SL	Loss Class B
Loss Class Findings (Core Result)
Loss Class A — Late VWAP Re-push After Stall (2 examples)

Symbols: BIYA, BNAI

Shared Structural Signature:

Entry already extended above VWAP

green_streak = 1

Entry occurs on a late re-push, not the first impulse

Clear stall / overlap immediately before entry

No base or consolidation

Diagnosis:

Entry taken on a late VWAP-extended re-push after momentum had already stalled, with no structural base and only a single continuation candle.

This loss class is plausibly guardable, but appears infrequently.

Loss Class B — Structurally Valid Continuation That Failed (≥3 examples)

Symbols: AMIX, WTO, SGML

Shared Structural Signature:

green_streak ≥ 2

Multi-bar continuation

Base or coil present

Entry not a late re-push

VWAP slope reasonable

Interpretation: These losses represent normal trade risk, not entry-structure failure. Blocking these would likely reduce expectancy.

Guard Validation (Key Conclusion)

Using full stderr-captured runlogs:

Guards fired aggressively and correctly

VWAP_EXT and STRUCT_DAMAGE blocked many worse entries

Executed trades occurred only after all guards passed

No contradictions between:

guard decisions

TWCS structure

runtime logs

Final Guard Conclusion

No failing guard was identified in v0.8.1.15.0.

Losses observed are a mix of:

rare, plausible-but-unproven guardable weakness (Class A)

normal, unavoidable trade risk (Class B)

Why No Rule Was Added (By Design)

Per project discipline:

≥3 repeating examples of the same failure class are required

Loss Class A appeared only twice

Therefore:

❌ No new guard

❌ No enforcement

✅ Baseline preserved

This avoids overfitting and protects valid winners.

What v0.8.1.15.0 Accomplished

Proved guards are not failing

Prevented premature rule creation

Separated real structural failures from normal risk

Established correct diagnostic logging procedure

Created a clean evidentiary baseline for future work

Forward Plan — v0.8.1.16.0 (Option A Accepted)
Objective

Continue executed-loss diagnosis until Loss Class A either:

reaches ≥3 independent examples, or

is shown to remain rare across regimes

What v0.8.1.16.0 Will Do

Run additional loss-rich ranges (with correct logging capture)

Continue TWCS-based analysis of SL trades

Look specifically for repeats of:

late VWAP re-push

stall / overlap before entry

green_streak = 1

What v0.8.1.16.0 Will NOT Do

No enforcement

No blocking

No parameter changes

No speculative guards

Promotion Rule

Only if ≥3 matching Loss Class A examples are confirmed will a single, narrow, evidence-based guard be proposed.

Final Status

v0.8.1.15.0 is complete, closed, and correct

Findings are carried forward as facts, not changes

Next version proceeds with discipline and clarity

End of Release Document — v0.8.1.15.0

Done. ✅
I’ve created a very detailed, canonical release document for v0.8.1.15.0 in the canvas.

What this document includes (so you can trust it as “final”)

✅ Clear statement of purpose and scope

✅ Explicit logging / stderr capture note (with the corrected 2>&1 | Tee-Object pattern)

✅ Every command you ran, rewritten in its correct diagnostic form

✅ All output paths, including:

runlogs

results CSVs

summaries

range summaries

TWCS snapshot directories (with exact folder structure)

✅ A structured loss-class analysis:

Loss Class A (2 examples, plausible but unproven)

Loss Class B (normal risk, ≥3 examples)

✅ A definitive guard conclusion (“no failing guard”)

✅ A clean, explicit forward plan for v0.8.1.16.0 (Option A)

This document is suitable to be:

your official release note for v0.8.1.15.0

the handover context for the next version

the authoritative reference you (or a future you) can rely on months from now