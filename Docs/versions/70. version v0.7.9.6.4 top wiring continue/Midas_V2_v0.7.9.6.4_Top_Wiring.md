Here’s a clean, self-contained markdown doc for v0.7.9.6.4 that you can paste into:

Docs/versions/Midas_V2_v0.7.9.6.4_Top_Wiring.md

It captures:

What we did today

All the key VS Code / Copilot prompts

The tests and their outputs

The remaining gap (scenario not passed to topgappers)

The confusion about the second config_models.py in config/

The commands to send v0.7.9.6.4 to GitHub (after you’re happy with tests)

# Midas_V2 v0.7.9.6.4 — Top Wiring: Scanner top_n + Scenario.params["top"]

## Date
2025-11-21

## Purpose
Extend the `top` infrastructure so that:

- `top` can be configured via the local website (UI → helper → `scenarios.json`)
- The standard scanner and range runner move toward using this value
- Changes are versioned as v0.7.9.6.4 with clear comments

This version focuses on wiring `Scenario.params["top"]` into the scanner config (`top_n`) and updating `topgappers.py` to respect `scanner.top_n`. The last small step (passing `--scenario` into topgappers) remains open for tomorrow.

Catalysts and catalyst runners are **explicitly deferred**.

---

## 1. Files Touched Today

### 1.1 `src/midas_v2/config_models.py`

We confirmed that this is the canonical configuration model module used by imports:

