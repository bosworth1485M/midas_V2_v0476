# src/midas_v2/cli.py
from __future__ import annotations
import argparse, json, os, sys
from .settings import load_settings
from .engine.backtester import run_backtest

def load_scenarios(path: str = "config/scenarios.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

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

    # NEW (v0.3.21): Opening RVOL gate plumbing
    p_bt.add_argument("--min-rvol-open", type=float, default=None,
                      help="Opening RVOL gate (e.g., 1.5 means 50%% > prior day first N minutes).")
    p_bt.add_argument("--rvol-open-minutes", type=int, default=15,
                      help="Minutes window for opening RVOL comparison (default 15).")

    args = parser.parse_args()
    cfg = load_settings()

    if args.cmd == "backtest":
        scenarios = load_scenarios()
        sc = dict(scenarios[args.scenario]["params"])  # copy so we can inject CLI overrides

        # Inject guardrails into params (engine/strategy can read them from params)
        sc["max_trades_per_symbol"] = args.max_trades_per_symbol
        sc["daily_max_loss"] = args.daily_max_loss

        # Inject RVOL-gate params only if provided/meaningful
        if args.min_rvol_open is not None:
            sc["min_rvol_open"] = float(args.min_rvol_open)
            sc["rvol_open_minutes"] = int(args.rvol_open_minutes)

        out_dir = args.out or os.path.join(cfg.out_root, args.date.replace("-", ""), args.scenario)

        # Optional: brief banner so SAFE runners show key toggles in logs
        print("[CFG] scenario=", args.scenario,
              " min_rvol_open=", sc.get("min_rvol_open"),
              " rvol_open_minutes=", sc.get("rvol_open_minutes"),
              " rise_bars=", sc.get("rise_bars"),
              " max_trades_per_symbol=", sc.get("max_trades_per_symbol"),
              " daily_max_loss=", sc.get("daily_max_loss"), file=sys.stderr)

        out_csv = run_backtest(args.date, args.universe, sc, cfg, out_dir)
        print(f"[OK] Backtest complete -> {out_csv}")

if __name__ == "__main__":
    main()