It documents everything we did this morning to fully fix and verify the per-scenario top behaviour for v0.7.9.6.5, and notes that the next design/implementation task is MACD from the web UI. At the end you’ll find the simple Git commands to tag and push this version.

# Midas_V2 v0.7.9.6.5 — Top (Per-Scenario) End-to-End Fix

**Date:** 2025-11-18  
**Scope:** Fix and finalise “top” handling so that per-scenario `top` is schema-valid, patched safely via the helper and UI, and correctly drives the range runner / scanner (topgappers) for scenario B. This closes the “top is half-wired” issue.

---

## 1. Starting Point and Problem

At the start of this session:

- The Phase 2b work from earlier versions had implemented:
  - `GET /current` and `POST /patch` in `tools/backend/param_helper.py`
  - UI support for editing a `top` value per scenario (Proposed → Preview → Apply)
- However, two issues remained:
  1. **Schema mismatch:** When running the range runner, `topgappers.py` raised a Pydantic `ValidationError`:

     > `ScenariosConfig: B.top extra_forbidden`

     Investigation showed that in `config/scenarios.json`, scenario `B` had:

     ```json
     "B": {
       "params": { ... },
       "top": 6
     }
     ```

     But `ScenariosConfig` defines a scenario with a `params` dict and does **not** allow arbitrary root keys like `top`, so `B.top` was invalid.

  2. **Scanner not using per-scenario top:** Even after setting `top` to 7 in the UI and verifying that `/current` and `/patch` worked, the range runner still selected more than 7 gappers per day. The number of top symbols in `universe_topgappers` was not controlled by `top`.

---

## 2. Changes Made in v0.7.9.6.5

### 2.1 Schema & Config: Move `top` into `params`

- We confirmed the schema for `ScenariosConfig`:

  - Each scenario entry has a `params` dictionary.
  - Extra root-level keys (like `B.top`) are forbidden by the Pydantic model.

- We fixed the data by:

  - Moving `top` from `B.top` into `B.params.top`, so scenario B now looks like:

    ```json
    "B": {
      "params": {
        "top": 7,
        ...
      }
    }
    ```

  - This resolved the Pydantic `extra_forbidden` error on `B.top`.

### 2.2 Helper: `/patch` and backup behaviour

We expanded `tools/backend/param/helper.py` so that:

- It now treats `top` as a **mutable field in `params` only**.
- New helper pieces were added (all commented with `v0.7.9.6.5`):

  - `MUTABLE_FIELDS = ("top",)`  
  - A `make_backup_path(...)` function to generate a timestamped backup filename like `scenarios.2025-11-18T19-34-11.bak.json`.
  - `save_scenarios_with_backup(...)`:
    - Writes the current `scenarios.json` to a `.bak.json` file.
    - Atomically writes the updated scenarios file via a `*.new` temp file and `Path.replace(...)`.
  - `get_scenario_object(...)` to locate a scenario entry regardless of structure (list vs dict).
  - `update_scenario_params(...)` to build `before_params` and `after_params` for a given `patch` (here, only `top` in this version).
  - New `@app.route("/patch", methods=["POST"])` implementation:
    - Accepts `?dry_run=1` or `?apply=1` and `{"top": <int>}` in JSON.
    - Validates that `top` is an integer `>= 1`.
    - On `dry_run=1`:
      - Returns `scenario`, `params_before`, `params_after`, `applied_fields`, `dry_run: true`.
    - On `apply=1`:
      - Updates `scenario["params"]["top"]`, writes `scenarios.json` via `save_scenarios_with_backup`, and returns `backup_file` name and `params_after`.

- We added PowerShell tests using `Invoke-WebRequest`:

  - Dry-run test:

    ```powershell
    Invoke-WebRequest "http://127.0.0.1:5001/patch?dry_run=1&scenario=B" `
      -Method POST -Headers @{ "Content-Type" = "application/json" } `
      -Body '{ "top": 7 }'
    ```

    Confirmed:
    - `params_before.top` was the old value (e.g. `6`), `params_after.top` was `7`.
    - No file write occurred (`dry_run: true`).

  - Apply test:

    ```powershell
    Invoke-WebRequest "http://127.0.0.1:5001/patch?apply=1&scenario=B" `
      -Method POST -Headers @{ "Content-Type" = "application/json" } `
      -Body '{ "top": 7 }'
    ```

    Confirmed:
    - `params_before.top` was `6`, `params_after.top` was `7`.
    - Response returned `backup_file: "scenarios.2025-11-18T19-34-11.bak.json"`.
    - `config/scenarios.json` was updated with `B.params.top = 7`.
    - The backup file existed in `config/`.

