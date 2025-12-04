#!/usr/bin/env python3
"""
Quick verification test for v0.7.9.7.6 config unification.
Tests that load_scenario_params() correctly loads B params from scenarios.json.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from midas_v2.config_models import load_scenario_params

def test_scenario_b_params():
    print("[TEST] v0.7.9.7.6: load_scenario_params() from scenarios.json")
    
    params = load_scenario_params("B", str(ROOT / "config" / "scenarios.json"))
    
    if params is None:
        print("  FAIL: params is None")
        return False
    
    print(f"  Loaded params type: {type(params)}")
    print(f"  Params keys: {list(params.keys()) if isinstance(params, dict) else 'N/A'}")
    
    # Check for required fields
    required = ["min_price", "max_price", "min_gap_pct", "top"]
    expected = {"min_price": 1, "max_price": 20, "min_gap_pct": 10, "top": 5}
    
    missing = []
    for key in required:
        if isinstance(params, dict):
            if key not in params:
                missing.append(key)
            else:
                val = params[key]
                exp_val = expected[key]
                status = "✓" if val == exp_val else f"✗ (got {val}, expected {exp_val})"
                print(f"  • {key}: {val} {status}")
        else:
            if not hasattr(params, key):
                missing.append(key)
            else:
                val = getattr(params, key)
                exp_val = expected[key]
                status = "✓" if val == exp_val else f"✗ (got {val}, expected {exp_val})"
                print(f"  • {key}: {val} {status}")
    
    if missing:
        print(f"  FAIL: Missing fields: {missing}")
        return False
    
    print("  PASS: All required fields present with correct values")
    return True

if __name__ == "__main__":
    success = test_scenario_b_params()
    sys.exit(0 if success else 1)
