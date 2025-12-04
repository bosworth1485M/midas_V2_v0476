✅ A single, complete, polished documentation file for this version only (v0.7.9.7.6)
❗ No next-step material, no candle printing, no future design — ONLY what was done in this version.

This is ready for you to save as:

Docs/versions/Midas_V2_v0.7.9.7.6.md


It documents everything we accomplished today, cleanly and exhaustively, and it includes the one-step Git commands at the end.

Midas_V2 — Version v0.7.9.7.6
Full Documentation of Changes Completed in This Version
1. Version Purpose

The goal of v0.7.9.7.6 was to finally unify all Scenario B configuration paths so that:

JSON → Strategy → Backtester → Summary

all reflect one consistent source of truth.

We completed three major tasks:

Scanner knobs → JSON unification

Strategy knobs → JSON unification

Risk knobs → JSON unification, with a new diagnostic:

Error: fallback used

We also cleaned up old unused configuration files and validated everything through a full Scenario B run.

All Python changes were implemented only through Copilot, following your project rule.
All JSON modifications were also Copilot-generated — no manual edits anywhere.

2. Step-by-Step Documentation of What Changed in This Version
2.1 Step 1 — Scanner Configuration Unification
What we accomplished

topgappers.py now loads all scanner-critical parameters for Scenario B from:

config/scenarios.json → B.params


These parameters are now fully JSON-driven:

min_price

max_price

min_gap_pct

top

Technical mechanisms added

Added load_scenario_params() integration.

Introduced a safe get_param() function in topgappers.py.

Resolved scanner knobs with JSON > CLI precedence.

Ensured scanner logging reflects JSON values.

Behavior preserved

Scanner output for Scenario B remains:

price=[1..20]  min_gap=10%
[UNIVERSE] Trimmed to Top-5 symbols


No changes to trading behavior — only config control.

2.2 Step 2 — Strategy Configuration Unification

Strategy parameters now originate entirely from Scenario B’s JSON, unless overridden.

Parameters unified
Field	Value	Source
gate_minutes	20	JSON
min_pm_vol	30000	JSON
min_rvol_open	2.0	JSON
rvol_open_minutes	15	JSON
rise_bars	3	JSON
green_body_min	0.22	JSON
require_macd_rise	true	JSON
macd_rise_bars	2	JSON
tp_pct	2.0	JSON
sl_pct	2.5	JSON
dip_reclaim	false	JSON
How this was implemented

In backtester.py, Copilot replaced direct StrategyParams instantiation with:

SimpleBreakoutStrategy(
    create_strategy_params(scenario_name=scenario_name, **norm_params)
)


This ensures:

Strategy defaults come from Scenario B JSON.

CLI overrides are still supported.

The system remains backwards-compatible.

Validation

Logs now show:

[WHY] Using StrategyParams: {...}


with values matching the Scenario B Atlas perfectly.

2.3 Step 3 — Risk Configuration Unification + Diagnostic System
What we added to Scenario B JSON

Under B.params in scenarios.json:

"max_trades_per_symbol": 1,
"daily_max_loss": 1000.0

What we added to cli.py

A new diagnostic system:

Error: fallback used

Fallbacks now produce loud, multi-line warnings when JSON is incomplete.

These warnings stop silently-misconfigured scenarios.

Logic added

If a required key is missing from JSON and CLI:

Error: fallback used  (v0.7.9.7.6)
  • Key: max_trades_per_symbol
  • Scenario: B
  • Default value used: 1
  • Reason: Neither scenario JSON nor CLI provided a value.
  • Action: Fix config/scenarios.json or pass an explicit CLI override.

Behavior after fix

After Copilot added those fields into Scenario B JSON:

No fallback warnings appear.

Risk configuration in summaries is correct:

"max_trades_per_symbol": 1
"daily_max_loss": 1000.0


Backtester receives the correct guardrails:

max_trades_per_symbol=sc.get("max_trades_per_symbol", 1)
daily_max_loss=sc.get("daily_max_loss", 1000.0)

3. Cleanup Work Completed

The following unused files were officially retired and renamed with version tags:

File	Status
config/config_models.py	renamed to _UNUSED_v0.7.9.7.6.py
config/topgappers.json	renamed to _UNUSED_v0.7.9.7.6.json
scripts/Get-TopGappers.ps1	renamed to _UNUSED_v0.7.9.7.6.ps1

These are no longer used anywhere in the JSON-driven configuration pipeline.

4. Evidence: Scenario B Test Results After All Changes

Running:

python scripts/run_range_and_summarize.py --start 2025-08-01 --end 2025-08-02 --scenario B


Produced:

Exact scanner selection

Exact StrategyParams

Correct risk settings

No fallback errors

Same 3 trades (MWYN, NAMM, BTAI)

Identical PnL (−104.87)

All narrative outputs intact and accurate

This proves:

✔ The refactor changed configuration, not behavior.
5. Final One-Step Git Commands for v0.7.9.7.6

Copy & paste:

git add -A
git commit -m "v0.7.9.7.6: Unified scanner/strategy/risk config + added fallback error diagnostics + JSON cleanup"
git tag -a v0.7.9.7.6 -m "v0.7.9.7.6: Completed JSON unification for Scenario B with strict fallback error reporting"
git push
git push --tags


This produces:

A clear tagged version

A fully reproducible config

A clean historical checkpoint before v0.8.0

End of v0.7.9.7.6 Documentation

This file is now ready to be archived in:

Docs/versions/


When you’re ready, just say:

“I am ready for the next step.”

and I will provide the next version’s starting point — but only when you explicitly ask.