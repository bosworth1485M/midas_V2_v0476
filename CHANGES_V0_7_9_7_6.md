# v0.7.9.7.6: Config Unification – Scanner Knobs from JSON

## Overview
For Scenario B (and other scenarios), the scanner now reads its universe knobs (min_price, max_price, min_gap_pct, top) from `config/scenarios.json` via Pydantic config, while maintaining backward compatibility with CLI arguments.

## Changes Made

### 1. `src/midas_v2/config_models.py`
**New Function:** `load_scenario_params(scenario_name, scenarios_path=None)`
- Helper to load a scenario's params dict from scenarios.json
- Safely handles missing scenarios or invalid JSON
- Returns the params dict or None on error
- Tagged with v0.7.9.7.6 comments

### 2. `scripts/topgappers.py`
**Imports:**
- Added `from midas_v2.config_models import load_scenario_params` (v0.7.9.7.6)

**New Logic (after config load):**
- Load scenario params if `--scenario` is provided (v0.7.9.7.6)
- Define `get_param()` helper to resolve knobs from scenario params with fallback to CLI/defaults (v0.7.9.7.6)
- Resolve `min_price`, `max_price`, `min_gap_pct`, and `top` from scenario params (v0.7.9.7.6)

**Updated Logging (v0.7.9.7.6):**
- Price/gap line now uses resolved `price_min`, `price_max`, `min_gap_pct` values
- Universe trimming messages use resolved `top_n` variable
- Logs reflect the effective scanner settings from JSON or CLI

**Behavior:**
- When `--scenario B` is passed:
  - min_price, max_price, min_gap_pct, top are read from Scenario B params in scenarios.json
  - Logs show these JSON values
- When `--scenario` is not passed or scenario doesn't define a field:
  - Falls back to CLI arguments or defaults (existing behavior)
- When a scenario is provided but a field is missing in JSON:
  - Falls back to CLI/default for that field (defensive)

## Verification

### Scenario B Config
```json
"B": {
  "params": {
    "min_price": 1,
    "max_price": 20,
    "min_gap_pct": 10,
    "max_gap_pct": 40,
    "top": 5,
    ...
  }
}
```

### Test Results
Ran `test_v0_7_9_7_6.py` which confirms:
- `load_scenario_params("B")` successfully loads params dict
- All required fields present and match expected values:
  - min_price: 1 ✓
  - max_price: 20 ✓
  - min_gap_pct: 10 ✓
  - top: 5 ✓

## Backward Compatibility
- No changes to Pydantic models or JSON schema
- CLI arguments still work as fallback
- Non-scenario runs use CLI defaults (no change to behavior)
- Scenario runs without specific fields use CLI defaults for those fields

## Version Tagging
All new/modified code related to this change is marked with v0.7.9.7.6 comments for easy identification during code reviews.
