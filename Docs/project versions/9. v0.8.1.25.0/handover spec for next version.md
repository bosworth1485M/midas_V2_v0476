echnical Handover — Starting Next Version

v0.8.1.25.0 completed an execution-correctness fix addressing duplicate minute timestamps in raw bar data. Minute bars are now deterministically canonicalized before use, ensuring that strategy evaluation, guard logic, and position management all reference the same OHLC per timestamp. This fully eliminates the previously observed POS_MGMT_MISMATCH failure mode.

Validation on known repro dates (2025-10-23, 2025-11-04) confirmed:

Duplicate timestamps remain present in the data (hundreds per symbol in some cases), proving the fix is exercised.

POS_MGMT_MISMATCH = False across all tested runs.

No regressions in execution flow, entry/exit handling, or trade lifecycle.

No changes to strategy logic, guards, parameters, or scenarios.

As a result, all post-v0.8.1.25.0 results should be treated as execution-clean and authoritative. Any losses observed from this version onward reflect true strategy behavior, not data or execution artifacts.

The next version should:

Remain strictly focused on Scenario B (baseline scenario).

Begin with TWCS (candle snapshot) analysis of real Scenario B losing trades.

Use snapshot analysis to identify structural failure modes (e.g., entry over-extension, weak continuation, immediate rejection).

Avoid parameter tuning or guard changes until failure modes are clearly understood and repeatable.

No further execution or infrastructure changes are expected unless new correctness issues are discovered.