COPILOT IMPLEMENTATION SPEC — DAY_GATE THROTTLE (Scenario B Only) — vNEXT
0) Objective (ALIGNMENT)

Implement the Cameron Alignment Plan step: convert DAY_GATE from a hard global block into a throttle for Scenario B only, so Scenario B behaves like successful Cameron projects (scale down on weak tape instead of shutting down).

1) CRITICAL RULE: DO NOT RUN ANYTHING (NO EXECUTION)

Copilot must not run, invoke, simulate, or attempt to execute:

python ...

scripts/run_range_and_summarize.py

any backtests

any shell/PowerShell commands

any “quick test” runs

any validation steps

This is implementation-only.
Validation commands are included for the human to run later, after code changes are complete.

If Copilot proposes “Let’s run…” or includes runtime output, do not proceed.

2) Non-negotiable constraints

Scenario scope: Apply throttle behavior to Scenario B only. All other scenarios must behave exactly as before.

One conceptual change: This version changes only DAY_GATE consequence behavior. No other entry logic, indicators, or filters change.

Preserve classification logic: DAY_GATE computations/classification (healthy/marginal/hostile + reasons) must remain identical.

Do not refactor: No large rewrites, no moving functions, no renaming modules, no architectural changes.

Fail-closed: If day class/throttle params cannot be determined, default to existing behavior (hard block) and log a clear warning.

Observability: Must print one summary line at runtime showing throttle state (enabled/disabled, class, risk_factor, max_trades).

3) Files allowed to change

Prefer one file if possible.

Primary target: src/midas_v2/engine/backtester.py

Config change (only if necessary and minimal): config/scenarios.json (Scenario B params only)

If Copilot wants to change additional files, stop and keep changes localized unless there is a clear, small reason.

4) Proven landmarks to anchor placement (do not guess)

Copilot must locate the existing DAY_GATE behavior using these already-present log strings:

DAY_GATE: CHECK enabled=True minutes=

DAY_GATE: FAILED

EARLY_REJECT reason=DAY_GATE_FAILED

REGIME_SUMMARY v0.8.1.21.0

MARGINAL_DAY_ELIGIBLE override_day_gate_failed=

Implementation must be anchored where EARLY_REJECT reason=DAY_GATE_FAILED is triggered today.

5) Desired new behavior (exact)

When DAY_GATE fails or day is classified hostile/marginal:

5.1 Scenario B behavior (NEW): throttle instead of hard block

Do NOT globally early-reject Scenario B for DAY_GATE_FAILED

Instead compute day class from existing logic and set throttle state:

Hostile day throttle (defaults):

max_trades_today = 1

risk_factor = 0.50

note = "hostile"

Marginal day throttle (defaults):

max_trades_today = 2

risk_factor = 0.75

note = "marginal"

Healthy day:

max_trades_today = existing behavior

risk_factor = 1.00

note = "healthy"

These are defaults. If a safe mechanism already exists for:

max trades/day or

risk factor / sizing scaling
reuse it, but keep the changes minimal and scoped to scenario B.

5.2 All other scenarios (UNCHANGED)

Preserve current behavior exactly:

If they hard-block on DAY_GATE failure today, they must keep hard-blocking.

If they use marginal-day override rules, keep those rules unchanged.

6) Implementation approach (minimal, deterministic, no refactors)
6.1 Add day-level throttle state (vNEXT comments required)

In backtester.py, add a tiny state structure stored per day run (local variables or a small dict) containing:

throttle_enabled: bool

throttle_class: str # "healthy"|"marginal"|"hostile"

throttle_risk_factor: float

throttle_max_trades: int

throttle_reason: str # keep existing reason text

All new/modified lines must include inline comments like:

# vNEXT (ALIGNMENT): ...
or

# vNEXT (OBSERVABILITY): ...
or

# vNEXT (SAFETY): ...

6.2 Replace hard block for Scenario B only (exact rule)

Where current code does:

