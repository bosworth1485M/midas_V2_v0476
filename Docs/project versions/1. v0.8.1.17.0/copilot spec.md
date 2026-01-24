# ============================================================
# COPILOT IMPLEMENTATION SPEC (FINAL — LOCKED)
# Midas_V2 v0.8.1.17.0
# Policy A: Stop-after-1-loss on MARGINAL days (close_gt_vwap_cnt == 1)
# Robust multi-file implementation (typed StrategyParams + scenario JSON + backtester)
# ============================================================

GOAL (EXACT)
Implement an OPTIONAL participation policy for Scenario B:

- On MARGINAL days only (is_marginal_day == True i.e., close_gt_vwap_count == 1),
- allow multiple trades UNTIL the first COMPLETED SL occurs,
- after the first SL, block all further entries for the rest of that day.

This is a POLICY / PARTICIPATION change only.
It must NOT change entry conditions, indicators, guards, VWAP logic, MACD logic, sizing, TP/SL math, or execution correctness rules.

DEFAULT must be OFF (baseline behavior identical when disabled).

FILES ALLOWED TO CHANGE
1) src/midas_v2/strategy.py
2) config/scenarios.json
3) src/midas_v2/engine/backtester.py

No other files.
No refactors.
No new helper modules.
No renames.
No moving large blocks around.

------------------------------------------------------------
WHY MULTI-FILE IS REQUIRED (CODE REALITY)
------------------------------------------------------------
- engine/backtester.py normalizes scenario_params via _normalize_strategy_params()
  which DROPS keys not present in StrategyParams.
- Therefore a toggle must exist on StrategyParams to survive normalization.

(Confirmed in your current backtester.py and strategy.py.)

------------------------------------------------------------
PART 1 — src/midas_v2/strategy.py
------------------------------------------------------------

A) Add a new StrategyParams field (typed, default OFF)
In the StrategyParams dataclass, add:

    marginal_stop_after_1_loss: bool = False  # v0.8.1.17.0

Place it near other day/policy-style toggles (e.g., after require_day_follow_through family is fine,
but keep it inside StrategyParams with a v0.8.1.17.0 comment).

B) Ensure create_strategy_params() loads this field from scenario params
In create_strategy_params(), in param_dict, add:

    "marginal_stop_after_1_loss": _get_strategy_param("marginal_stop_after_1_loss", False),

This guarantees that Scenario B can enable it via scenarios.json in a typed way.

Do not change any existing defaults or mapping logic beyond adding this one key.

------------------------------------------------------------
PART 2 — config/scenarios.json
------------------------------------------------------------

Under scenario "B" -> "params", add:

    "marginal_stop_after_1_loss": false

This makes the default state explicit and documents the feature.
(Leave it false for baseline parity; we will enable via env var for variant runs.)

Do not alter any other params.

------------------------------------------------------------
PART 3 — src/midas_v2/engine/backtester.py
------------------------------------------------------------

We must change TWO places in backtester.py, and add day-scoped state + logs.
Do not break existing marginal-day cap behavior when the new feature is disabled.

A) Feature enablement + day-start log (once per day)

After day classification is computed (is_marginal_day / day_class is available)
and after day_trade_count is initialized, compute enablement:

- scenario toggle:
    scenario_on = bool(getattr(strat.p, "marginal_stop_after_1_loss", False))

- env override (for A/B without editing JSON):
    env_on = os.getenv("MIDAS_MARGINAL_STOP1LOSS", "").strip().lower() in {"1","true","yes"}

- effective:
    marginal_stop1loss_enabled = bool(scenario_on or env_on)

Also compute a source string:
- "scenario" if scenario_on else "env" if env_on else "off"

Add a single INFO log line emitted once per day:
    log.info("MARGINAL_STOP_AFTER_1_LOSS v0.8.1.17.0: enabled=%s source=%s", marginal_stop1loss_enabled, source)

B) Day-scoped state

Where day_trade_count is initialized (currently:
    day_trade_count = 0
), add:

    marginal_sl_seen = False  # v0.8.1.17.0
    marginal_stop_trigger_logged = False  # v0.8.1.17.0

These must reset per day-run.

C) Replace marginal eligibility / cap logic (effective_day_gate_failed)

Current logic (v0.8.1.9.0) is:

- if is_marginal_day and day_trade_count < 1: allow eligibility
- elif is_marginal_day and day_trade_count >= 1: cap reached

This must be preserved EXACTLY when marginal_stop1loss_enabled == False.

When marginal_stop1loss_enabled == True, replace marginal logic with:

