Here’s a clean, self-contained markdown document you can paste into:
Docs/versions/Midas_V2_v0.7.9.6.3_Top_Infrastructure.md
It documents what we did, why it matters, what’s still missing, and a clear plan (with Copilot use) to finish wiring top so the dev website controls the standard range runner.

# Midas_V2 v0.7.9.6.3 — Top Parameter Infrastructure & Schema Alignment

## Date
2025-11-18

## Purpose
Bring the `top` parameter under proper JSON + Pydantic control, wire it safely through the helper and UI (nested under `params`), and set up a clear plan to finish the `top` feature so that:

> `top` can be configured on the local website **and** is actually used by the *standard* range runner (scenario B, D, E, etc.), without leaving the feature half finished.

Catalyst runners are explicitly **out of scope** for this version and will be revisited later.

---

## 1. Work Completed in v0.7.9.6.3

### 1.1 Scenarios JSON migration for `top`

**Problem before:**  
`config/scenarios.json` had an illegal root-level field:

```json
"B": {
  ...
  "top": 6,
  "params": { ... }
}

The Scenario Pydantic model (from config_models.py) is defined as:
class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scanner: Optional[ScannerOverride] = None
    params: Dict[str, Any] = Field(default_factory=dict)

With extra="forbid", any unknown top-level key (like B.top) causes:


ValidationError: B.top → Extra inputs are not permitted


Fix:
Using Copilot, we created a migration script:


tools/backend/migrate_top_to_params.py


The script:


Opens config/scenarios.json


For each scenario:


If there is a root-level "top":


Removes it from the root: top_value = scenario.pop("top")


Ensures scenario["params"] exists and is a dict


Sets scenario["params"]["top"] = top_value






Before writing:


Creates config/scenarios.top_migration.bak.json (backup of original)




Writes the updated JSON with indent=2, sort_keys=True


Prints: Migrated N scenarios: ... and backup path


Result after running the script:
"B": {
  "params": {
    "...": "...",
    "top": 6
  }
}

No more root-level B.top. top is now nested under params for scenario B (and any others that had it).
Schema is aligned with Scenario(params=Dict[str, Any]).
Backups exist in config/ (e.g. scenarios.top_migration.bak.json).

1.2 Helper updated to use nested params for allowed fields
Original _filter_params behavior:
def _filter_params(scenario_obj: Dict[str, Any]) -> Dict[str, Any]:
    params = {}
    for key in ALLOWED_FIELDS:
        if key in scenario_obj:
            params[key] = scenario_obj[key]
    return params

This assumed top, price_min, price_max etc. lived at the root of the scenario, which is no longer correct.
New _filter_params behavior (via Copilot edits):
def _filter_params(scenario_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Return a dict containing only ALLOWED_FIELDS if present."""
    raw_params = scenario_obj.get("params") if isinstance(scenario_obj, dict) else {}
    if not isinstance(raw_params, dict):
        raw_params = {}
    params: Dict[str, Any] = {}
    for key in ALLOWED_FIELDS:
        if key in raw_params:
            params[key] = raw_params[key]
    return params



Now reads from scenario_obj["params"] only.


GET /current?scenario=B returns params from the nested dict.



1.3 /patch handler now writes params["top"] (not root top)
Original apply logic (simplified):
if apply_flag:
    data[key]["top"] = new_top_int  # ❌ root-level write
    backup_file = _write_with_backup(data, SCENARIOS_PATH)
    ...

This resurrected the invalid root-level top and would break Pydantic again.
New apply logic (via Copilot edits):
if apply_flag:
    # Ensure scenario_obj is a dict
    if not isinstance(scenario_obj, dict):
        return jsonify({"error": "unsupported scenario object"}), 400

    # Ensure nested params exists
    params_obj = scenario_obj.get("params")
    if not isinstance(params_obj, dict):
        params_obj = {}
        scenario_obj["params"] = params_obj

    # Write nested top only
    params_obj["top"] = new_top_int

    # Write with backup
    backup_file = _write_with_backup(data, SCENARIOS_PATH)

    # Recompute params_after from nested params
    params_after = _filter_params(scenario_obj)

    return jsonify({
        "scenario": scenario,
        "params_before": params_before,
        "params_after": params_after,
        "applied_fields": applied_fields,
        "dry_run": False,
        "backup_file": backup_file,
    }), 200

Dry-run (dry_run=1) uses the nested params too:


params_before = _filter_params(scenario_obj)


params_after = dict(params_before); params_after["top"] = new_top_int


So:


Dry-run shows how params.top would change (no write).


Apply writes nested params.top, creates a backup, and returns updated params_after.



1.4 Verified /current, dry-run, and apply
We tested via PowerShell:
Invoke-WebRequest -Uri "http://127.0.0.1:5001/current?scenario=B"
# -> {"params":{"top":6}, "scenario":"B"}

Invoke-WebRequest -Uri "http://127.0.0.1:5001/patch?dry_run=1&scenario=B" `
  -Method POST -Headers @{ "Content-Type" = "application/json" } `
  -Body '{ "top": 7 }'
# -> {"params_before":{"top":6}, "params_after":{"top":7}, "applied_fields":["top"], "dry_run":true}

Invoke-WebRequest -Uri "http://127.0.0.1:5001/patch?apply=1&scenario=B" `
  -Method POST -Headers @{ "Content-Type" = "application/json" } `
  -Body '{ "top": 7 }'
# -> {"params_before":{"top":6}, "params_after":{"top":7}, "backup_file":"scenarios.2025-11-18T19-34-11.bak.json", ...}

Results:


GET /current shows top from params (initially 6).


Dry-run correctly computes 6 → 7 but does not write.


Apply writes nested params.top = 7, creates a new backup file, and returns the changed value.


config/scenarios.json now contains:
"B": {
  "params": {
    ...
    "top": 7,
    ...
  }
}

and **no root-level "top": ..." under "B".

1.5 Dev UI: top is round-tripping through helper + JSON
With the dev UI running:


Load Current for scenario B:


Shows top = 7 in the Parameters card.




Changing Proposed top and clicking Preview:


Calls /patch?dry_run=1, uses nested params.top.




Clicking Apply:


Calls /patch?apply=1, updates nested params.top, shows the backup filename, and the UI syncs Current/Proposed/Preview After accordingly.




So: top (as params.top) is now a safe, backed-up, JSON-driven, UI-editable parameter.

2. What Is Still Not Done (To Be Finished Next)
Despite all the infrastructure, the standard scanner / range runner does not yet use params.top as Top-N tickers.
Currently:


The standard range runner (scripts/run_range_and_summarize.py → topgappers.py) chooses its Top-N symbols from:


scanner.json (global) + any Scenario.scanner overrides (if present), via ScannerConfig / ScannerOverride / merge_scanner(...)




It does not yet look at Scenario.params["top"] when deciding how many symbols to scan.
Therefore:


Changing top in the UI → B.params.top works and is safe,


but it does not currently change the number of symbols used in the standard range run.


This is the partially finished state we specifically want to resolve next, so that top is both:


JSON + helper + UI controlled,


and actually drives the scanner in the standard range runner.


Catalyst runners (with their own --top flags) are intentionally deferred and not touched in this version.

3. Next Steps — Plan to Make top Fully Functional
Goal for next version:

When I change top in the dev UI for scenario B and hit Apply, the standard range runner (scenario B) really uses that top value as its Top-N gappers parameter.

No catalysts; no new features; only finish top for the standard runner so the feature is not left half done.
3.1 Prerequisite: Work in a stable environment
These steps should be done:


At home or on a stable network


With ChatGPT available on the PC (ideally GPT-5.1)


With VS Code + Copilot working as they were


So we’re not fighting hotel Wi-Fi or browser issues while editing scanner code.

3.2 Step 1 — Identify where scanner Top-N is currently defined


Open config/config_models.py or src/midas_v2/config_models.py in VS Code.


Locate ScannerConfig and ScannerOverride:


Identify whether there is a field like top, top_n, max_symbols, etc.




Open scripts/topgappers.py (and any helper it calls):


Find where it reads scanner config (e.g., scanner.top) to decide how many tickers to consider.




Outcome:
We know precisely which field in the scanner config controls “Top-N gappers” today.

3.3 Step 2 — Decide on the canonical top source per scenario
To avoid duplication and confusion, we will have:


One canonical top per scenario that the scanner uses in the standard run.


My recommendation (to minimize churn and reuse what we already wired):


Treat Scenario.params["top"] as the per-scenario Top-N override.


That means:


scanner.json still holds a global default Top-N (if needed).


For each scenario (B, D, E…), params.top (in scenarios.json) overrides the scanner’s Top-N for that scenario.


If we later decide scanner.top is clearer, we can move it – but first we’ll make params.top really drive behavior so this feature is not half done.

3.4 Step 3 — Implement scanner Top-N override using params.top (with Copilot help)
Files to adjust:


config_models.py (where merge_scanner or similar lives)


Possibly scripts/topgappers.py (where scanner_for_B.top is used)


Conceptual change:
After constructing scanner_for_B (merged global + per-scenario scanner), add logic like:
# Pseudocode:
scenario = scenarios["B"]  # a Scenario object
params = scenario.params   # Dict[str, Any]
if "top" in params:
    scanner_for_B.top = params["top"]

This ensures:


params.top is actually used as the per-scenario Top-N.


Using Copilot (tiny steps):


Open the relevant file (e.g. config_models.py) in VS Code.


Add a comment block above the appropriate function, e.g.:
# We now want Scenario.params["top"] (if present) to override the
# scanner's top-N setting for that scenario in the standard run.
# After merging scanner + scenario, if params contains 'top', assign it
# to the effective scanner config's 'top' field.



In Copilot Chat (right panel), type:

“Please update this function so that if scenario.params contains 'top', it overrides the scanner’s top field for that scenario. Do not change anything else.”



Let Copilot propose a small patch and apply it.


Review the change to ensure:


It only sets scanner_for_B.top from params["top"] when present.


It does not introduce another top field or duplicate state.





3.5 Step 4 — Re-test helper/UI + JSON remain consistent
After scanner code changes:


Ensure config/scenarios.json still validates via ScenariosConfig.


Confirm helper /current still shows params.top.


Confirm /patch dry-run/apply still update nested params.top with backups.


No changes to helper/UI are needed yet; we’re just making the scanner honor what the helper/UI is already editing.

3.6 Step 5 — End-to-end tests for top
Scenario: B


Start the helper:
cd C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working
python tools/backend/param_helper.py --port 5001



Start the UI:
cd C:\Users\boydp\Desktop\midas-ui
npm run dev



Open the UI → Parameters card for B:


Load Current → Confirm current top.


Set Proposed top = 3, Preview, Apply.




Verify config/scenarios.json shows:
"B": { "params": { "top": 3, ... } }



Run the standard range runner:
cd C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B



Inspect logs/behavior:


Confirm that the scanner for B is now using top = 3 (e.g. number of gappers considered per day <= 3, or via debug logs if present).




Once this is confirmed, top will be fully wired:


JSON (scenarios.json)


Pydantic (ScenariosConfig/Scenario)


Helper (param_helper.py)


UI (MidasLocalRunnerUI)


Scanner/runner (ScannerConfig + overrides)


No half-done feature for top.

4. Version Tagging & Git Commands
After you have this markdown file in your core repo (e.g., Docs/versions/Midas_V2_v0.7.9.6.3_Top_Infrastructure.md), you can tag v0.7.9.6.3 to capture the current state (infrastructure completed; scanner wiring for top planned).
Core repo (Midas_V2)
From:
cd C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working
git add -A
git commit -m "v0.7.9.6.3: top infrastructure – scenarios.json migration + helper/UI nested params"
git tag -a v0.7.9.6.3 -m "v0.7.9.6.3: stabilize 'top' in JSON + helper; scanner wiring deferred"
git push
git push --tags

(If Git reports “nothing to commit”, you can still create the tag and push it.)
UI repo (midas-ui) — only if you changed UI in this version
If there were no UI changes in this exact step, you may skip tagging the UI for 0.7.9.6.3.
Otherwise:
cd C:\Users\boydp\Desktop\midas-ui
git add -A
git commit -m "v0.7.9.6.3: parameters panel confirmed for nested top"
git tag -a v0.7.9.6.3 -m "v0.7.9.6.3: UI supports nested top in params"
git push
git push --tags


5. Summary


top is now properly nested under params in scenarios.json and validated by Pydantic.


The helper + UI safely edit this nested params.top with backups.


We are not leaving top half done: this version completes the infrastructure.


Next version:
Finish wiring params.top into the standard scanner so that:

Editing top via the local website → updates scenarios.json → scanner uses that top → range runner behavior matches what the UI shows.

Catalyst runners remain explicitly deferred until after top is fully functional in the standard path.

::contentReference[oaicite:0]{index=0}
