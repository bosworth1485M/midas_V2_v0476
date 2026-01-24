COPILOT IMPLEMENTATION SPEC — v0.8.1.30.0
Title
- Temporarily disable ASC_GREEN for Scenario B only (A/B test) to see if it blocks valid Cameron-style continuation entries.

Primary hypothesis
- ASC_GREEN (v0.8.1.28.0) is overly strict and is suppressing valid continuation entries in Scenario B.
- Disable it ONLY for Scenario B, without touching any other guard, sizing, or logic.

Non-negotiable constraints
- No refactors. No new helper modules. No algorithm changes except disabling ASC_GREEN for Scenario B.
- Keep ASC_GREEN behavior unchanged for all non-B scenarios (even if they don’t currently use it).
- Must be reversible via one config flag.
- Must log clearly whether ASC_GREEN is enabled/disabled for Scenario B (once per run/day).
- Add inline comments containing “v0.8.1.30.0” on every changed/added line.

Files allowed to change (ONLY these)
1) src/midas_v2/engine/backtester.py
2) config/scenarios.json

Ground truth from current backtester.py (important)
- ASC_GREEN enforcement is currently hard-wired for Scenario B in TWO code paths:
  A) Normal entry veto: after `should_enter_now = strat.should_enter(bars, i)` it checks `if should_enter_now and (scenario_name or scn) == "B":` and can set `should_enter_now = False` with log `[WHY] v0.8.1.28.0 ASC_GREEN_BLOCK ...`
  B) Pending-entry confirmation path: when post-entry expansion confirms, it re-checks ASC_GREEN and can cancel the pending entry with log `[WHY] v0.8.1.28.0 ASC_GREEN_CANCEL_PENDING ...`
- v0.8.1.30.0 must disable BOTH A and B when Scenario B says so.

Implementation steps

Step 1 — Add scenario flag in config/scenarios.json
- Under Scenario B params, add:
  "disable_asc_green": true
- Do NOT add this flag anywhere else.
- Default behavior if flag missing must be “ASC_GREEN enabled” (i.e., current behavior).

Step 2 — Read the flag once in backtester.py (safe default)
In run_backtest(), after scenario_name/scn is known and scenario_params is available:
- Compute:
  asc_green_disabled_for_B = False by default
  If (scenario_name or scn) == "B" AND scenario_params is dict:
      asc_green_disabled_for_B = bool(scenario_params.get("disable_asc_green", False))

Add a log-once latch (similar style to existing latches):
- asc_green_state_logged = False (per run/day)
- When first entering the bar loop for Scenario B (or near the top once per run), emit exactly one log:
  If asc_green_disabled_for_B:
     log.info("ASC_GREEN v0.8.1.30.0: scenario=B enabled=False (disabled via scenarios.json)")
  Else:
     log.info("ASC_GREEN v0.8.1.30.0: scenario=B enabled=True")

IMPORTANT: This log must be emitted even if there are zero trades, so put it early enough
(e.g., right after throttle setup / before looping symbols, OR at first bar i==0 for first symbol).

Step 3 — Disable ASC_GREEN in the Normal Entry Veto path (A)
Locate the existing block:

  # v0.8.1.28.0 (ALIGNMENT): Scenario-B ascending-green enforcement (veto applied here)
  if should_enter_now and (scenario_name or scn) == "B":
      ...

Modify the condition so enforcement happens ONLY when not disabled:
- Change to:
  if should_enter_now and (scenario_name or scn) == "B" and (not asc_green_disabled_for_B):

- Do not change the internal ASC_GREEN logic at all; just bypass it when disabled.
- Keep the existing v0.8.1.28.0 log messages intact for the enabled path.

Step 4 — Disable ASC_GREEN in the Pending Entry Confirmation Cancel path (B)
Locate the existing block inside the “confirmed” pending entry section:

  # v0.8.1.28.0 (ALIGNMENT): Re-evaluate ASCENDING green candles at confirmation time for Scenario B
  if (scenario_name or scn) == "B":
      try:
         ...
         if not asc_ok:
             log.warning("[WHY] v0.8.1.28.0 ASC_GREEN_CANCEL_PENDING ...")
             pending_entry = None
             continue

Modify the condition so it runs ONLY when not disabled:
- Change to:
  if (scenario_name or scn) == "B" and (not asc_green_disabled_for_B):

- Again: do not change internal logic; just bypass entirely when disabled.

Step 5 — Keep ASC_GREEN_ENFORCE log behavior consistent
- Currently there is an “ASC_GREEN_ENFORCE v0.8.1.28.0: scenario=B enabled=True ...” log that fires once when the veto path runs.
- With v0.8.1.30.0:
  - If disabled: do NOT emit the v0.8.1.28.0 “enabled=True” enforcement announcement at all.
  - Instead, rely on the new v0.8.1.30.0 state log line (“enabled=False…”).
  - If enabled: keep existing v0.8.1.28.0 enforcement announcement as-is.

Step 6 — No other behavior changes
- Do not change throttle logic, DAY_GATE, damage logic, VWAP gates, risk sizing, etc.
- Do not change the early_reject_logged dedupe behavior.
- Do not rename ASC_GREEN log tags from v0.8.1.28.0. Those tags must remain to preserve historical meaning when enabled.

Acceptance checklist (developer self-check)
- Grep in backtester.py for "ASC_GREEN_BLOCK" and "ASC_GREEN_CANCEL_PENDING":
  - Both code blocks must be guarded by `and (not asc_green_disabled_for_B)` (Scenario B only).
- Grep for "ASC_GREEN v0.8.1.30.0":
  - Exactly one state log emitted per run/day (Scenario B), showing enabled True/False.
- Confirm config/scenarios.json has disable_asc_green only under Scenario B.
- Run existing test command(s) unchanged; no CLI additions.

Deliverable
- Provide a minimal diff affecting only:
  - config/scenarios.json (Scenario B adds disable_asc_green=true)
  - src/midas_v2/engine/backtester.py (read flag + gate both ASC_GREEN enforcement points + one state log line)