IF is_marginal_day and marginal_stop1loss_enabled:
    - If marginal_sl_seen is True:
        effective_day_gate_failed = True
        emit a log-once EARLY_REJECT for this symbol/day with reason:
            MARGINAL_STOP_AFTER_1_LOSS_BLOCK
        (use early_reject_logged latch: key f"{date_str}:{sym}:MARGINAL_STOP_AFTER_1_LOSS_BLOCK")
    - Else (no SL yet):
        effective_day_gate_failed = False
        emit a log-once INFO:
            "[INFO] v0.8.1.17.0 MARGINAL_STOP_AFTER_1_LOSS_ELIGIBLE sl_seen=False day_trade_count=%d"
        (use a new day-level latch; do not reuse marginal_eligible_logged if you prefer, but keep log-once)

ELSE (feature disabled):
    keep existing v0.8.1.9.0 behavior and existing log lines exactly:
    - MARGINAL_DAY_ELIGIBLE
    - MARGINAL_DAY_TRADE_CAP_REACHED

IMPORTANT:
- This policy affects ONLY marginal days.
- Hostile and healthy days must remain unchanged.
- Do not touch day_gate_failed computation, close_gt_vwap_count, or guard stack.

D) Update the v0.8.1.11.0 marginal VWAP window gate condition

Current code applies the marginal VWAP acceptance gate only when:
    is_marginal_day and day_trade_count < 1 and not effective_day_gate_failed ...

If we allow >1 marginal trades before the first SL, this gate MUST still apply
to those subsequent marginal entries until the stop triggers,
otherwise we accidentally weaken the marginal VWAP gate.

Therefore, change ONLY the IF condition to:

    if (require_day_follow_through and is_marginal_day and position is None and pending_entry is None and not effective_day_gate_failed
        and (
            (not marginal_stop1loss_enabled and day_trade_count < 1)
            or (marginal_stop1loss_enabled and not marginal_sl_seen)
        )
    ):

All inner logic of the VWAP window gate (VWAP calc, hits>=2 check, reject logging) must remain unchanged.

E) Trigger the stop on FIRST completed SL on a marginal day

In the SL-close branch (where outcome is set to "SL" or "ERR_SL_POS_PNL"),
after outcome is computed and before position is cleared,
add:

IF is_marginal_day and marginal_stop1loss_enabled and (outcome in {"SL","ERR_SL_POS_PNL"}) and (not marginal_sl_seen):
    marginal_sl_seen = True
    if not marginal_stop_trigger_logged:
        log.warning("[WHY] v0.8.1.17.0 MARGINAL_STOP_AFTER_1_LOSS_TRIGGERED date=%s symbol=%s pnl=%.2f day_trade_count=%d",
                    date_str, sym, pnl, day_trade_count)
        marginal_stop_trigger_logged = True

Notes:
- This must trigger only on COMPLETED SL, not on intrabar checks.
- day_trade_count increments later in the current code; log uses current value (pre-increment) which is fine.
- Do not change outcome correctness invariant logic.

F) Baseline parity requirement (non-negotiable)
When marginal_stop1loss_enabled == False:
- behavior must be identical to current baseline
- all existing log lines remain the same
- existing 1-trade marginal cap remains enforced

------------------------------------------------------------
HOW TO RUN A/B (NO JSON EDIT REQUIRED)
------------------------------------------------------------

Baseline (A): env var OFF
- run normally

Variant (B): enable env var in PowerShell on one line:
    $env:MIDAS_MARGINAL_STOP1LOSS="1"; python scripts\run_range_and_summarize.py ...

We will keep scenarios.json default false to ensure baseline parity.

------------------------------------------------------------
ACCEPTANCE CHECKS (MANDATORY)
------------------------------------------------------------

1) Toggle visibility
- Run any single day and confirm log appears once:
  "MARGINAL_STOP_AFTER_1_LOSS v0.8.1.17.0: enabled=... source=..."

2) Baseline parity
- With env OFF, rerun a known range and confirm totals match pre-change.

3) Policy behavior sanity
- On a marginal day with an SL, confirm:
  - TRIGGERED log appears once
  - subsequent entry attempts are blocked with EARLY_REJECT reason=MARGINAL_STOP_AFTER_1_LOSS_BLOCK

4) Marginal VWAP gate preserved
- When feature enabled and before SL occurs, confirm marginal VWAP window rejects can still fire for later attempts,
  proving the v0.8.1.11.0 gate is still applied beyond the first trade attempt.

END SPEC