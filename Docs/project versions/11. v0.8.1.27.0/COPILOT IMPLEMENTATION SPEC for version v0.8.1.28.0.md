COPILOT IMPLEMENTATION SPEC — ENFORCE ASCENDING GREEN CANDLES (Scenario B Only) — v0.8.1.28.0

0) Objective (ALIGNMENT + SAFETY)

Implement the Cameron-aligned continuation rule correctly for Scenario B:
- A “rise_bars / green candles” continuation must mean ASCENDING green candles on intact structure.
- Prevent trades like MAGN (2025-11-20) where “green candles” were counted mechanically but were not ascending in the entry structure.

This version introduces ONE conceptual change only:
✅ Enforce ASCENDING green candles (and reset/invalidates the count after structural damage).
❌ No changes to DAY_GATE throttle, MACD, VWAP, RVOL, TP/SL, sizing logic, or any other guards.

1) CRITICAL RULE: DO NOT RUN ANYTHING (NO EXECUTION)

Copilot must not run, invoke, simulate, or attempt to execute:
- python ...
- scripts/run_range_and_summarize.py
- any backtests
- any shell/PowerShell commands
- any “quick test” runs
- any validation steps

Implementation only.
Human-run validation commands are included at the end for later.

2) Non-negotiable constraints

2.1 Scenario scope
- Apply new “ascending green candles” enforcement to Scenario B only.
- All other scenarios must behave exactly as before.

2.2 Preserve existing parameters and meaning
- Keep using existing Scenario B params:
  - rise_bars (default 3)
  - green_body_min (default 0.22)
- Do NOT rename params.
- Do NOT change existing thresholds.
- Only change how the “rise bars / green streak” requirement is evaluated for Scenario B.

2.3 Do not refactor
- No moving functions, no new modules, no renaming, no architecture changes.
- Add minimal local logic near the existing rise/green evaluation.

2.4 Fail-closed
- If the new ascending logic cannot be evaluated safely (missing data, division by zero, etc.), fall back to the existing behavior and emit a clear warning log:
  "[WHY] v0.8.1.28.0 ASC_GREEN_FALLBACK symbol=XYZ ts=HH:MM reason=<...>"

2.5 Observability (required)
- Add explicit logs when a candidate is blocked by the new rule, so TWCS and logs clearly explain “why”.

3) Files allowed to change

Prefer one file only:

- src/midas_v2/engine/backtester.py

Config changes are NOT allowed in this version unless absolutely necessary.
(We are implementing correctness, not retuning.)

4) Proven landmarks to anchor placement (DO NOT GUESS)

Copilot must locate the existing “green / rise bars” logic for Scenario B using these anchors already present in backtester.py:

- Reading of Scenario B params:
  - rise_bars
  - green_body_min

- Existing code that checks “rising green candles / green streak” before entry.
  (Search for references to: rise_bars, green_streak, green_body_min, “GREEN”, “RISE”.)

- Existing WHY logging patterns:
  - log.warning("[WHY] ...")
  - log.info("[SIZE] ...")
  - TWCS/trade-card hooks (do not change them)

Implementation must be placed at the point where a candidate is accepted/rejected due to “rise/green continuation”.
Do NOT add a second separate gate elsewhere.

5) Desired new behavior (exact)

For Scenario B only, when the strategy requires rising/green candles (rise_bars = N, default 3):

A candidate PASS requires the last N qualifying candles (ending at the candidate’s confirm/entry decision point) to satisfy ALL:

5.1 Green + real body (existing definition)
For each of the N candles:
- close > open  (green)
- body_frac = abs(close - open) / (high - low)
- body_frac >= green_body_min
- high-low must be > 0 (otherwise candle invalid)

5.2 ASCENDING requirement (NEW)
For the sequence of N candles:
- closes must be strictly increasing:
  close[k] > close[k-1] for k = 2..N
- and (recommended, minimal extra safety):
  lows must be non-decreasing:
  low[k] >= low[k-1] for k = 2..N

If either ascending condition fails, the candidate FAILS.

5.3 Structural damage reset / invalidation (NEW)
If a structural damage event occurred after the first candle of the N-candle sequence, the candidate FAILS.