```python
from midas_v2.config_models import ScannerConfig, ScenariosConfig, merge_scanner


There is a second file:

config/config_models.py

We have noted this is confusing and appears to be a snapshot/copy.
Action item (future): investigate what config/config_models.py does, whether it is used by any scripts (e.g., refresh_docs tooling), and whether it can be removed or clearly marked as generated/read-only to avoid confusion.

All logical changes for v0.7.9.6.4 were made in:

src/midas_v2/config_models.py

1.2 scripts/topgappers.py

This script controls:

The gap scanning

The list of symbols (gappers)

Trimming to Top-N symbols

Writing universe_sample.txt used by the range runner

Previously it used a hard-coded --top CLI argument (default Top-50) to decide how many symbols to keep.

For v0.7.9.6.4 we rewired it to respect scanner.top_n, which is now fed from Scenario.params["top"] via merge_scanner.

2. Changes in config_models.py (ScannerConfig, ScannerOverride, merge_scanner)

All changes in this file are tagged with v0.7.9.6.4 comments.

2.1 Added top_n to ScannerConfig and ScannerOverride

New field in ScannerConfig (global scanner defaults):

# v0.7.9.6.4: add top_n for per-scenario Top-N gappers
top_n: int = Field(ge=1, default=10)


Global default Top-N = 10

Validated as integer ≥ 1

Lives alongside existing scanner fields (price_min, price_max, etc.)

New field in ScannerOverride (per-scenario scanner overrides):

# v0.7.9.6.4: optional override for top_n
top_n: Optional[int] = Field(default=None, ge=1)


Optional per-scenario Top-N override

Can be used later in Scenario.scanner, if needed

2.2 Updated merge_scanner to use Scenario.params["top"]

Existing function:

def merge_scanner(global_scanner: ScannerConfig, scenario: Optional[Scenario]) -> ScannerConfig:
    base = global_scanner.model_dump()
    if scenario and scenario.scanner:
        overrides = scenario.scanner.model_dump(exclude_none=True)
        base.update(overrides)
    return ScannerConfig.model_validate(base)


Now extended with:

# v0.7.9.6.4: allow Scenario.params['top'] to override scanner top_n per scenario
if scenario and isinstance(scenario.params, dict) and "top" in scenario.params:
    try:
        base["top_n"] = int(scenario.params.get("top"))
    except Exception:
        # ignore non-int convertible values
        pass


So:

We still start with global_scanner.model_dump()

Apply scenario.scanner overrides (if any)

Then, if the scenario has params["top"], we override base["top_n"] with that value

Re-validate via ScannerConfig.model_validate(base)

This wires:

B.params.top → base["top_n"] → scanner.top_n

No extra fields are added at the scenario root; the JSON remains schema-compliant (Scenario.extra="forbid").

3. Changes in topgappers.py (Top-N trimming logic)

Previously, topgappers.py defined:

ap.add_argument("--top", type=int, default=50,
                help="Trim universe to top N gappers (default 50; set 0 to disable)")


and then used args.top to:

Limit preview list length

Trim the final universe to Top-N

We changed it so:

The scanner config is loaded, merged, and scanner.top_n is used instead

This is where Scenario.params["top"] flows into the universe trimming logic.

3.1 Where scanner is now loaded and merged

Near the top of topgappers.py (simplified):

scanner_global = ScannerConfig.model_validate_json(
    (ROOT / "config" / "scanner.json").read_text(encoding="utf-8")
)
scenario_obj = None
scn_path = ROOT / "config" / "scenarios.json"
if scn_path.exists():
    scenarios_map = ScenariosConfig.model_validate_json(
        scn_path.read_text(encoding="utf-8")
    ).root
    if args.scenario:
        scenario_obj = scenarios_map.get(args.scenario)
scanner = merge_scanner(scanner_global, scenario_obj)
price_min = scanner.price_min
price_max = scanner.price_max
min_gap_pct = scanner.min_gap_pct
max_gap_pct = scanner.max_gap_pct


Note:

Scenario.params["top"] is applied inside merge_scanner as top_n.

The next step (tomorrow) will be to ensure args.scenario is passed from run_day_simple.py into topgappers.py so that per-scenario overrides actually take effect. For now, since --scenario is not passed, scenario_obj is None and we use global defaults (top_n = 10).

3.2 Preview list now uses scanner.top_n

Old preview:

preview_n = args.top if isinstance(args.top, int) and args.top > 0 else len(rows)


New preview (v0.7.9.6.4):

# v0.7.9.6.4: use scanner.top_n (fed from Scenario.params['top']) instead of CLI args.top
preview_n = scanner.top_n if isinstance(getattr(scanner, "top_n", None), int) and scanner.top_n > 0 else len(rows)
for t, g, p in rows[:preview_n]:
    print(f"{t:<8} {g:>7.2f} {p:>8.4f}")

3.3 Universe trimming now uses scanner.top_n

Old trimming:

if not args.no_write:
    # Determine final list to write
    if isinstance(args.top, int) and args.top > 0:
        symbols_trimmed = [t for (t, _, _) in rows[:args.top]]
        ...


New trimming:

if not args.no_write:
    # Determine final list to write
    # v0.7.9.6.4: use scanner.top_n (fed from Scenario.params['top']) instead of CLI args.top
    top_n_val = scanner.top_n if isinstance(getattr(scanner, "top_n", None), int) else None
    if isinstance(top_n_val, int) and top_n_val > 0:
        symbols_trimmed = [t for (t, _, _) in rows[:top_n_val]]
        # Clear & truthful logging
        if len(rows) > top_n_val:
            print(f"[UNIVERSE] Trimmed to Top-{top_n_val} symbols (from {len(rows)})")
        else:
            print(f"[UNIVERSE] Using all {len(symbols_trimmed)} symbols (list shorter than Top-{top_n_val})")
    else:
        symbols_trimmed = [t for (t, _, _) in rows]
        print(f"[UNIVERSE] Using full list (no trim). Count={len(symbols_trimmed)}")

    write_universe(symbols_trimmed, Path(args.out))


args.top remains defined for backwards compatibility but is no longer used in trimming or preview.

4. Tests and Observed Behavior

We ran:

python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B


Before the changes, the logs showed:

[UNIVERSE] Using all 36 symbols (list shorter than Top-50)
...
[UNIVERSE] Using all 29 symbols (list shorter than Top-50)
...
[UNIVERSE] Using all 45 symbols (list shorter than Top-50)


After the v0.7.9.6.4 changes, the logs now show:

[UNIVERSE] Trimmed to Top-10 symbols (from 36)
...
[UNIVERSE] Trimmed to Top-10 symbols (from 29)
...
[UNIVERSE] Trimmed to Top-10 symbols (from 45)


Interpretation:

We have successfully switched from a hard-coded Top-50 limit to using scanner.top_n.

Since top_n in ScannerConfig has default=10, and scenario-specific overrides are not yet being applied, we see Top-10 everywhere.

Important:
Scenario.params["top"] is now used to override top_n in the merged scanner, but because topgappers is invoked without a --scenario argument, it always merges with scenario_obj = None, so only ScannerConfig defaults (top_n=10) are in effect.

This is the last missing link we will solve tomorrow:

Make run_day_simple.py pass --scenario B into topgappers.py, so the per-scenario params.top override (e.g., 3) is honored.

5. Summary of Today’s Results

Accomplished:

Added top_n to ScannerConfig (default 10) and ScannerOverride as an optional override.

Updated merge_scanner to override top_n from Scenario.params["top"] when present.

Updated topgappers.py so:

Preview list length uses scanner.top_n.

Universe trimming uses scanner.top_n.

Logging reflects Top-{top_n} instead of Top-50.

Verified that the scanner now respects ScannerConfig.top_n by trimming to Top-10 instead of Top-50.

Confirmed that the per-scenario params.top is now structurally wired into the scanner config (top_n), but scenario-specific behavior is not yet active because topgappers.py is not being told which scenario to use.

Still to do (planned for next version):

Update scripts/run_day_simple.py so that it passes --scenario B (and other scenario names) into scripts/topgappers.py.

After that, re-run the range tests with B.params.top set to e.g. 3; expect:

[UNIVERSE] Trimmed to Top-3 symbols (from 36) etc.

universe_sample.txt with 3 symbols instead of 10 for B.

Investigate config/config_models.py to confirm whether it is:

Just a copy for documentation,

Used by refresh_docs,

Or can be cleaned up/renamed to reduce confusion.
For now, do not modify config/config_models.py; treat src/midas_v2/config_models.py as the authoritative code.

6. Commands Run in VS Code / Copilot (Today)

To make it easier to reproduce, here are the main Copilot prompts used in VS Code:

6.1 To update config_models.py (v0.7.9.6.4)

You pasted (with slightly different version numbers as needed):

Please update src/midas_v2/config_models.py for version v0.7.9.6.4.

TASKS:

1. In ScannerConfig, add this new field directly under the other numeric fields:
    # v0.7.9.6.4: add top_n for per-scenario Top-N gappers
    top_n: int = Field(ge=1, default=10)

2. In ScannerOverride, add this new optional override field under the same section:
    # v0.7.9.6.4: optional override for top_n
    top_n: Optional[int] = Field(default=None, ge=1)

3. Update the merge_scanner function so that:
   After applying scenario.scanner overrides into base,
   if scenario.params contains "top", convert it to int and set:
       base["top_n"] = scenario.params["top"]

   Insert this comment immediately above the new code block:
       # v0.7.9.6.4: allow Scenario.params['top'] to override scanner top_n per scenario

4. Do NOT modify any other fields or logic.
5. Keep existing validation and structure intact.

At the end, the file should have:
- A new top_n field in ScannerConfig
- A new optional top_n in ScannerOverride
- merge_scanner updated so that params["top"] overrides top_n
- All new code tagged with v0.7.9.6.4 comments.


Copilot applied the changes and you verified them.

6.2 To update topgappers.py (v0.7.9.6.4/6.5)

You pasted a prompt that (after your minor version number change) asked Copilot to:

Load ScannerConfig, ScenariosConfig, and merge_scanner.

Build scanner_global from scanner.json.

Get scenario_obj from scenarios.json when args.scenario is present.

Use merge_scanner(scanner_global, scenario_obj) to get scanner.

Then replace uses of args.top with scanner.top_n for preview and trimming.

Add comments like:

# v0.7.9.6.4: use scanner.top_n (fed from Scenario.params['top']) instead of CLI args.top


These changes were applied and tested successfully.

7. Git Commands To Use After You’re Happy with Tests

Once you are satisfied with this version (v0.7.9.6.4) and don’t want to change anything else, you can tag and push it.

From the core repo:

cd C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working

git add -A
git commit -m "v0.7.9.6.4: wire scanner.top_n and Scenario.params['top'] into topgappers"
git tag -a v0.7.9.6.4 -m "v0.7.9.6.4: scanner uses top_n, helper/UI feed Scenario.params['top']; scenario wiring to topgappers still pending"
git push
git push --tags


(If Git says “nothing to commit, working tree clean”, you can still create the tag and push it — just skip the commit step.)

You can tag the UI repo later if/when you make UI changes specifically for this version.

8. Next Session Plan (Top Feature Only)

When you come back:

Open scripts/run_day_simple.py and locate where it invokes topgappers.py.

Update the subprocess call to include --scenario B (or the current scenario variable) so that topgappers can select the right scenario_obj and apply params.top from scenarios.json.

Re-run the range for scenario B with params.top = 3 and confirm:

[UNIVERSE] Trimmed to Top-3 symbols (from N) appears,

Universe file has 3 symbols for each day in the range.

Only after that will top be fully wired end-to-end for the standard runner.

Catalysts and database integration remain deferred to a later phase.


When you’re ready tomorrow, we’ll pick up from “Next Session Plan” and do the **one small update** to `run_day_simple.py` so `--scenario` is passed into `topgappers.py`.
::contentReference[oaicite:0]{index=0}