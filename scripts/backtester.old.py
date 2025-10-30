from __future__ import annotations
import os
from typing import List
from ..utils_logging import setup_logging
from ..settings import Settings
from ..dataprov.csv_local import CsvLocalProvider
from ..strategy import SimpleBreakoutStrategy, StrategyParams
from ..risk import RiskManager
from ..broker.alpaca_stub import AlpacaBrokerStub

def run_backtest(date_str: str, universe_path: str, scenario_params: dict, settings: Settings, out_dir: str):
    log = setup_logging(level=settings.logging.level, log_dir=settings.logging.log_dir,
                        rotate_bytes=settings.logging.rotate_bytes, backup_count=settings.logging.backup_count)
    os.makedirs(out_dir, exist_ok=True)

    # Instantiate modules
    data = CsvLocalProvider(settings.data.data_root)
    risk = RiskManager(settings.risk)
    broker = AlpacaBrokerStub(dry_run=True)  # force dry-run in backtest

    # Load universe
    with open(universe_path) as f:
        symbols = [line.strip() for line in f if line.strip()]

    # Strategy
    strat = SimpleBreakoutStrategy(StrategyParams(**scenario_params))

    # Naive backtest loop (demo-scale)
    trades = []
    for sym in symbols:
        try:
            bars = data.load_minute_bars(sym, date_str)
        except FileNotFoundError as e:
            log.warning(str(e))
            continue

        position = None
        entry = None
        for i in range(len(bars)):
            bar = bars[i]
            # entry logic
            if position is None and strat.should_enter(bars, i) and risk.allow_new_trade():
                entry = bar.c
                position = {"symbol": sym, "entry": entry, "i": i}
                tp, sl = strat.targets(entry)
            # manage open position
            if position is not None:
                # check TP/SL within this bar range (approximation)
                if bar.high >= tp:
                    pnl = (tp - entry) * 100  # assume 100 shares for demo
                    trades.append((sym, "TP", pnl))
                    risk.on_trade_closed(pnl)
                    position = None
                elif bar.low <= sl:
                    pnl = (sl - entry) * 100
                    trades.append((sym, "SL", pnl))
                    risk.on_trade_closed(pnl)
                    position = None

    # Write results csv
    out_csv = os.path.join(out_dir, f"results_{date_str}.csv")
    with open(out_csv, "w") as f:
        f.write("symbol,outcome,pnl\n")
        for sym, outcome, pnl in trades:
            f.write(f"{sym},{outcome},{pnl:.2f}\n")
    return out_csv