On DAY_GATE failure → EARLY_REJECT reason=DAY_GATE_FAILED and stops all entries

Replace with:

If scenario == "B":

Do not early-reject.

Set throttle state using day class:

hostile → (1 trade, 0.50 risk)

marginal → (2 trades, 0.75 risk)

healthy → (no throttle)

Continue into candidate evaluation.

Else:

Keep current behavior unchanged (including EARLY_REJECT).

Fail-closed rule: If day class cannot be computed, fall back to old behavior (block) and log:

[WHY] vNEXT DAY_GATE_THROTTLE_FALLBACK reason=<why>

6.3 Enforce max_trades_today for Scenario B (SAFETY)

Implement (or reuse) a deterministic per-day counter for Scenario B:

day_trade_count_B

Before accepting a new entry for Scenario B:

If day_trade_count_B >= throttle_max_trades:

block entry

log once per symbol/day:

[WHY] vNEXT DAY_THROTTLE_MAX_TRADES_BLOCK symbol=XYZ ts=HH:MM limit=<n> class=<hostile/marginal>

No spam: use existing “log-once” / dedupe patterns if present.

6.4 Apply risk_factor to sizing for Scenario B (ALIGNMENT)

Find the per-trade risk sizing calculation (RiskManager / sizing logic). Apply:

effective_risk = base_risk * throttle_risk_factor

Only when:

scenario == "B"

throttle_enabled True

class in {"hostile","marginal"}

Do not alter sizing for other scenarios.

6.5 Preserve all entry gates unchanged (SAFETY)

Do not change:

MACD rise logic

rise_bars

RVOL open

vwap_extension_gate

gate_minutes

post-entry expansion gate

structural damage logic

TP/SL

The goal is participation realignment, not entry loosening.

7) Required new logs (OBSERVABILITY)

Add these logs (with vNEXT inline comments):

Once per day:

DAY_GATE_THROTTLE vNEXT: scenario=B enabled=<bool> class=<...> risk_factor=<x> max_trades=<n> reason=<...>

When blocking due to max trades:

[WHY] vNEXT DAY_THROTTLE_MAX_TRADES_BLOCK ...

If fallback occurs:

[WHY] vNEXT DAY_GATE_THROTTLE_FALLBACK ...

Do not remove existing DAY_GATE logs.

8) Human-run validation (DO NOT RUN IN COPILOT)

These commands are for the human to run after implementation. Copilot must not run them.

8.1 Sanity cluster (previously 0 trades)
python scripts\run_range_and_summarize.py --start 2025-11-18 --end 2025-11-22 --scenario B 2>&1 | Tee-Object -FilePath .\out\auto\B_runlog_B_20251118_20251122_vNEXT.txt

8.2 Protection cluster (time-diverse)

Pick an older 3–5 day window and run the same command.

8.3 Post-run grep (human-run)
Select-String -Path .\out\auto\B_runlog_B_20251118_20251122_vNEXT.txt -Pattern "DAY_GATE_THROTTLE vNEXT|DAY_THROTTLE_MAX_TRADES_BLOCK|DAY_GATE_THROTTLE_FALLBACK|EARLY_REJECT.*DAY_GATE_FAILED"


Acceptance:

DAY_GATE_THROTTLE vNEXT appears.

EARLY_REJECT ... DAY_GATE_FAILED should not appear for Scenario B in this run.

9) Safety / rollback

Throttle must be strictly under scenario == "B" condition.

If any uncertainty exists, fail-closed to old behavior with a warning.

Rollback should be a single commit revert.

10) Required docs updates (human)

After tests pass:

Update Docs/1. project status/PROJECT_STATUS.md

Update Docs/2. active guards ledger/ACTIVE_GUARDS_LEDGER.md

11) Copilot acceptance checklist (human review)

Before committing:

Only expected files changed (ideally just backtester.py)

All new lines include # vNEXT comments

No changes to entry filters

No changes to non-B scenarios

New logs exist exactly as specified