#!/usr/bin/env python3
"""
Patch scenarios.json to add adaptive sizing blocks consistently.

- Ensures Scenario B has sizing.enabled = True
- Ensures A/C/D/E (+ backups if present) have sizing.enabled = False
- Idempotent; preserves all other keys/ordering as much as Python allows
- Creates a timestamped .bak backup before writing
- Optional --dry-run to see changes without saving

Usage:
  python scripts/patch_add_sizing.py
  python scripts/patch_add_sizing.py --path config/scenarios.json --dry-run
  python scripts/patch_add_sizing.py --enable B,C   # also enable sizing on C
"""

import argparse
import copy
import datetime as dt
import json
import os
import sys
from pathlib import Path

DEFAULT_PATH = Path("config/scenarios.json")

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

# Scenarios to ensure have a block (if present in file)
SCEN_KEYS_DEFAULT = ("A", "B", "C", "D", "E", "B_safe", "D_backup", "B_backup")


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", type=Path, default=DEFAULT_PATH, help="Path to scenarios.json")
    ap.add_argument(
        "--enable",
        type=str,
        default="B",
        help="Comma-separated scenario keys to force sizing.enabled=true (default: B)",
    )
    ap.add_argument("--dry-run", action="store_true", help="Show result but do not write file")
    return ap.parse_args()


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[ERR] File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERR] Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)


def ensure_block(obj: dict, scen_key: str, enabled=None):
    scen = obj.setdefault(scen_key, {}).setdefault("params", {})
    if "sizing" not in scen or not isinstance(scen["sizing"], dict):
        scen["sizing"] = copy.deepcopy(DEFAULT_BLOCK)
    # Only toggle enabled if caller asked us to
    if enabled is not None:
        scen["sizing"]["enabled"] = bool(enabled)


def main():
    args = parse_args()
    path: Path = args.path
    enable_set = {k.strip() for k in args.enable.split(",")} if args.enable else set()

    data = load_json(path)
    original = json.dumps(data, indent=2, ensure_ascii=False)

    # Apply: for any present scenario in SCEN_KEYS_DEFAULT, ensure a block exists (disabled)
    for key in SCEN_KEYS_DEFAULT:
        if key in data:
            ensure_block(data, key, enabled=False)

    # Force-enable on requested scenarios (if present)
    for key in enable_set:
        if key in data:
            ensure_block(data, key, enabled=True)

    # Summarize changes
    after = json.dumps(data, indent=2, ensure_ascii=False)
    changed = (after != original)

    # Print a small report
    print("=== sizing.enabled status by scenario ===")
    for key in sorted(data.keys()):
        try:
            en = data[key]["params"]["sizing"]["enabled"]
        except Exception:
            en = "<absent>"
        print(f"{key:12s} sizing.enabled = {en}")

    if args.dry_run:
        print("\n[DRY-RUN] No files written.")
        if changed:
            print("[DRY-RUN] Changes would be applied.")
        else:
            print("[DRY-RUN] No changes needed (already patched).")
        return

    if not changed:
        print("\n[OK] No changes needed. File already up to date.")
        return

    # Backup and write
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_suffix(path.suffix + f".{ts}.bak")
    try:
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        # Backup
        backup.write_text(original, encoding="utf-8")
        # Write updated
        path.write_text(after + "\n", encoding="utf-8")
        print(f"\n[OK] Patched {path}")
        print(f"[OK] Backup written to {backup}")
    except OSError as e:
        print(f"[ERR] Failed to write files: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()