- We also validated that `GET /current?scenario=B` now returns:

  ```json
  { "scenario": "B", "params": { "top": 7, ... } }

2.3 UI verification (Parameters card)

With the dev server running (npm run dev in midas-ui):

In the Parameters (read-only) card for scenario B:

Click Load Current:

Current.top shows the latest value (e.g. 7).

Proposed.top is prefilled with the same value.

Change Proved.top to 8 and click Preview:

Validation enforces top >= 1.

Preview After.top updates to 8, no errors shown.

Click Apply:

UI sends POST /patch?apply=1 with { "top": 8 }.

On success:

Shows Applied top = 8. Backup: scenarios.<timestamp>.bak.json.

Current, Proposed, and Preview After all show 8.

scenarios.json now has B.params.top = 8.

This confirms the helper + UI + scenarios.json round-trip is correct and safe.

2.4 Range Runner & Scanner (topgappers) behaviour

With the backend helper still running on port 5001 and scenario B’s top set (e.g. 7), we re-ran:

python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B


After fixing the schema and helper:

topgappers.py no longer produced a Pydantic extra_forbidden error, because B.top was correctly inside params.

The logs now show:

[UNIVERSE] ... min_gap=10.0%
...
[UNIVERSE] Trimmed to Top-7 symbols (from N)


and out\20250805\universe_topgappers_...csv contained 7 tickers for scenario B, matching the top value in B.params.top.

Backtests for scenario B now use exactly 7 starting symbols per day, and range_summary shows:

2025-08-05 [B] -> trades=3, ...

2025-08-06 [B] -> trades=4, ...

Universe CSVs contain 7 tickers, confirming that the scanner respects top.

This confirms that top is now truly per scenario, stored in params, and drives the scanner/range runner as intended.

3. Outcome

With v0.7.9.6.5:

top is no longer an illegal root key; it lives in scenario["params"]["top"] per the Pydantic schema.

The helper’s /patch route:

Validates top, performs safe dry-run and apply with atomic backups.

Updates scenarios.json only through save_scenarios_with_backup.

The UI’s Parameters card:

Correctly loads, previews, and applies top.

Displays success messages including the backup filename.

The range runner and topgappers now honour top for scenario B, trimming the universe to top N symbols as configured in B.params.top.

This closes the long-standing issue where top was only “half wired”, and resolves the Pydantic extra_forbidden error and scanner mismatch.

4. Next Planned Work — MACD Design & Implementation from Web UI

The next major feature on the roadmap is to bring MACD fully under the same configuration and testing discipline:

Design step:

Decide exactly how MACD configuration should look under params and/or scanner in scenarios.json (e.g. macd_fast, macd_slow, macd_signal, macd_rise_bars).

Document this in a MACD spec (Docs/Phase_3_MACD_Design_v0.7.9.7.md) for Claude and Copilot, following the same approach as the Phase 2b specs.

Implementation step:

Extend param_helper.py and the UI to surface and validate MACD parameters (Preview + Apply + backups).

Extend the strategy code (e.g. strategy.py, update_scenario_params) so that MACD gating uses the configured values from params.

Add tests:

Pydantic validation.

Helper dry-run / apply.

Strategy behaviour under different MACD settings.

Add documentation and a new version tag (e.g. v0.7.9.7.x).

As with top, we will implement MACD in small, well-documented steps, with one change at a time and full test coverage.

5. Git Commands for v0.7.9.6.5

Once you’ve saved this documentation file and are ready to tag and push:

From the core repo (midas_V2):

cd C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working

git add -A
git commit -m "v0.7.9.6.5: Fix per-scenario top end-to-end (schema, helper/UI, scanner), add backups"
git tag -a v0.7.9.6.5 -m "v0.7.9.6.5: Top per-scenario fix completed"
git push
git push --tags


From the UI repo (midas-ui), after ensuring the updated MidasLocalRunnerUI.tsx and Docs/Phase_2b_UI_Apply_TopOnly_*.md are committed:

cd C:\Users\boydp\Desktop\midas-ui

git add -A
git commit -m "v0.7.9.6.5: UI Parameters Apply + top per-scenario wiring"
git tag -a v0.7.9.6.5 -m "v0.7.9.6.5: UI side of top fix complete"
git push
git push --tags


This locks in v0.7.9.6.5 as the version where top is fully functional and safely wired end-to-end, and clears the way to start the MACD design and implementation in the next version.