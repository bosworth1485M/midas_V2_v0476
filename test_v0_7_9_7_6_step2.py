#!/usr/bin/env python3
"""
Quick verification test for v0.7.9.7.6 Step 2 – strategy params from scenarios.json.
Tests that create_strategy_params() correctly loads B params from scenarios.json.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from midas_v2.strategy import create_strategy_params

def test_strategy_params_from_scenario_b():
    print("[TEST] v0.7.9.7.6 Step 2: create_strategy_params() with Scenario B")
    
    params = create_strategy_params(scenario_name="B")
    
    print(f"  Created StrategyParams with type: {type(params).__name__}")
    
    # Check for required fields and their values
    tests = [
        ("gate_minutes", 20),
        ("min_pm_vol", 30000),
        ("min_rvol_open", 2.0),
        ("rvol_open_minutes", 15),
        ("rise_bars", 3),
        ("green_body_min", 0.22),
        ("require_macd_rise", True),
        ("macd_rise_bars", 2),
        ("tp_pct", 2.0),
        ("sl_pct", 2.5),
        ("dip_reclaim", False),
    ]
    
    all_pass = True
    for field, expected in tests:
        actual = getattr(params, field, "NOT_FOUND")
        if actual == expected:
            print(f"  ✓ {field}: {actual}")
        else:
            print(f"  ✗ {field}: got {actual}, expected {expected}")
            all_pass = False
    
    if all_pass:
        print("\n  PASS: All strategy params from Scenario B are correct")
        return True
    else:
        print("\n  FAIL: Some strategy params don't match")
        return False

def test_strategy_params_with_overrides():
    print("\n[TEST] v0.7.9.7.6 Step 2: create_strategy_params() with overrides")
    
    # Load Scenario B, but override tp_pct
    params = create_strategy_params(scenario_name="B", tp_pct=3.0)
    
    print(f"  Override tp_pct to 3.0 (from JSON default 2.0)")
    test_pass = True
    if params.tp_pct == 3.0:
        print(f"  ✓ tp_pct: {params.tp_pct}")
    else:
        print(f"  ✗ tp_pct: got {params.tp_pct}, expected 3.0")
        test_pass = False
    
    # Other fields should still come from JSON
    if params.gate_minutes == 20:
        print(f"  ✓ gate_minutes (from JSON): {params.gate_minutes}")
    else:
        print(f"  ✗ gate_minutes: got {params.gate_minutes}, expected 20")
        test_pass = False
    
    if test_pass:
        print("\n  PASS: Overrides take precedence while JSON values are used for other fields")
    else:
        print("\n  FAIL: Override or JSON precedence test failed")
    return test_pass

if __name__ == "__main__":
    test1 = test_strategy_params_from_scenario_b()
    test2 = test_strategy_params_with_overrides()
    sys.exit(0 if (test1 and test2) else 1)