Definition of “structural damage event” (must reuse existing signals; do NOT invent new concepts):
- If the code already has a boolean like `struct_damage_seen` / `post_damage` / similar per-symbol state, use it.
- OR if Scenario B already has “auto_struct_damage_from_day_gate” / “damage” markers in the entry flow, reuse those.

Rule:
- If damage has been flagged at any time since the start of the N-candle sequence:
  - treat green continuation as invalid (reset to 0).
  - require a new ascending sequence after damage to trade.

IMPORTANT: This specifically blocks the MAGN-style failure:
- green candles elsewhere or after damage cannot qualify an entry in the damaged zone.

6) Implementation approach (minimal, deterministic)

6.1 Implement a helper block locally (not a refactor)
Do NOT create a new module.
Do NOT restructure the file.

Add a small local check near the existing continuation/rise evaluation:

Inputs needed:
- recent candles (1m bars already available in the decision context)
- rise_bars (N)
- green_body_min
- any existing “damage occurred” marker(s) the code already tracks

Output:
- asc_green_ok: bool
- asc_green_fail_reason: short string

6.2 Candidate rejection (Scenario B only)
If Scenario B requires rise_bars >= 1 and asc_green_ok is False:
- block entry
- log once per symbol/time:
  "[WHY] v0.8.1.28.0 ASC_GREEN_BLOCK symbol=XYZ ts=HH:MM reason=<...> N=<rise_bars> green_body_min=<...>"

Reasons should be one of:
- "not_enough_candles"
- "non_green_or_small_body"
- "non_ascending_close"
- "non_ascending_low"
- "post_damage_reset"
- "zero_range_candle"
- "fallback"

No spam: use existing log-once/dedupe patterns if present.

6.3 Keep existing green_streak / rise logic for non-B scenarios unchanged
Only Scenario B behavior changes.
For all other scenarios, do not alter the existing evaluation.

7) Required logs (OBSERVABILITY)

Add:
1) When Scenario B blocks due to ascending rule:
   "[WHY] v0.8.1.28.0 ASC_GREEN_BLOCK symbol=XYZ ts=HH:MM reason=<...> N=<...>"

2) Once per day (Scenario B only), announce the rule is enabled:
   "ASC_GREEN_ENFORCE v0.8.1.28.0: scenario=B enabled=True N=<rise_bars> green_body_min=<green_body_min>"

3) Fallback warning (only on exception):
   "[WHY] v0.8.1.28.0 ASC_GREEN_FALLBACK symbol=XYZ ts=HH:MM reason=<...>"

All new/modified lines must include inline comments:
- # v0.8.1.28.0 (ALIGNMENT): ...
- # v0.8.1.28.0 (SAFETY): ...
- # v0.8.1.28.0 (OBSERVABILITY): ...

8) Human-run validation (DO NOT RUN IN COPILOT)

8.1 Primary sanity cluster (the one that produced MAGN)
python scripts/run_range_and_summarize.py --start 2025-11-18 --end 2025-11-22 --scenario B 2>&1 | Tee-Object -FilePath .\out\auto\B_runlog_20251118_20251122_v0.8.1.28.0.txt

Grep:
Select-String .\out\auto\B_runlog_20251118_20251122_v0.8.1.28.0.txt -Pattern "ASC_GREEN_ENFORCE v0.8.1.28.0|ASC_GREEN_BLOCK|MAGN|DAY_GATE_THROTTLE v0.8.1.27.0|DAY_GATE_THROTTLE v0.8.1.28.0"

Expected:
- ASC_GREEN_ENFORCE appears.
- The MAGN trade should be blocked with ASC_GREEN_BLOCK (or never appear in results).

8.2 Protection cluster (time-diverse, 3–5 days)
Pick an older cluster (e.g., Aug 2025 or Jul 2025) and run the same command.
Goal:
- Ensure winners are not destroyed.
- Ensure the rule reduces structurally bad entries without collapsing to zero trades everywhere.

9) Acceptance checklist (human review)

Before committing:
- Only backtester.py changed.
- No changes to DAY_GATE throttle, sizing math, MACD/VWAP/RVOL/TP/SL.
- New logic only affects Scenario B continuation evaluation.
- Logs added as specified.
- New logic is deterministic and fail-closed.

END OF SPEC
