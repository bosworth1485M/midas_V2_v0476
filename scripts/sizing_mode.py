#!/usr/bin/env python3
"""
Simple sizing mode switcher so you don't have to remember flags.

Usage:
  python scripts/sizing_mode.py off      # disable sizing for ALL scenarios
  python scripts/sizing_mode.py on-b     # enable sizing for B only (others off)
  python scripts/sizing_mode.py on-bc    # enable sizing for B and C (others off)

Also supports:
  python scripts/sizing_mode.py status   # print sizing.enabled per scenario
"""

import sys, json
from pathlib import Path
import copy
PATH = Path("config/scenarios.json")

DEFAULT_BLOCK = {
    "enabled": False,
    "base_risk_usd": 50,
    "max_per_trade_risk_usd": 120,
    "max_daily_risk_usd": 300,
    "drawdown_throttle_after_losses": 3,
    "throttled_risk_factor": 0.5,
    "confidence_map": {"A": 1.8, "B": 1.0, "C": 0.5},
    "tier_rules": {
        "A": {"news_min_score": 3, "min_rvol_open": 2.4},
        "B": {"news_min_score": 2, "min_rvol_open": 2.0},
        "C": {"news_min_score": 1, "min_rvol_open": 1.5},
    },
}

SCENS = ("A","B","C","D","E","B_safe","D_backup","B_backup")

def load():
    try:
        return json.loads(PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"[ERR] {PATH} not found")
    except json.JSONDecodeError as e:
        sys.exit(f"[ERR] invalid JSON in {PATH}: {e}")

def ensure_block(j, key, enabled=None):
    if key not in j: return
    params = j[key].setdefault("params", {})
    if "sizing" not in params or not isinstance(params["sizing"], dict):
        params["sizing"] = copy.deepcopy(DEFAULT_BLOCK)
    if enabled is not None:
        params["sizing"]["enabled"] = bool(enabled)

def set_mode(mode: str):
    j = load()
    wants = set()
    if mode == "off":
        wants = set()
    elif mode == "on-b":
        wants = {"B"}
    elif mode == "on-bc":
        wants = {"B","C"}
    else:
        sys.exit("[ERR] unknown mode. use: off | on-b | on-bc | status")

    # ensure block exists for known scenarios, default disabled
    for k in SCENS:
        if k in j: ensure_block(j, k, enabled=False)
    # enable only the wanted ones
    for k in wants:
        if k in j: ensure_block(j, k, enabled=True)

    PATH.write_text(json.dumps(j, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] sizing mode set: {mode}")
    print_status(j)

def print_status(j=None):
    j = j or load()
    print("=== sizing.enabled status ===")
    for k in sorted(j.keys()):
        en = j[k].get("params",{}).get("sizing",{}).get("enabled","<absent>")
        print(f"{k:12s} {en}")

if __name__ == "__main__":
    mode = (sys.argv[1].strip().lower() if len(sys.argv)>1 else "status")
    if mode == "status":
        print_status()
    else:
        set_mode(mode)