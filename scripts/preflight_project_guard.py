#!/usr/bin/env python3
r"""
preflight_project_guard.py — quick sanity checks so we don't mix this repo with anything else.

What it prints:
- Repo path, Python executable
- Git branch and latest local tag
- scenarios.json path + SHA1 + key fields for D/E (so you can spot gate_minutes etc.)
- Warn if any TOML files mention "scenario" (legacy noise from the old project)
- .env presence + key booleans (no secrets)
- Presence of key scripts

Run from repo root:
  python scripts\preflight_project_guard.py
"""

from __future__ import annotations
import os, sys, json, subprocess
from pathlib import Path
from hashlib import sha1 as _sha1

ROOT = Path(__file__).resolve().parents[1]

def sh(cmd: str) -> str:
    """Run a shell command and return stdout (or an (err: ...) string)."""
    try:
        return subprocess.check_output(cmd, cwd=str(ROOT), shell=True, text=True).strip()
    except Exception as e:
        return f"(err: {e})"

def file_sha1(p: Path) -> str:
    h = _sha1()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

print("== Preflight Project Guard ==")
print(f"Repo root: {ROOT}")
print(f"Python   : {sys.executable}")

# Git info
branch = sh("git branch --show-current")
print(f"Branch   : {branch}")

# Latest tag (Windows-safe; avoid 'head')
tags_out = sh("git tag --sort=-creatordate")
latest_tag = "(none)"
if tags_out and not tags_out.startswith("(err"):
    lines = [ln for ln in tags_out.splitlines() if ln.strip()]
    latest_tag = lines[0] if lines else "(none)"
print(f"Latest tag (local): {latest_tag}")

# Config (JSON expected)
cfg = ROOT / "config" / "scenarios.json"
if cfg.exists():
    try:
        raw = cfg.read_text(encoding="utf-8")
        data = json.loads(raw)
        print(f"Config   : {cfg}  (sha1={file_sha1(cfg)})")
        # Handle either flat or {"params": {...}} shapes
        def get_params(block: dict) -> dict:
            return block.get("params", block) if isinstance(block, dict) else {}
        d = get_params(data.get("D", {}))
        e = get_params(data.get("E", {}))
        print(f"  D -> gate_minutes={d.get('gate_minutes')}, rise_bars={d.get('rise_bars')}, "
              f"min_pm_vol={d.get('min_pm_vol')}, tp_pct={d.get('tp_pct')}, sl_pct={d.get('sl_pct')}")
        print(f"  E -> gate_minutes={e.get('gate_minutes')}, rise_bars={e.get('rise_bars')}, "
              f"min_pm_vol={e.get('min_pm_vol')}, tp_pct={e.get('tp_pct')}, sl_pct={e.get('sl_pct')}")
    except Exception as e:
        print(f"Config   : {cfg} (read error: {e})")
else:
    print(f"Config   : MISSING -> {cfg}")

# Legacy TOML heads-up (shouldn't be used in this repo)
legacy_hits = []
for p in (ROOT / "config").glob("*.toml"):
    try:
        if "scenario" in p.read_text(encoding="utf-8", errors="ignore").lower():
            legacy_hits.append(p)
    except Exception:
        pass
if legacy_hits:
    print("[WARN] Found TOML files mentioning scenarios (legacy only, should not be used):")
    for p in legacy_hits:
        print("   -", p)

# .env quick check (no secrets printed)
dotenv = ROOT / ".env"
print(f".env     : {'present' if dotenv.exists() else 'MISSING'}")
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(dotenv)
    print(f"  POLYGON_API_KEY set? {bool(os.getenv('POLYGON_API_KEY'))}")
    print(f"  ALPACA_API_KEY  set? {bool(os.getenv('ALPACA_API_KEY'))}")
except Exception as e:
    print(f"  [WARN] python-dotenv not available ({e})")

# Key scripts presence
must = [
    "scripts/run_day_simple.py",
    "scripts/topgappers.py",
    "scripts/fetch_minutes_polygon.py",
    "scripts/prev_trading_day_polygon.py",
    "scripts/run_range_and_summarize.py",
    "scripts/view_results.py",
]
for rel in must:
    p = ROOT / rel
    print(f"{rel:<38} {'OK' if p.exists() else 'MISSING'}")

print("\n[OK] Preflight complete. If anything shows MISSING/WARN, fix that before running ranges.")