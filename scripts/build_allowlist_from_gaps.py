#!/usr/bin/env python3
# scripts/build_allowlist_from_gaps.py
# Build a "must-keep" allowlist from a raw top-gappers list by recomputing gap% with Polygon.
# Tier-A threshold is controlled by --gap-thresh (default 50%).

import os
import sys
import json
import urllib.request
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parents[1]

def load_key() -> str:
    """
    Load POLYGON_API_KEY from ROOT/.env (if python-dotenv available) or environment.
    """
    try:
        from dotenv import load_dotenv  # optional
        load_dotenv(ROOT / ".env", override=True)
    except Exception:
        pass
    key = (os.environ.get("POLYGON_API_KEY") or "").strip().strip('"').strip("'")
    if not key:
        print("[ERR] POLYGON_API_KEY missing in .env or environment", file=sys.stderr)
        sys.exit(1)
    return key

def http_get_json(url: str, key: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}", "User-Agent": "midas_v2/allowlist/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def prev_trading_day_for(date_iso: str) -> str:
    """
    Ask helper script; fallback to previous calendar day on error.
    """
    try:
        helper = ROOT / "scripts" / "prev_trading_day_polygon.py"
        if helper.exists():
            r = subprocess.run(
                [sys.executable, str(helper), "--date", date_iso],
                capture_output=True, text=True, check=True
            )
            for line in (r.stdout or "").splitlines():
                if "Previous trading day for" in line and " is " in line:
                    return line.split(" is ")[-1].strip()
    except Exception:
        pass
    # simple fallback
    return (datetime.fromisoformat(date_iso).date() - timedelta(days=1)).isoformat()

def read_universe(path: Path):
    if not path.exists():
        return []
    return [ln.strip().upper() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]

def main():
    ap = argparse.ArgumentParser(description="Build allowlist (Tier-A gappers) by recomputing gap%% with Polygon.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--in", dest="inp", required=True, help="Input TXT: raw top-gappers (one ticker per line)")
    ap.add_argument("--out", dest="outp", required=True, help="Output TXT: allowlist (Tier-A)")
    ap.add_argument("--gap-thresh", type=float, default=50.0, help="Gap%% threshold for must-keep (default 50)")
    args = ap.parse_args()

    key = load_key()
    date_iso = args.date
    prev_iso = prev_trading_day_for(date_iso)

    tickers = read_universe(Path(args.inp))
    if not tickers:
        print("[WARN] Input universe is empty.")
        Path(args.outp).parent.mkdir(parents=True, exist_ok=True)
        Path(args.outp).write_text("", encoding="utf-8")
        return

    # Fetch grouped aggregates for prev and today
    u_prev  = f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{prev_iso}?adjusted=true"
    u_today = f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{date_iso}?adjusted=true"

    try:
        prev = http_get_json(u_prev, key)
        today = http_get_json(u_today, key)
    except Exception as e:
        print(f"[ERR] Polygon request failed: {e}", file=sys.stderr)
        sys.exit(2)

    prev_close = {}
    for r in (prev.get("results") or []):
        t = r.get("T"); c = r.get("c")
        if t and c is not None:
            try:
                prev_close[t] = float(c)
            except Exception:
                pass

    today_open = {}
    for r in (today.get("results") or []):
        t = r.get("T"); o = r.get("o")
        if t and o is not None:
            try:
                today_open[t] = float(o)
            except Exception:
                pass

    allow = []
    for t in tickers:
        pc = prev_close.get(t)
        op = today_open.get(t)
        gap = None
        if pc and op:
            try:
                gap = (op - pc) / pc * 100.0
            except Exception:
                gap = None
        if gap is not None and gap >= args.gap_thresh:
            allow.append(t)

    outp = Path(args.outp)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text("\n".join(allow) + ("\n" if allow else ""), encoding="utf-8")

    print(f"[ALLOWLIST] date={date_iso} prev={prev_iso} gap_thresh={args.gap_thresh}% -> wrote {len(allow)} -> {outp}")
    if allow:
        print("[ALLOWLIST] ", ", ".join(allow))

if __name__ == "__main__":
    main()