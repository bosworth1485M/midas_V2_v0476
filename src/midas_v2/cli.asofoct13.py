# src/midas_v2/cli.py
from __future__ import annotations
import argparse, json, os, sys
from .settings import load_settings
from .engine.backtester import run_backtest

def load_scenarios(path: str = "config/scenarios.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _env_float(name: str):
    v = os.getenv(name)
    if v in (None, "", "None"):
        return None
    try:
        return float(v)
    except ValueError:
        return None

def _env_int(name: str):
    v = os.getenv(name)
    if v in (None, "", "None"):
        return None
    try:
        return int(v)
    except ValueError:
        return None

def main():
    parser = argparse.ArgumentParser(prog="midas_v2")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_bt = sub.add_parser("backtest", help="Run a backtest on local CSV data")
    p_bt.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_bt.add_argument("--universe", required=True, help="Path to symbols list")
    p_bt.add_argument("--scenario", choices=["A", "B", "C", "D", "E"], default="B", help="Scenario preset")
    p_bt.add_argument("--out", default=None, help="Output directory")

    # Guardrails already staged previously
    p_bt.add_argument("--max-trades-per-symbol", type=int, default=1,
                      help="Max trades allowed per symbol for this session (default 1).")
    p_bt.add_argument("--daily-max-loss", type=float, default=1000.0,
                      help="Stop opening NEW trades once cumulative PnL reaches -X (default 1000).")

    # Opening RVOL gate (CLI flags + env fallback)
    p_bt.add_argument("--min-rvol-open", type=float, default=None,
                      help="Opening RVOL gate (e.g., 1.8 means 80% > prior day first N minutes).")
    p_bt.add_argument("--rvol-open-minutes", type=int, default=None,
                      help="Minutes window for opening RVOL comparison (e.g., 15).")

    # NEW: open wait gate (CLI + env fallback)
    p_bt.add_argument("--gate-minutes", type=int, default=None,
                      help="Wait this many minutes after the open before allowing entries.")

    args = parser.parse_args()
    cfg = load_settings()

    if args.cmd == "backtest":
        scenarios = load_scenarios()
        # copy so we can inject CLI/env overrides without mutating the JSON in memory
        sc = dict(scenarios[args.scenario]["params"])

        # Guardrails (always injected)
        sc["max_trades_per_symbol"] = args.max_trades_per_symbol
        sc["daily_max_loss"] = args.daily_max_loss

        # --- RVOL gate precedence: CLI > ENV > scenario/default ---
        min_rvol_open = sc.get("min_rvol_open")
        rvol_open_minutes = sc.get("rvol_open_minutes")

        # 1) CLI overrides
        if args.min_rvol_open is not None:
            min_rvol_open = float(args.min_rvol_open)
        if args.rvol_open_minutes is not None:
            rvol_open_minutes = int(args.rvol_open_minutes)

        # 2) ENV fallback
        if min_rvol_open is None:
            v = _env_float("MIDAS_MIN_RVOL_OPEN")
            if v is not None:
                min_rvol_open = v
        if rvol_open_minutes is None:
            v = _env_int("MIDAS_RVOL_OPEN_MINUTES")
            if v is not None:
                rvol_open_minutes = v

        # 3) Sensible default for window if threshold present but window missing
        if (min_rvol_open is not None) and (rvol_open_minutes is None):
            rvol_open_minutes = 15

        if min_rvol_open is not None:
            sc["min_rvol_open"] = min_rvol_open
        if rvol_open_minutes is not None:
            sc["rvol_open_minutes"] = rvol_open_minutes

        # --- Open wait (gate) precedence: CLI > ENV > scenario/default ---
        gate_minutes = sc.get("gate_minutes")
        if args.gate_minutes is not None:
            gate_minutes = int(args.gate_minutes)
        if gate_minutes is None:
            v = _env_int("MIDAS_GATE_MINUTES")
            if v is not None:
                gate_minutes = v
        if gate_minutes is not None:
            sc["gate_minutes"] = gate_minutes

        out_dir = args.out or os.path.join(cfg.out_root, args.date.replace("-", ""), args.scenario)

        # Brief banner so SAFE runners show key toggles in logs
        print("[CFG] scenario=", args.scenario,
              " gate_minutes=", sc.get("gate_minutes"),
              " min_rvol_open=", sc.get("min_rvol_open"),
              " rvol_open_minutes=", sc.get("rvol_open_minutes"),
              " green_streak=", sc.get("green_streak"),
              " macd_rise_bars=", sc.get("macd_rise_bars"),
              " max_trades_per_symbol=", sc.get("max_trades_per_symbol"),
              " daily_max_loss=", sc.get("daily_max_loss"),
              file=sys.stderr)

        out_csv = run_backtest(args.date, args.universe, sc, cfg, out_dir)
        print(f"[OK] Backtest complete -> {out_csv}")

if __name__ == "__main__":
    main()