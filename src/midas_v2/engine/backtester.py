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

# Copilot: Define a dataclass called SimpleTradeSummary that captures the key fields
# we need to explain a single completed trade in simple language.
#
# Fields:
#   symbol: str
#   scenario: str           # e.g. "B"
#   side: str               # "long" or "short"
#   entry_time: datetime
#   exit_time: datetime
#   entry_price: float
#   exit_price: float
#   shares: int
#   gross_entry_value: float   # shares * entry_price
#   gross_exit_value: float    # shares * exit_price
#   pnl_usd: float             # gross_exit_value - gross_entry_value
#   risk_usd: float            # e.g. 35
#   stop_price: float
#   tp_price: float
#   sl_pct: float              # stop loss percent, e.g. 2.5
#   tp_pct: float              # take profit percent, e.g. 2.0
#   risk_per_share: float      # entry_price - stop_price (for long)
#   exit_reason: str           # "stop_loss", "take_profit", etc.
#
# Use @dataclass and type hints.
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SimpleTradeSummary:
    symbol: str
    scenario: str            # e.g. "B"
    side: str                # "long" or "short"
    entry_time: datetime     # when the trade was opened
    exit_time: datetime      # when the trade was closed
    entry_price: float
    exit_price: float
    shares: int
    gross_entry_value: float   # shares * entry_price
    gross_exit_value: float    # shares * exit_price
    pnl_usd: float             # gross_exit_value - gross_entry_value
    risk_usd: float            # e.g. 35
    stop_price: float
    tp_price: float
    sl_pct: float              # stop loss percent, e.g. 2.5
    tp_pct: float              # take profit percent, e.g. 2.0
    risk_per_share: float      # entry_price - stop_price (for long)
    exit_reason: str           # "stop_loss", "take_profit", etc.


