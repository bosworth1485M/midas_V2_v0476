# src/midas_v2/engine/backtester.py
from __future__ import annotations
import os
from typing import List, Dict, Any
from collections import defaultdict

from ..utils_logging import setup_logging
from ..settings import Settings
from ..dataprov.csv_local import CsvLocalProvider
from ..strategy import SimpleBreakoutStrategy, StrategyParams
from ..risk import RiskManager
from ..broker.alpaca_stub import AlpacaBrokerStub

# NEW: adaptive sizing
from ..sizing import build_sizer_from_config  # <-- added

# v0.4.8: feature registry imports
from pathlib import Path  # v0.4.8
try:  # v0.4.8
    from midas_v2.features.registry import FeatureRegistry  # v0.4.8
except Exception:  # v0.4.8
    FeatureRegistry = None  # v0.4.8


def _normalize_strategy_params(scenario_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Make JSON config keys backward/forward compatible with StrategyParams.
    """
    params = dict(scenario_params)  # shallow copy

    # 1) Discover what StrategyParams actually accepts
    allowed = None
    try:
        from dataclasses import fields as dc_fields  # type: ignore
        allowed = {f.name for f in dc_fields(StrategyParams)}
    except Exception:
        pass
    if not allowed:
        try:
            # pydantic v2
            allowed = set(getattr(StrategyParams, "model_fields", {}).keys())  # type: ignore[attr-defined]
        except Exception:
            pass
    if not allowed:
        import inspect
        allowed = set(inspect.signature(StrategyParams).parameters.keys())

    # 2) Legacy aliases that are safe (only map when the *target* is accepted)
    alias = {
        "price_min": "min_price",
        "price_max": "max_price",
        "gap_min":   "min_gap_pct",
        "gap_max":   "max_gap_pct",
        "tp_pct":    "take_profit_pct",
        "sl_pct":    "stop_loss_pct",
        "gate_minutes": "start_bar",
        # NOTE: Do NOT force-map rise_bars -> macd_rise_bars unconditionally.
        # We'll bridge between them conditionally below.
    }

    for old, new in list(alias.items()):
        if old in params:
            if old in allowed:
                continue
            if new in allowed and new not in params:
                params[new] = params.pop(old)

    # 3) Bridge between macd_rise_bars and rise_bars depending on what StrategyParams supports.
    #    This prevents silently dropping whichever one the user/config/env provided.
    if "macd_rise_bars" in params and "macd_rise_bars" not in allowed and "rise_bars" in allowed and "rise_bars" not in params:
        # StrategyParams wants rise_bars; user/config provided macd_rise_bars
        params["rise_bars"] = params.pop("macd_rise_bars")
    elif "rise_bars" in params and "rise_bars" not in allowed and "macd_rise_bars" in allowed and "macd_rise_bars" not in params:
        # StrategyParams wants macd_rise_bars; user/config provided rise_bars
        params["macd_rise_bars"] = params.pop("rise_bars")

    # 4) Drop anything StrategyParams doesn't accept
    params = {k: v for k, v in params.items() if k in allowed}
    return params


def run_backtest(
    date_str: str,
    universe_path: str,
    scenario_params: dict,
    settings: Settings,
    out_dir: str,
    max_trades_per_symbol: int = 1,
    daily_max_loss: float = 1000.0,
):
    log = setup_logging(
        level=settings.logging.level,
        log_dir=settings.logging.log_dir,
        rotate_bytes=settings.logging.rotate_bytes,
        backup_count=settings.logging.backup_count,
    )
    os.makedirs(out_dir, exist_ok=True)

    # v0.4.8: load feature registry once (safe no-op if registry missing)
    if FeatureRegistry is not None:  # v0.4.8
        try:  # v0.4.8
            FeatureRegistry.load(Path(__file__).resolve().parents[2])  # v0.4.8
            log.debug("[FEATURES] registry loaded")  # v0.4.8
        except Exception as e:  # v0.4.8
            log.debug(f"[FEATURES] registry load skipped: {e}")  # v0.4.8

    # Instantiate modules
    data = CsvLocalProvider(settings.data.data_root)
    risk = RiskManager(settings.risk)
    broker = AlpacaBrokerStub(dry_run=True)

    # Load universe
    with open(universe_path) as f:
        symbols = [line.strip() for line in f if line.strip()]

    # Strategy
    norm_params = _normalize_strategy_params(scenario_params)
    log.info(f"[WHY] Using StrategyParams: {norm_params}")
    strat = SimpleBreakoutStrategy(StrategyParams(**norm_params))

    # v0.4.8: derive scenario id/name from settings (best-effort)
    scn = getattr(settings, "scenario", None) or getattr(settings, "scenario_name", None) or "UNKNOWN"  # v0.4.8

    # NEW: build adaptive sizer from full scenario params (not just normalized)
    sizer = build_sizer_from_config(scenario_params if isinstance(scenario_params, dict) else {})
    sizer.reset_daily()

    # Guardrail trackers
    trades_by_symbol = defaultdict(int)
    cum_pnl = 0.0

    trades = []
    for sym in symbols:
        try:
            bars = data.load_minute_bars(sym, date_str)
        except FileNotFoundError as e:
            log.warning(str(e))
            continue

        # v0.4.8: set per-symbol identity & scenario on the strategy
        try:  # v0.4.8
            strat.symbol = sym  # v0.4.8
            strat.session_date = date_str  # v0.4.8 (lets the strategy convert 'HH:MM' to epoch)
            strat.scenario_id = scn  # v0.4.8
        except Exception:
            pass  # v0.4.8

        position = None
        entry = None
        # Tiering context (scenario-level until per-symbol features are wired)
        tier_ctx = {
            # ONE-LINE PATCH: make sizing "score-aware" for this run
            "news_score": float(norm_params.get("news_min_score", 0.0)),
            "min_rvol_open": float(norm_params.get("min_rvol_open", 0.0)),  # scenario-level fallback
        }

        for i in range(len(bars)):
            bar = bars[i]

            # Guardrail: stop new trades if daily loss exceeded
            if daily_max_loss and cum_pnl <= -abs(daily_max_loss):
                continue

            # Guardrail: per-symbol trade cap
            if max_trades_per_symbol and trades_by_symbol[sym] >= max_trades_per_symbol:
                continue

            # entry logic
            if position is None and strat.should_enter(bars, i) and risk.allow_new_trade():
                entry = bar.c
                tp, sl = strat.targets(entry)

                # LEGACY default quantity
                qty = 100

                # NEW: adaptive sizing (if enabled)
                try:
                    tier = sizer.pick_tier(tier_ctx)
                    risk_usd = sizer.per_trade_risk_usd(tier)
                    if sizer.s.enabled and risk_usd > 0:
                        sized_qty = sizer.shares_for(entry, sl, risk_usd)
                        if sized_qty > 0:
                            qty = sized_qty
                            log.info(
                                f"[SIZE] {sym} tier={tier} risk_usd={risk_usd:.2f} "
                                f"entry={entry:.4f} sl={sl:.4f} qty={qty}"
                            )
                except Exception as e:
                    # On any issue, keep legacy qty
                    log.debug(f"[SIZE] fallback to legacy qty for {sym}: {e}")

                position = {"symbol": sym, "entry": entry, "i": i, "tp": tp, "sl": sl, "qty": qty}

            # manage open position
            if position is not None:
                tp = position["tp"]
                sl = position["sl"]
                qty = position["qty"]
                if bar.h >= tp:
                    pnl = (tp - entry) * qty
                    trades.append((sym, "TP", pnl))
                    risk.on_trade_closed(pnl)
                    sizer.on_exit(pnl)  # NEW: update sizing state
                    trades_by_symbol[sym] += 1
                    cum_pnl += pnl
                    position = None
                elif bar.l <= sl:
                    pnl = (sl - entry) * qty
                    trades.append((sym, "SL", pnl))
                    risk.on_trade_closed(pnl)
                    sizer.on_exit(pnl)  # NEW: update sizing state
                    trades_by_symbol[sym] += 1
                    cum_pnl += pnl
                    position = None

    # Write results csv
    out_csv = os.path.join(out_dir, f"results_{date_str}.csv")
    with open(out_csv, "w", newline="") as f:
        f.write("symbol,outcome,pnl\n")
        for sym, outcome, pnl in trades:
            f.write(f"{sym},{outcome},{pnl:.2f}\n")
    return out_csv