#!/usr/bin/env python3
"""
Toggle micro-confirmation flags in ../scenarios.json (relative to this script).

Usage examples (run from project root):
  # Show current flags (no changes)
  python config\\toggles\\toggle_micro.py --show

  # Turn ON for B and E
  python config\\toggles\\toggle_micro.py --on --scenarios B E

  # Turn OFF for B only
  python config\\toggles\\toggle_micro.py --off --scenarios B

  # Turn ON for all scenarios present in the JSON
  python config\\toggles\\toggle_micro.py --on --all
"""

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
import sys

# Paths
HERE = Path(__file__).resolve().parent
SCENARIO_PATH = (HERE.parent / "scenarios.json").resolve()

# Micro keys & defaults
MICRO_DEFAULTS = {
    "use_micro_confirmation": True,
    "require_micro_continuation": True,
    "micro_resolution": "5s",
    "micro_window_secs": 60,
    "micro_min_green_ratio": 0.60,
    "micro_require_ema_reclaim": True,
    "micro_require_vwap_hold": False,
    "micro_allow_first_pullback": True,
}
MICRO_BOOL_KEYS = {
    "use_micro_confirmation",
    "require_micro_continuation",
    "micro_require_ema_reclaim",
    "micro_require_vwap_hold",
    "micro_allow_first_pullback",
}
MICRO_NUM_KEYS = {
    "micro_window_secs",
    "micro_min_green_ratio",
}

def load_cfg(path: Path) -> dict:
    if not path.exists():
        print(f"[ERROR] Not found: {path}")
        sys.exit(1)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def backup_then_save(path: Path, data: dict) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.stem}.{ts}.bak.json")
    if path.exists():
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"[backup] Saved previous file to {backup.name}")
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] Wrote {path}")

def show_flags(cfg: dict) -> None:
    print("\nCurrent micro flags per scenario:")
    for sid, s in cfg.items():
        p = s.get("params", {})
        row = {
            "use_micro_confirmation": p.get("use_micro_confirmation"),
            "require_micro_continuation": p.get("require_micro_continuation"),
            "micro_resolution": p.get("micro_resolution"),
            "micro_window_secs": p.get("micro_window_secs"),
            "micro_min_green_ratio": p.get("micro_min_green_ratio"),
            "micro_require_ema_reclaim": p.get("micro_require_ema_reclaim"),
            "micro_require_vwap_hold": p.get("micro_require_vwap_hold"),
            "micro_allow_first_pullback": p.get("micro_allow_first_pullback"),
        }
        print(f"  {sid}: {row}")
    print("")

def ensure_params(cfg: dict, sid: str) -> dict:
    """Ensure cfg[sid]['params'] exists and return it."""
    sc = cfg.setdefault(sid, {})
    return sc.setdefault("params", {})

def apply_on(params: dict) -> None:
    """Set micro ON and ensure all micro fields exist with defaults where missing."""
    for k, v in MICRO_DEFAULTS.items():
        if k not in params:
            params[k] = v
    # Normalize types just in case
    for k in MICRO_BOOL_KEYS:
        if k in params:
            params[k] = bool(params[k])
    for k in MICRO_NUM_KEYS:
        if k in params:
            # window secs is int, ratio is float
            params[k] = int(params[k]) if k == "micro_window_secs" else float(params[k])

def apply_off(params: dict) -> None:
    """Turn micro off by setting the two flags False (preserve other fields)."""
    params["use_micro_confirmation"] = False
    params["require_micro_continuation"] = False

def main():
    ap = argparse.ArgumentParser(description="Toggle micro-confirmation flags in scenarios.json")
    g = ap.add_mutually_exclusive_group(required=False)
    g.add_argument("--on", action="store_true", help="Enable micro-confirmation for target scenarios")
    g.add_argument("--off", action="store_true", help="Disable micro-confirmation for target scenarios")
    ap.add_argument("--scenarios", nargs="*", help="Scenario IDs to modify (e.g. B D E)")
    ap.add_argument("--all", action="store_true", help="Apply to all scenarios present in the JSON")
    ap.add_argument("--show", action="store_true", help="Show current micro flags and exit")
    args = ap.parse_args()

    cfg = load_cfg(SCENARIO_PATH)

    if args.show:
        show_flags(cfg)
        return

    # Determine targets
    if args.all:
        targets = list(cfg.keys())
    elif args.scenarios:
        targets = args.scenarios
    else:
        print("[ERROR] Provide --scenarios <IDs> (e.g. B D E) or use --all; or use --show.")
        sys.exit(1)

    # Validate targets
    missing = [sid for sid in targets if sid not in cfg]
    if missing:
        print(f"[ERROR] Scenario(s) not found: {', '.join(missing)}")
        sys.exit(1)

    if not (args.on or args.off):
        print("[ERROR] You must specify exactly one of --on or --off (or use --show).")
        sys.exit(1)

    # Apply
    for sid in targets:
        params = ensure_params(cfg, sid)
        if args.on:
            apply_on(params)
        else:
            apply_off(params)

    backup_then_save(SCENARIO_PATH, cfg)
    print("\nUpdated micro flags:")
    show_flags(cfg)

if __name__ == "__main__":
    main()