def format_simple_trade_calcs(summary: SimpleTradeSummary) -> str:
    """
    Returns a child-friendly multi-line string explaining one trade.
    
    Includes:
    - Header with symbol, side, date, time, and scenario
    - Scenario description (especially for Scenario B)
    - Buy/sell explanation
    - Trade results (dollars, shares, prices)
    - Trading parameters (stop loss and take profit)
    - Risk calculation breakdown
    """
    entry_date = summary.entry_time.strftime("%Y-%m-%d")
    entry_time = summary.entry_time.strftime("%H:%M")
    exit_date = summary.exit_time.strftime("%Y-%m-%d")
    exit_time = summary.exit_time.strftime("%H:%M")
    
    # Clean up exit reason for display
    exit_reason_display = summary.exit_reason.replace("_", " ").lower()
    
    lines = []
    
    # Header
    lines.append(f"{'=' * 70}")
    lines.append(f"TRADE: {summary.symbol} | Side: {summary.side.upper()} | Entry: {entry_date} {entry_time} | Scenario: {summary.scenario}")
    lines.append(f"{'=' * 70}")
    lines.append("")
    
    # Scenario description
    if summary.scenario == "B":
        lines.append("SCENARIO B – Gap-and-Go:")
        lines.append("Buys small cheap stocks that gap up strongly before the market opens")
        lines.append("and keep going up after the open, using simple trend and momentum rules.")
        lines.append("")
    
    # Buy/Sell explanation
    lines.append("WHY WE TRADED:")
    lines.append("• We bought because the stock looked strong according to the rules.")
    lines.append(f"• We sold because the {exit_reason_display} was hit.")
    lines.append("")
    
    # Trade results
    lines.append("RESULTS:")
    lines.append(f"• Profit/Loss: ${summary.pnl_usd:,.2f}")
    lines.append(f"• Number of shares: {summary.shares}")
    lines.append(f"• Entry price: ${summary.entry_price:.2f}")
    lines.append(f"• Exit price: ${summary.exit_price:.2f}")
    lines.append(f"• Profit per share: ${(summary.exit_price - summary.entry_price):.2f}")
    lines.append(f"• Sale time: {exit_date} {exit_time}")
    lines.append("")
    
    # Trading parameters
    lines.append("TRADING PARAMETERS:")
    lines.append(f"• Stop loss: {summary.sl_pct:.1f}% (price: ${summary.stop_price:.2f})")
    lines.append(f"• Take profit: {summary.tp_pct:.1f}% (price: ${summary.tp_price:.2f})")
    lines.append("")
    
    # Risk section
    lines.append("RISK CALCULATION:")
    # Compute risk amount from risk per share and number of shares
    risk_amount = summary.risk_per_share * summary.shares
    lines.append(f"• Risk amount (USD): ${risk_amount:,.2f}")
    lines.append(f"• Risk per share: ${summary.risk_per_share:.2f}")
    if summary.risk_per_share > 0:
        approx_shares = risk_amount / summary.risk_per_share
        lines.append(f"• Approximate shares: {risk_amount:,.2f} ÷ {summary.risk_per_share:.2f} ≈ {approx_shares:.0f}")
    lines.append("")
    lines.append(f"{'=' * 70}")
    
    return "\n".join(lines)


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
    if scn == "UNKNOWN":
        scn = "B"

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
                    # Build and print a SimpleTradeSummary for this closed trade
                    try:
                        entry_time_dt = datetime.strptime(f"{date_str} {bars[position['i']].ts}", "%Y-%m-%d %H:%M")
                        exit_time_dt = datetime.strptime(f"{date_str} {bar.ts}", "%Y-%m-%d %H:%M")

                        exit_price = tp
                        gross_entry = qty * entry
                        gross_exit = qty * exit_price
                        # Resolve sl_pct and tp_pct with fallbacks (always float)
                        if isinstance(scenario_params, dict):
                            sl_candidate = scenario_params.get("sl_pct")
                            tp_candidate = scenario_params.get("tp_pct")
                        else:
                            sl_candidate = None
                            tp_candidate = None
                        sl_val = sl_candidate if sl_candidate is not None else norm_params.get("stop_loss_pct")
                        tp_val = tp_candidate if tp_candidate is not None else norm_params.get("take_profit_pct")
                        try:
                            sl_pct_final = float(sl_val) if sl_val is not None else 0.0
                        except Exception:
                            sl_pct_final = 0.0
                        try:
                            tp_pct_final = float(tp_val) if tp_val is not None else 0.0
                        except Exception:
                            tp_pct_final = 0.0

                        # Ensure risk_usd is never None
                        risk_value = getattr(settings.risk, "per_trade_risk", 0.0)
                        if risk_value is None:
                            risk_value = 0.0
                        risk_usd_final = float(risk_value)

                        summary = SimpleTradeSummary(
                            symbol=sym,
                            scenario=scn,
                            side="long",
                            entry_time=entry_time_dt,
                            exit_time=exit_time_dt,
                            entry_price=entry,
                            exit_price=exit_price,
                            shares=qty,
                            gross_entry_value=gross_entry,
                            gross_exit_value=gross_exit,
                            pnl_usd=pnl,
                            risk_usd=risk_usd_final,
                            stop_price=sl,
                            tp_price=tp,
                            sl_pct=sl_pct_final,
                            tp_pct=tp_pct_final,
                            risk_per_share=(entry - sl),
                            exit_reason="take_profit",
                        )
                        print()
                        print(format_simple_trade_calcs(summary))
                        print()
                    except Exception as e:
                        print(f"[SUMMARY_ERROR] {e}")

                    risk.on_trade_closed(pnl)
                    sizer.on_exit(pnl)  # NEW: update sizing state
                    trades_by_symbol[sym] += 1
                    cum_pnl += pnl
                    position = None
                elif bar.l <= sl:
                    pnl = (sl - entry) * qty
                    trades.append((sym, "SL", pnl))
                    # Build and print a SimpleTradeSummary for this closed trade
                    try:
                        entry_time_dt = datetime.strptime(f"{date_str} {bars[position['i']].ts}", "%Y-%m-%d %H:%M")
                        exit_time_dt = datetime.strptime(f"{date_str} {bar.ts}", "%Y-%m-%d %H:%M")

                        exit_price = sl
                        gross_entry = qty * entry
                        gross_exit = qty * exit_price
                        # Resolve sl_pct and tp_pct with fallbacks (always float)
                        if isinstance(scenario_params, dict):
                            sl_candidate = scenario_params.get("sl_pct")
                            tp_candidate = scenario_params.get("tp_pct")
                        else:
                            sl_candidate = None
                            tp_candidate = None
                        sl_val = sl_candidate if sl_candidate is not None else norm_params.get("stop_loss_pct")
                        tp_val = tp_candidate if tp_candidate is not None else norm_params.get("take_profit_pct")
                        try:
                            sl_pct_final = float(sl_val) if sl_val is not None else 0.0
                        except Exception:
                            sl_pct_final = 0.0
                        try:
                            tp_pct_final = float(tp_val) if tp_val is not None else 0.0
                        except Exception:
                            tp_pct_final = 0.0

                        # Ensure risk_usd is never None
                        risk_value = getattr(settings.risk, "per_trade_risk", 0.0)
                        if risk_value is None:
                            risk_value = 0.0
                        risk_usd_final = float(risk_value)

                        summary = SimpleTradeSummary(
                            symbol=sym,
                            scenario=scn,
                            side="long",
                            entry_time=entry_time_dt,
                            exit_time=exit_time_dt,
                            entry_price=entry,
                            exit_price=exit_price,
                            shares=qty,
                            gross_entry_value=gross_entry,
                            gross_exit_value=gross_exit,
                            pnl_usd=pnl,
                            risk_usd=risk_usd_final,
                            stop_price=sl,
                            tp_price=tp,
                            sl_pct=sl_pct_final,
                            tp_pct=tp_pct_final,
                            risk_per_share=(entry - sl),
                            exit_reason="stop_loss",
                        )
                        print()
                        print(format_simple_trade_calcs(summary))
                        print()
                    except Exception as e:
                        print(f"[SUMMARY_ERROR] {e}")

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