# v0.8.1.0.0: TWCS core (snapshots)
from __future__ import annotations
import os
import sys  # v0.8.1.0.0: needed for stderr messages from TWCS hooks
from typing import List, Dict, Any
from collections import defaultdict

from ..utils_logging import setup_logging
from ..settings import Settings
from ..dataprov.csv_local import CsvLocalProvider
from ..strategy import SimpleBreakoutStrategy, StrategyParams, create_strategy_params  # v0.7.9.7.6: import factory
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

# v0.8.1.0.0: TWCS core (snapshots)
from midas_v2.snapshots import twcs  # v0.8.1.0.0: TWCS core (snapshots)
# v0.8.1.0.1: TWCS minute window loader
from midas_v2.dataio.twcs_minute_loader import load_twcs_minute_window  # v0.8.1.0.1
# v0.8.1.0.2: TWCS indicators stub
from midas_v2.indicators.twcs_indicators import build_twcs_indicators  # v0.8.1.0.2: TWCS indicators stub
# v0.8.1.0.4: 1-second TWCS window loader
from midas_v2.dataio.twcs_second_loader import load_twcs_second_window  # v0.8.1.0.4
# v0.8.1.0.5: TWCS PNG rendering
from midas_v2.plotting.twcs_plotter import plot_twcs_snapshot  # v0.8.1.0.5

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
    gap_pct: float | None = None
    top_rank: int | None = None
    universe_size: int | None = None
    open_price: float | None = None
    pm_volume: float | None = None
    price_band_passed: bool | None = None
    gap_band_passed: bool | None = None
    pm_volume_passed: bool | None = None
    # Key scenario knobs (friendly)
    top: int | None = None
    price_min: float | None = None
    price_max: float | None = None
    min_gap_pct: float | None = None
    max_gap_pct: float | None = None
    min_pm_vol: float | None = None
    min_rvol_open: float | None = None
    rvol_open_minutes: int | None = None
    gate_minutes: int | None = None
    macd_rise_bars: int | None = None
    require_macd_rise: bool | None = None
    rise_bars: int | None = None
    green_body_min: float | None = None

    # Raw snapshots for completeness
    strategy_params: dict[str, Any] | None = None
    risk_snapshot: dict[str, Any] | None = None


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

        # CONTEXT BEFORE TRADE (show if any context is available)
        has_ctx = any(
            v is not None
            for v in (
                summary.gap_pct,
                summary.open_price,
                summary.pm_volume,
                summary.top_rank,
                summary.universe_size,
            )
        )
        if has_ctx:
            lines.append("CONTEXT BEFORE TRADE:")
            # Gap
            if summary.gap_pct is not None:
                if summary.gap_band_passed is not None:
                    status = "PASSED" if summary.gap_band_passed else "FAILED"
                    lines.append(f"• Gap % at open: {summary.gap_pct:.2f}% ({status} gap band)")
                else:
                    lines.append(f"• Gap % at open: {summary.gap_pct:.2f}%")

            # Pre-market volume
            if summary.pm_volume is not None:
                if summary.pm_volume_passed is not None:
                    status = "PASSED" if summary.pm_volume_passed else "FAILED"
                    lines.append(f"• Pre-market volume: {summary.pm_volume:,.0f} ({status} minimum volume)")
                else:
                    lines.append(f"• Pre-market volume: {summary.pm_volume:,.0f}")

            # Price at open
            if summary.open_price is not None:
                if summary.price_band_passed is not None:
                    status = "PASSED" if summary.price_band_passed else "FAILED"
                    lines.append(f"• Price at open: ${summary.open_price:.2f} ({status} price band)")
                else:
                    lines.append(f"• Price at open: ${summary.open_price:.2f}")

            # Rank among gappers
            if summary.top_rank is not None and summary.universe_size is not None:
                lines.append(f"• Rank among gappers: #{summary.top_rank} of {summary.universe_size}")

            lines.append("")


        # RULES WE USED BEFORE TAKING THIS TRADE (friendly explanation + raw)
        try:
            have_rules = any([
                summary.gate_minutes is not None,
                summary.min_pm_vol is not None,
                summary.min_rvol_open is not None,
                summary.rise_bars is not None,
                summary.macd_rise_bars is not None,
                summary.tp_pct is not None,
                summary.sl_pct is not None,
                bool(summary.risk_snapshot),
                bool(summary.strategy_params),
            ])
        except Exception:
            have_rules = False

        if have_rules:
            lines.append("RULES WE USED BEFORE TAKING THIS TRADE:")

            # Entry gate timing
            if summary.gate_minutes is not None:
                try:
                    lines.append(f"• We waited {int(summary.gate_minutes)} minutes after the open before entering any trades.")
                except Exception:
                    pass

            # Pre-market volume requirement
            if summary.min_pm_vol is not None:
                try:
                    lines.append(f"• Before the market opened, the stock needed at least {int(summary.min_pm_vol):,} shares of activity.")
                except Exception:
                    pass

            # Opening RVOL gate
            if summary.min_rvol_open is not None:
                try:
                    mins_text = f"{int(summary.rvol_open_minutes)} minutes" if summary.rvol_open_minutes is not None else "the opening minutes"
                    lines.append(f"• In the first {mins_text}, today's volume needed to be at least {float(summary.min_rvol_open):.2f}× yesterday's volume.")
                except Exception:
                    pass

            # Green candles requirement (from earlier section, but summarize here)
            if summary.rise_bars is not None or summary.green_body_min is not None:
                try:
                    rb = int(summary.rise_bars) if summary.rise_bars is not None else None
                    gb = float(summary.green_body_min) if summary.green_body_min is not None else None
                    if rb is not None and gb is not None:
                        lines.append(f"• We required {rb} recent green candles in a row, each with a strong body (≥ {gb:.2f} of the bar).")
                    elif rb is not None:
                        lines.append(f"• We required {rb} recent green candles in a row, each closing higher than the previous.")
                    elif gb is not None:
                        lines.append(f"• Each candle had to have a strong body (≥ {gb:.2f} of the bar).")
                except Exception:
                    pass

            # MACD requirement
            if summary.macd_rise_bars is not None or summary.require_macd_rise is not None:
                try:
                    if summary.require_macd_rise is True and summary.macd_rise_bars is not None:
                        lines.append(f"• The MACD histogram had to be above zero and rising for {int(summary.macd_rise_bars)} bars.")
                    elif summary.require_macd_rise is True:
                        lines.append("• The MACD histogram had to be above zero and rising.")
                    elif summary.macd_rise_bars is not None:
                        lines.append(f"• The MACD histogram had to be rising for {int(summary.macd_rise_bars)} bars.")
                except Exception:
                    pass

            # Take-profit and stop-loss
            if summary.tp_pct is not None and summary.sl_pct is not None:
                try:
                    lines.append(f"• Take-profit was set at +{float(summary.tp_pct):.1f}% and stop-loss was set at –{float(summary.sl_pct):.1f}%.")
                except Exception:
                    pass

            # Risk limits
            try:
                if summary.risk_snapshot:
                    max_trades = summary.risk_snapshot.get("max_trades_per_symbol")
                    if max_trades is not None:
                        lines.append(f"• We only take {int(max_trades)} trade per symbol.")
            except Exception:
                pass

            lines.append("")

            # (Moved exact-settings block to the end under RISK CALCULATION.)
    
    # Buy/Sell explanation
    lines.append("WHY WE TRADED:")
    lines.append("• We bought because the stock looked strong according to the rules.")
    lines.append(f"• We sold because the {exit_reason_display} was hit.")
    lines.append("")
    
    # Trade results
    lines.append("RESULTS:")
    lines.append(f"• Profit/Loss: ${summary.pnl_usd:,.2f}")
    # Plain English P/L sentence for clarity
    try:
        pnl_val = getattr(summary, "pnl_usd", None)
        if pnl_val is not None:
            if pnl_val > 0:
                lines.append(f"• This trade made a profit of ${pnl_val:.2f}.")
            elif pnl_val < 0:
                lines.append(f"• This trade lost ${abs(pnl_val):.2f}.")
            else:
                lines.append("• This trade broke even.")
    except Exception:
        pass
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
    # Daily loss (from risk snapshot) — show here as part of risk calculation
    try:
        daily_max_loss = None
        risk_cfg = getattr(summary, "risk_snapshot", None)
        if isinstance(risk_cfg, dict):
            daily_max_loss = risk_cfg.get("daily_max_loss")
        if daily_max_loss is not None:
            lines.append(f"• Daily loss limit: we stop trading for the day if total losses reach ${float(daily_max_loss):,.0f}.")
    except Exception:
        pass

    lines.append("")

    # EXACT SETTINGS FOR REFERENCE: (raw snapshots for debugging / record)
    try:
        have_raw = bool(summary.strategy_params) or bool(summary.risk_snapshot)
    except Exception:
        have_raw = False

    if have_raw:
        import json
        lines.append("EXACT SETTINGS FOR REFERENCE:")
        try:
            if summary.strategy_params:
                s_str = json.dumps(summary.strategy_params, sort_keys=True)
                lines.append(f"• Strategy settings: {s_str}")
            if summary.risk_snapshot:
                r_str = json.dumps(summary.risk_snapshot, sort_keys=True)
                lines.append(f"• Risk configuration: {r_str}")
        except Exception:
            if summary.strategy_params:
                lines.append(f"• Strategy settings: {repr(summary.strategy_params)}")
            if summary.risk_snapshot:
                lines.append(f"• Risk configuration: {repr(summary.risk_snapshot)}")

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


def _load_symbol_context_from_gapmap(date_str: str, out_dir: str, log) -> Dict[str, Dict[str, Any]]:
    """Load scanner gap-map context for symbols for a given date.

    Returns a dict mapping symbol -> context dict with keys:
      gap_pct, open_price, pm_volume, top_rank, universe_size
    """
    from pathlib import Path
    import json

    try:
        out_path = Path(out_dir).resolve()
        date_root = out_path.parent
        scanner_dir = date_root / "scanner"
        gap_map_path = scanner_dir / f"gap_map_{date_str}.json"
    except Exception as e:
        log.debug(f"[CTX] failed to derive gap_map path: {e}")
        return {}

    if not gap_map_path.exists():
        log.debug("[CTX] gap_map file missing, skipping context.")
        return {}

    try:
        with gap_map_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as e:
        log.debug(f"[CTX] failed to load gap context: {e}")
        return {}

    # Collect numeric gap entries for ranking
    gap_rows: List[tuple] = []
    ctx_map: Dict[str, Dict[str, Any]] = {}
    for sym, info in (data or {}).items():
        try:
            gap_val = None

            # If the JSON uses flat mapping like {"SYM": 123.45} treat that numeric
            if isinstance(info, (int, float)):
                try:
                    gap_val = float(info)
                except Exception:
                    gap_val = None
            else:
                # Also handle numeric strings if present
                if isinstance(info, str):
                    try:
                        gap_val = float(info)
                    except Exception:
                        gap_val = None
                else:
                    # Fallback: original behavior for dict-like entries
                    try:
                        for k in ("gap_pct", "gap", "gap_percent"):
                            if isinstance(info, dict) and k in info:
                                try:
                                    gap_val = float(info.get(k))
                                    break
                                except Exception:
                                    gap_val = None
                    except Exception:
                        gap_val = None

            # Per spec: third element is unused but preserve tuple shape for downstream code
            if gap_val is not None:
                gap_rows.append((sym, float(gap_val), None))

            # Only populate gap_pct here; leave open_price and pm_volume as None
            ctx_map[sym] = {
                "gap_pct": float(gap_val) if gap_val is not None else None,
                "open_price": None,
                "pm_volume": None,
            }
        except Exception:
            # be defensive per spec
            continue

    # compute rankings
    try:
        valid = [r for r in gap_rows if r[1] is not None]
        valid.sort(key=lambda x: x[1], reverse=True)
        universe_size = len(valid)
        for idx, (sym, _) in enumerate(valid, start=1):
            if sym in ctx_map:
                ctx_map[sym]["top_rank"] = idx
                ctx_map[sym]["universe_size"] = universe_size
    except Exception:
        # if ranking fails, leave ctx_map as-is
        pass

    return ctx_map


def run_backtest(
    date_str: str,
    universe_path: str,
    scenario_params: dict,
    settings: Settings,
    out_dir: str,
    scenario_name: Optional[str] = None,
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
    
    if isinstance(scenario_params, dict):  # v0.8.1.0.5
        plot_twcs_flag = bool(scenario_params.get("plot_twcs", False))  # v0.8.1.0.5
    else:
        plot_twcs_flag = False  # v0.8.1.0.5

    # v0.8.1.0.0: TWCS enable flag from scenario params.
    twcs_enabled = False
    try:
        params_dict = scenario_params if isinstance(scenario_params, dict) else {}
        twcs_enabled = bool(params_dict.get("twcs_enabled", False))
    except Exception as exc:
        print(f"[WARN] v0.8.1.0.0: Failed to read twcs_enabled from params: {exc}", file=sys.stderr)
        twcs_enabled = False

    # v0.7.9.7.6: use factory to create StrategyParams with scenario-aware defaults; norm_params still override.
    strat = SimpleBreakoutStrategy(create_strategy_params(scenario_name=scenario_name, **norm_params))
    # Load scanner context for this run (safe no-op if missing)
    symbol_ctx = _load_symbol_context_from_gapmap(date_str, out_dir, log)

    # Snapshot the normalized strategy params for inclusion in summaries
    try:
        strategy_snapshot: dict[str, Any] = dict(norm_params) if isinstance(norm_params, dict) else dict()
    except Exception:
        strategy_snapshot = dict()

    # Snapshot risk/safety knobs (best-effort, defensive)
    risk_snapshot: dict[str, Any] = {}
    try:
        risk_cfg = getattr(settings, "risk", None)
        if risk_cfg is not None:
            per_trade_risk = getattr(risk_cfg, "per_trade_risk", None)
            if per_trade_risk is not None:
                risk_snapshot["per_trade_risk"] = per_trade_risk
    except Exception as e:
        log.debug(f"[RISK] unable to snapshot risk settings: {e}")

    try:
        # include the run-level knobs too
        if max_trades_per_symbol is not None:
            risk_snapshot["max_trades_per_symbol"] = max_trades_per_symbol
        if daily_max_loss is not None:
            risk_snapshot["daily_max_loss"] = daily_max_loss
    except Exception:
        pass

    # v0.4.8: derive scenario id/name from settings (best-effort)
    scn = getattr(settings, "scenario", None) or getattr(settings, "scenario_name", None) or "UNKNOWN"  # v0.4.8
    if scn == "UNKNOWN":
        scn = "B"

    # NEW: build adaptive sizer from full scenario params (not just normalized)
    sizer = build_sizer_from_config(scenario_params if isinstance(scenario_params, dict) else {})
    sizer.reset_daily()

    # v0.8.1.3.0: Day follow-through gate prepass (Scenario B)
    day_gate_failed = False  # v0.8.1.3.0: default to no gate
    require_day_follow_through = scenario_params.get("require_day_follow_through", False) if isinstance(scenario_params, dict) else False  # v0.8.1.3.0
    day_follow_through_minutes = scenario_params.get("day_follow_through_minutes", 20) if isinstance(scenario_params, dict) else 20  # v0.8.1.3.0
    day_follow_through_min_symbols = scenario_params.get("day_follow_through_min_symbols", 2) if isinstance(scenario_params, dict) else 2  # v0.8.1.3.0
    green_body_min = norm_params.get("green_body_min", 0.0)  # v0.8.1.3.0
    if green_body_min is None:  # v0.8.1.3.0
        green_body_min = 0.0  # v0.8.1.3.0
    vwap_extension_max_pct = norm_params.get("vwap_extension_max_pct", 1.5)  # v0.8.1.3.0
    if vwap_extension_max_pct is None:  # v0.8.1.3.0
        vwap_extension_max_pct = 1.5  # v0.8.1.3.0

    # v0.8.1.3.0: Always emit check log
    log.info(  # v0.8.1.3.0
        "DAY_GATE: CHECK enabled=%s minutes=%d min_symbols=%d universe=%d",  # v0.8.1.3.0
        require_day_follow_through, day_follow_through_minutes, day_follow_through_min_symbols, len(symbols)  # v0.8.1.3.0
    )  # v0.8.1.3.0

    if require_day_follow_through:  # v0.8.1.3.0
        # v0.8.1.3.0: Prepass to evaluate day follow-through across universe
        i_eval = day_follow_through_minutes  # v0.8.1.3.0
        follow_through_count = 0  # v0.8.1.3.0
        for sym in symbols:  # v0.8.1.3.0
            sym_passed = False  # v0.8.1.3.0: track if this symbol passes
            j_pass = -1  # v0.8.1.3.0: first bar that passed
            j_start = max(0, i_eval - 5)  # v0.8.1.3.0: late window start (for logging)
            pass_rule = ""  # v0.8.1.3.0: which rule triggered
            fail_reason = "no_bar_passed"  # v0.8.1.3.0: default fail reason
            err_msg = ""  # v0.8.1.3.0: exception details for load_error
            # v0.8.1.3.0: debug metrics (best effort)
            dbg_close, dbg_open, dbg_high, dbg_low, dbg_vol = 0.0, 0.0, 0.0, 0.0, 0.0  # v0.8.1.3.0
            dbg_vwap, dbg_dist_pct, dbg_body_frac = None, None, 0.0  # v0.8.1.3.0
            dbg_cum_v = 0.0  # v0.8.1.3.0: cumulative volume for liquidity check
            try:  # v0.8.1.3.0
                bars = data.load_minute_bars(sym, date_str)  # v0.8.1.3.0
                if len(bars) <= i_eval:  # v0.8.1.3.0
                    fail_reason = "insufficient_bars"  # v0.8.1.3.0
                    # v0.8.1.3.0: capture last available bar for debug
                    if len(bars) > 0:  # v0.8.1.3.0
                        last_bar = bars[-1]  # v0.8.1.3.0
                        dbg_close, dbg_open, dbg_high, dbg_low, dbg_vol = last_bar.c, last_bar.o, last_bar.h, last_bar.l, last_bar.v  # v0.8.1.3.0
                        dbg_body_frac = abs(last_bar.c - last_bar.o) / max(1e-9, (last_bar.h - last_bar.l))  # v0.8.1.3.0
                else:  # v0.8.1.3.0
                    # v0.8.1.3.0: Scan late window [j_start..i_eval] for qualification; compute VWAP incrementally from 0
                    j_start = max(0, i_eval - 5)  # v0.8.1.3.0: late window only (last 5 minutes)
                    running_pv = 0.0  # v0.8.1.3.0
                    running_v = 0.0  # v0.8.1.3.0
                    for j in range(i_eval + 1):  # v0.8.1.3.0
                        try:  # v0.8.1.3.0
                            b = bars[j]  # v0.8.1.3.0
                            typical = (b.h + b.l + b.c) / 3.0  # v0.8.1.3.0
                            running_pv += typical * b.v  # v0.8.1.3.0
                            running_v += b.v  # v0.8.1.3.0
                            vwap_j = running_pv / running_v if running_v > 0 else None  # v0.8.1.3.0
                            # v0.8.1.3.0: Only test follow-through in late window [j_start..i_eval]
                            if j >= j_start:  # v0.8.1.3.0
                                close_above_vwap = False  # v0.8.1.3.0
                                if vwap_j is not None and b.c > vwap_j:  # v0.8.1.3.0
                                    # v0.8.1.3.0: Apply VWAP extension cap to close_gt_vwap qualification
                                    dist_pct_j = abs(b.c - vwap_j) / vwap_j * 100.0  # v0.8.1.3.0
                                    if dist_pct_j <= vwap_extension_max_pct:  # v0.8.1.3.0
                                        close_above_vwap = True  # v0.8.1.3.0
                                green_body_ok = False  # v0.8.1.3.0
                                body_frac = abs(b.c - b.o) / max(1e-9, (b.h - b.l))  # v0.8.1.3.0
                                # v0.8.1.3.0: Apply VWAP extension cap to green_body qualification
                                if b.c > b.o and body_frac >= green_body_min:  # v0.8.1.3.0
                                    if vwap_j is not None and vwap_j > 0:  # v0.8.1.3.0
                                        dist_abs_pct_j = abs(b.c - vwap_j) / vwap_j * 100.0  # v0.8.1.3.0
                                        if dist_abs_pct_j <= vwap_extension_max_pct:  # v0.8.1.3.0
                                            green_body_ok = True  # v0.8.1.3.0
                                    # v0.8.1.3.0: else vwap_j is None or 0, fail closed (green_body_ok remains False)
                                # v0.8.1.3.0: If either condition passes, check liquidity floor
                                if close_above_vwap or green_body_ok:  # v0.8.1.3.0
                                    # v0.8.1.3.0: Apply liquidity floor (cumulative volume >= 50k)
                                    if running_v >= 50_000:  # v0.8.1.3.0
                                        sym_passed = True  # v0.8.1.3.0
                                        j_pass = j  # v0.8.1.3.0
                                        pass_rule = "close_gt_vwap" if close_above_vwap else "green_body"  # v0.8.1.3.0
                                        # v0.8.1.3.0: capture debug metrics from passing bar
                                        dbg_close, dbg_open, dbg_high, dbg_low, dbg_vol = b.c, b.o, b.h, b.l, b.v  # v0.8.1.3.0
                                        dbg_vwap = vwap_j  # v0.8.1.3.0
                                        dbg_cum_v = running_v  # v0.8.1.3.0
                                        if vwap_j is not None and vwap_j > 0:  # v0.8.1.3.0
                                            dbg_dist_pct = 100.0 * (b.c - vwap_j) / vwap_j  # v0.8.1.3.0
                                        dbg_body_frac = body_frac  # v0.8.1.3.0
                                        break  # v0.8.1.3.0: early exit once passed
                                    # v0.8.1.3.0: else insufficient liquidity, continue scanning
                        except Exception:  # v0.8.1.3.0
                            continue  # v0.8.1.3.0: skip this bar, try next
                    # v0.8.1.3.0: If no bar passed, capture debug from i_eval bar
                    if not sym_passed:  # v0.8.1.3.0
                        try:  # v0.8.1.3.0
                            bar_eval = bars[i_eval]  # v0.8.1.3.0
                            dbg_close, dbg_open, dbg_high, dbg_low, dbg_vol = bar_eval.c, bar_eval.o, bar_eval.h, bar_eval.l, bar_eval.v  # v0.8.1.3.0
                            dbg_body_frac = abs(bar_eval.c - bar_eval.o) / max(1e-9, (bar_eval.h - bar_eval.l))  # v0.8.1.3.0
                            dbg_cum_v = running_v  # v0.8.1.3.0: capture cumulative volume at i_eval
                            # v0.8.1.3.0: compute final VWAP at i_eval
                            if running_v > 0:  # v0.8.1.3.0
                                dbg_vwap = running_pv / running_v  # v0.8.1.3.0
                                if dbg_vwap > 0:  # v0.8.1.3.0
                                    dbg_dist_pct = 100.0 * (bar_eval.c - dbg_vwap) / dbg_vwap  # v0.8.1.3.0
                        except Exception:  # v0.8.1.3.0
                            pass  # v0.8.1.3.0
            except Exception as exc:  # v0.8.1.3.0
                fail_reason = "load_error"  # v0.8.1.3.0
                err_str = str(exc)  # v0.8.1.3.0
                err_short = err_str[:160].replace("\n", " ").replace("\r", " ")  # v0.8.1.3.0
                err_msg = err_short  # v0.8.1.3.0
            # v0.8.1.3.0: Emit per-symbol debug log
            if sym_passed:  # v0.8.1.3.0
                follow_through_count += 1  # v0.8.1.3.0
                vwap_str = f"vwap={dbg_vwap:.4f}" if dbg_vwap is not None else "vwap=N/A"  # v0.8.1.3.0
                dist_str = f"dist_pct={dbg_dist_pct:.2f}" if dbg_dist_pct is not None else "dist_pct=N/A"  # v0.8.1.3.0
                # v0.8.1.3.0: Compute absolute distance percent for logging clarity
                if dbg_vwap is not None and dbg_vwap != 0:  # v0.8.1.3.0
                    dist_abs_pct = abs(dbg_close - dbg_vwap) / dbg_vwap * 100.0  # v0.8.1.3.0
                    dist_abs_str = f"dist_abs_pct={dist_abs_pct:.2f}"  # v0.8.1.3.0
                else:  # v0.8.1.3.0
                    dist_abs_str = "dist_abs_pct=N/A"  # v0.8.1.3.0
                log.info(  # v0.8.1.3.0
                    "DAY_GATE: SYM symbol=%s j_start=%d i_eval=%d pass=True j=%d rule=%s close=%.4f open=%.4f high=%.4f low=%.4f v=%.0f cum_v=%.0f %s %s %s vwap_cap=%.2f body_frac=%.2f",  # v0.8.1.3.0
                    sym, j_start, i_eval, j_pass, pass_rule, dbg_close, dbg_open, dbg_high, dbg_low, dbg_vol, dbg_cum_v, vwap_str, dist_str, dist_abs_str, vwap_extension_max_pct, dbg_body_frac  # v0.8.1.3.0
                )  # v0.8.1.3.0
            else:  # v0.8.1.3.0
                vwap_str = f"vwap={dbg_vwap:.4f}" if dbg_vwap is not None else "vwap=N/A"  # v0.8.1.3.0
                dist_str = f"dist_pct={dbg_dist_pct:.2f}" if dbg_dist_pct is not None else "dist_pct=N/A"  # v0.8.1.3.0
                # v0.8.1.3.0: Compute absolute distance percent for logging clarity
                if dbg_vwap is not None and dbg_vwap != 0:  # v0.8.1.3.0
                    dist_abs_pct = abs(dbg_close - dbg_vwap) / dbg_vwap * 100.0  # v0.8.1.3.0
                    dist_abs_str = f"dist_abs_pct={dist_abs_pct:.2f}"  # v0.8.1.3.0
                else:  # v0.8.1.3.0
                    dist_abs_str = "dist_abs_pct=N/A"  # v0.8.1.3.0
                err_str = f' err="{err_msg}"' if fail_reason == "load_error" and err_msg else ""  # v0.8.1.3.0
                log.info(  # v0.8.1.3.0
                    "DAY_GATE: SYM symbol=%s j_start=%d i_eval=%d pass=False reason=%s%s close=%.4f open=%.4f high=%.4f low=%.4f v=%.0f cum_v=%.0f %s %s %s vwap_cap=%.2f body_frac=%.2f",  # v0.8.1.3.0
                    sym, j_start, i_eval, fail_reason, err_str, dbg_close, dbg_open, dbg_high, dbg_low, dbg_vol, dbg_cum_v, vwap_str, dist_str, dist_abs_str, vwap_extension_max_pct, dbg_body_frac  # v0.8.1.3.0
                )  # v0.8.1.3.0
        # v0.8.1.3.0: Determine gate outcome
        if follow_through_count < day_follow_through_min_symbols:  # v0.8.1.3.0
            day_gate_failed = True  # v0.8.1.3.0
            log.info("DAY_GATE: FAILED symbols=%d reason=insufficient_follow_through", follow_through_count)  # v0.8.1.3.0
        else:  # v0.8.1.3.0
            log.info("DAY_GATE: PASSED symbols=%d", follow_through_count)  # v0.8.1.3.0

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
            if (not day_gate_failed) and position is None and strat.should_enter(bars, i) and risk.allow_new_trade():  # v0.8.1.3.0: added day gate check
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

                # v0.8.1.0.0: build trade_id and attach minimal identifiers to the position
                try:
                    entry_time_iso = bars[i].ts  # expected "HH:MM"
                    trade_id = f"{sym}_{date_str}_{entry_time_iso.replace(':','')}"
                except Exception:
                    entry_time_iso = bars[i].ts if i < len(bars) else ""
                    trade_id = f"{sym}_{date_str}_{i}"
                # attach to position for later use
                if isinstance(position, dict):
                    position["trade_id"] = trade_id  # v0.8.1.0.0
                    position["entry_time_iso"] = entry_time_iso  # v0.8.1.0.0

                # v0.8.1.0.0: TWCS entry snapshot hook (non-blocking, best-effort)
                if twcs_enabled:
                    try:
                        root_out = Path(settings.out_root) if hasattr(settings, "out_root") else Path("out")  # v0.8.1.0.0
                        snapshot_dir = twcs.build_snapshot_dir(
                            root_out=root_out,
                            date_str=date_str,
                            scenario=(scenario_name or scn),
                            symbol=sym,
                            trade_id=trade_id,
                        )  # v0.8.1.0.0

                        # v0.8.1.0.1: Load TWCS 1-minute window around entry.
                        candles_1m, window_meta_1m = load_twcs_minute_window(
                            symbol=sym,
                            date_str=date_str,
                            target_time_str=entry_time_iso,
                            window_before=10,
                            window_after=0,
                        )

                        # v0.8.1.0.4: load 1-second TWCS window around entry time
                        entry_candles_1s, entry_meta_1s = load_twcs_second_window(
                            symbol=sym,
                            date_str=date_str,
                            target_time_str=entry_time_iso,
                            window_before_seconds=60,
                            window_after_seconds=0,
                        )

                        entry_indicators: Dict[str, Any] = {}  # default

                        # v0.8.1.0.2: attempt to build TWCS entry indicators (non-blocking)
                        try:
                            entry_when = datetime.fromisoformat(f"{date_str}T{entry_time_iso}".replace("Z", ""))
                            entry_indicators = build_twcs_indicators(
                                symbol=sym,
                                date_str=date_str,
                                when=entry_when,
                                candles_1m=candles_1m,
                                strategy_state=None,
                            )
                        except Exception as exc:
                            print(f"[WARN] v0.8.1.0.2: Failed to build TWCS entry indicators for {sym}: {exc}", file=sys.stderr)
                            entry_indicators = {}

                        entry_meta: Dict[str, Any] = {
                            "symbol": sym,
                            "scenario": (scenario_name or scn),
                            "trade_id": trade_id,
                            "date": date_str,
                            "entry_time": f"{date_str} {entry_time_iso}",
                            "window_type": "entry",
                            "candles_1m": candles_1m,  # v0.8.1.0.1: populated from loader
                            "window_size_1m": window_meta_1m.get("window_size_1m", 0),  # v0.8.1.0.1
                            "window_before_1m": window_meta_1m.get("window_before_1m", 10),  # v0.8.1.0.1
                            "window_after_1m": window_meta_1m.get("window_after_1m", 0),  # v0.8.1.0.1
                            "candles_1s": entry_candles_1s,  # v0.8.1.0.4
                            "window_size_1s": entry_meta_1s.get("window_size_1s", 0),  # v0.8.1.0.4
                            "window_before_1s": entry_meta_1s.get("window_before_1s", 60),  # v0.8.1.0.4
                            "window_after_1s": entry_meta_1s.get("window_after_1s", 0),  # v0.8.1.0.4
                            "indicators": entry_indicators,
                        }  # v0.8.1.0.0

                        twcs.save_entry_snapshot(snapshot_dir, entry_meta)  # v0.8.1.0.0
                        
                        # v0.8.1.0.5: render entry TWCS PNG if enabled
                        if plot_twcs_flag:  # v0.8.1.0.5
                            try:
                                out_png = os.path.join(snapshot_dir, "trade_snapshot_entry.png")
                                plot_twcs_snapshot(entry_meta, out_png)
                            except Exception as exc:
                                print(f"[WARN] v0.8.1.0.5: Failed to plot entry TWCS for {sym}: {exc}", file=sys.stderr)
                    except Exception as exc:
                        print(f"[WARN] v0.8.1.0.1: Failed to save TWCS entry snapshot for {sym}: {exc}", file=sys.stderr)

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

                        # enrich with scanner context when available
                        ctx = symbol_ctx.get(sym, {}) if isinstance(symbol_ctx, dict) else {}
                        gap_pct = ctx.get("gap_pct")
                        top_rank = ctx.get("top_rank")
                        universe_size = ctx.get("universe_size")
                        open_price = ctx.get("open_price")
                        pm_volume = ctx.get("pm_volume")

                        # params for pass/fail flags
                        min_price = norm_params.get("min_price")
                        max_price = norm_params.get("max_price")
                        min_gap = norm_params.get("min_gap_pct")
                        max_gap = norm_params.get("max_gap_pct")
                        min_pm_vol = norm_params.get("min_pm_vol")

                        price_band_passed = None
                        if open_price is not None and min_price is not None and max_price is not None:
                            try:
                                price_band_passed = (float(min_price) <= float(open_price) <= float(max_price))
                            except Exception:
                                price_band_passed = None

                        gap_band_passed = None
                        if gap_pct is not None and min_gap is not None and max_gap is not None:
                            try:
                                gap_band_passed = (float(min_gap) <= float(gap_pct) <= float(max_gap))
                            except Exception:
                                gap_band_passed = None

                        pm_volume_passed = None
                        if pm_volume is not None and min_pm_vol is not None:
                            try:
                                pm_volume_passed = (float(pm_volume) >= float(min_pm_vol))
                            except Exception:
                                pm_volume_passed = None

                        # Read friendly knobs from normalized params
                        top = norm_params.get("top")
                        price_min = norm_params.get("min_price") or norm_params.get("price_min")
                        price_max = norm_params.get("max_price") or norm_params.get("price_max")
                        min_gap_pct = norm_params.get("min_gap_pct")
                        max_gap_pct = norm_params.get("max_gap_pct")
                        min_pm_vol = norm_params.get("min_pm_vol")
                        min_rvol_open = norm_params.get("min_rvol_open")
                        rvol_open_minutes = norm_params.get("rvol_open_minutes")
                        gate_minutes = norm_params.get("gate_minutes")
                        macd_rise_bars = norm_params.get("macd_rise_bars")
                        require_macd_rise = norm_params.get("require_macd_rise")
                        rise_bars = norm_params.get("rise_bars")
                        green_body_min = norm_params.get("green_body_min")

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
                            gap_pct=gap_pct,
                            top_rank=top_rank,
                            universe_size=universe_size,
                            open_price=open_price,
                            pm_volume=pm_volume,
                            price_band_passed=price_band_passed,
                            gap_band_passed=gap_band_passed,
                            pm_volume_passed=pm_volume_passed,
                            risk_per_share=(entry - sl),
                            exit_reason="take_profit",
                            top=top,
                            price_min=price_min,
                            price_max=price_max,
                            min_gap_pct=min_gap_pct,
                            max_gap_pct=max_gap_pct,
                            min_pm_vol=min_pm_vol,
                            min_rvol_open=min_rvol_open,
                            rvol_open_minutes=rvol_open_minutes,
                            gate_minutes=gate_minutes,
                            macd_rise_bars=macd_rise_bars,
                            require_macd_rise=require_macd_rise,
                            rise_bars=rise_bars,
                            green_body_min=green_body_min,
                            strategy_params=strategy_snapshot,
                            risk_snapshot=risk_snapshot or None,
                        )
                        print()
                        print(format_simple_trade_calcs(summary))
                        print()
                    except Exception as e:
                        print(f"[SUMMARY_ERROR] {e}")

                    # v0.8.1.0.0: TWCS exit snapshot hook (non-blocking, best-effort)
                    if twcs_enabled:
                        try:
                            raw_trade_id = position.get("trade_id") if isinstance(position, dict) else None
                            entry_time_iso = position.get("entry_time_iso") if isinstance(position, dict) else None
                            exit_time_iso = bar.ts
                            
                            # v0.8.1.0.1: Ensure a stable TWCS trade_id for exit snapshots.
                            if raw_trade_id:
                                trade_id_for_twcs = str(raw_trade_id)
                            else:
                                trade_id_for_twcs = f"{sym}_{date_str}_{exit_time_iso.replace(':', '')}"

                            mfe_value = None  # v0.8.1.0.0: placeholder
                            mae_value = None  # v0.8.1.0.0: placeholder
                            pnl_raw = pnl
                            gross_entry_val = gross_entry if 'gross_entry' in locals() else (qty * entry if entry else 0.0)
                            pnl_pct = (pnl / gross_entry_val * 100.0) if gross_entry_val else None
                            outcome_label = "TP"

                            root_out = Path(settings.out_root) if hasattr(settings, "out_root") else Path("out")
                            snapshot_dir = twcs.build_snapshot_dir(
                                root_out=root_out,
                                date_str=date_str,
                                scenario=(scenario_name or scn),
                                symbol=sym,
                                trade_id=trade_id_for_twcs,  # v0.8.1.0.1: use normalized trade_id
                            )  # v0.8.1.0.0

                            # v0.8.1.0.1: Load TWCS 1-minute window around exit.
                            candles_1m_exit, window_meta_1m_exit = load_twcs_minute_window(
                                symbol=sym,
                                date_str=date_str,
                                target_time_str=exit_time_iso,
                                window_before=10,
                                window_after=0,
                            )

                            # v0.8.1.0.4: load 1-second TWCS window around TP exit time
                            tp_candles_1s, tp_meta_1s = load_twcs_second_window(
                                symbol=sym,
                                date_str=date_str,
                                target_time_str=exit_time_iso,
                                window_before_seconds=60,
                                window_after_seconds=0,
                            )

                            exit_indicators: Dict[str, Any] = {}  # default

                            # v0.8.1.0.2: attempt to build TWCS exit indicators (non-blocking)
                            try:
                                exit_when = datetime.fromisoformat(f"{date_str}T{exit_time_iso}".replace("Z", ""))
                                exit_indicators = build_twcs_indicators(
                                    symbol=sym,
                                    date_str=date_str,
                                    when=exit_when,
                                    candles_1m=candles_1m_exit,
                                    strategy_state=None,
                                )
                            except Exception as exc:
                                print(f"[WARN] v0.8.1.0.2: Failed to build TWCS exit indicators for {sym}: {exc}", file=sys.stderr)
                                exit_indicators = {}

                            exit_meta: Dict[str, Any] = {
                                "symbol": sym,
                                "scenario": (scenario_name or scn),
                                "trade_id": trade_id_for_twcs,  # v0.8.1.0.1: use normalized trade_id
                                "date": date_str,
                                "exit_time": f"{date_str} {exit_time_iso}",
                                "window_type": "exit",
                                "candles_1m": candles_1m_exit,  # v0.8.1.0.1: populated from loader
                                "window_size_1m": window_meta_1m_exit.get("window_size_1m", 0),  # v0.8.1.0.1
                                "window_before_1m": window_meta_1m_exit.get("window_before_1m", 10),  # v0.8.1.0.1
                                "window_after_1m": window_meta_1m_exit.get("window_after_1m", 0),  # v0.8.1.0.1
                                "candles_1s": tp_candles_1s,  # v0.8.1.0.4
                                "window_size_1s": tp_meta_1s.get("window_size_1s", 0),  # v0.8.1.0.4
                                "window_before_1s": tp_meta_1s.get("window_before_1s", 60),  # v0.8.1.0.4
                                "window_after_1s": tp_meta_1s.get("window_after_1s", 0),  # v0.8.1.0.4
                                "indicators": exit_indicators,
                                "mfe": mfe_value,
                                "mae": mae_value,
                                "pnl_raw": pnl_raw,
                                "pnl_pct": pnl_pct,
                                "outcome": outcome_label,
                            }  # v0.8.1.0.0

                            twcs.save_exit_snapshot(snapshot_dir, exit_meta)  # v0.8.1.0.0
                            
                            # v0.8.1.0.5: render exit TWCS PNG if enabled
                            if plot_twcs_flag:  # v0.8.1.0.5
                                try:
                                    out_png = os.path.join(snapshot_dir, "trade_snapshot_exit.png")
                                    plot_twcs_snapshot(exit_meta, out_png)
                                except Exception as exc:
                                    print(f"[WARN] v0.8.1.0.5: Failed to plot exit TWCS for {sym}: {exc}", file=sys.stderr)
                        except Exception as exc:
                            print(f"[WARN] v0.8.1.0.1: Failed to save TWCS exit snapshot for {sym}: {exc}", file=sys.stderr)

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

                        # enrich with scanner context when available
                        ctx = symbol_ctx.get(sym, {}) if isinstance(symbol_ctx, dict) else {}
                        gap_pct = ctx.get("gap_pct")
                        top_rank = ctx.get("top_rank")
                        universe_size = ctx.get("universe_size")
                        open_price = ctx.get("open_price")
                        pm_volume = ctx.get("pm_volume")

                        # params for pass/fail flags
                        min_price = norm_params.get("min_price")
                        max_price = norm_params.get("max_price")
                        min_gap = norm_params.get("min_gap_pct")
                        max_gap = norm_params.get("max_gap_pct")
                        min_pm_vol = norm_params.get("min_pm_vol")

                        price_band_passed = None
                        if open_price is not None and min_price is not None and max_price is not None:
                            try:
                                price_band_passed = (float(min_price) <= float(open_price) <= float(max_price))
                            except Exception:
                                price_band_passed = None

                        gap_band_passed = None
                        if gap_pct is not None and min_gap is not None and max_gap is not None:
                            try:
                                gap_band_passed = (float(min_gap) <= float(gap_pct) <= float(max_gap))
                            except Exception:
                                gap_band_passed = None

                        pm_volume_passed = None
                        if pm_volume is not None and min_pm_vol is not None:
                            try:
                                pm_volume_passed = (float(pm_volume) >= float(min_pm_vol))
                            except Exception:
                                pm_volume_passed = None

                        # Read friendly knobs from normalized params
                        top = norm_params.get("top")
                        price_min = norm_params.get("min_price") or norm_params.get("price_min")
                        price_max = norm_params.get("max_price") or norm_params.get("price_max")
                        min_gap_pct = norm_params.get("min_gap_pct")
                        max_gap_pct = norm_params.get("max_gap_pct")
                        min_pm_vol = norm_params.get("min_pm_vol")
                        min_rvol_open = norm_params.get("min_rvol_open")
                        rvol_open_minutes = norm_params.get("rvol_open_minutes")
                        gate_minutes = norm_params.get("gate_minutes")
                        macd_rise_bars = norm_params.get("macd_rise_bars")
                        require_macd_rise = norm_params.get("require_macd_rise")
                        rise_bars = norm_params.get("rise_bars")
                        green_body_min = norm_params.get("green_body_min")

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
                            gap_pct=gap_pct,
                            top_rank=top_rank,
                            universe_size=universe_size,
                            open_price=open_price,
                            pm_volume=pm_volume,
                            price_band_passed=price_band_passed,
                            gap_band_passed=gap_band_passed,
                            pm_volume_passed=pm_volume_passed,
                            risk_per_share=(entry - sl),
                            exit_reason="stop_loss",
                            top=top,
                            price_min=price_min,
                            price_max=price_max,
                            min_gap_pct=min_gap_pct,
                            max_gap_pct=max_gap_pct,
                            min_pm_vol=min_pm_vol,
                            min_rvol_open=min_rvol_open,
                            rvol_open_minutes=rvol_open_minutes,
                            gate_minutes=gate_minutes,
                            macd_rise_bars=macd_rise_bars,
                            require_macd_rise=require_macd_rise,
                            rise_bars=rise_bars,
                            green_body_min=green_body_min,
                            strategy_params=strategy_snapshot,
                            risk_snapshot=risk_snapshot or None,
                        )
                        print()
                        print(format_simple_trade_calcs(summary))
                        print()
                    except Exception as e:
                        print(f"[SUMMARY_ERROR] {e}")

                    # v0.8.1.0.0: TWCS exit snapshot hook for stop-loss (non-blocking)
                    if twcs_enabled:
                        try:
                            raw_trade_id = position.get("trade_id") if isinstance(position, dict) else None
                            entry_time_iso = position.get("entry_time_iso") if isinstance(position, dict) else None
                            exit_time_iso = bar.ts
                            
                            # v0.8.1.0.1: Ensure a stable TWCS trade_id for exit snapshots.
                            if raw_trade_id:
                                trade_id_for_twcs = str(raw_trade_id)
                            else:
                                trade_id_for_twcs = f"{sym}_{date_str}_{exit_time_iso.replace(':', '')}"

                            mfe_value = None
                            mae_value = None
                            pnl_raw = pnl
                            gross_entry_val = gross_entry if 'gross_entry' in locals() else (qty * entry if entry else 0.0)
                            pnl_pct = (pnl / gross_entry_val * 100.0) if gross_entry_val else None
                            outcome_label = "SL"

                            root_out = Path(settings.out_root) if hasattr(settings, "out_root") else Path("out")
                            snapshot_dir = twcs.build_snapshot_dir(
                                root_out=root_out,
                                date_str=date_str,
                                scenario=(scenario_name or scn),
                                symbol=sym,
                                trade_id=trade_id_for_twcs,  # v0.8.1.0.1: use normalized trade_id
                            )  # v0.8.1.0.0

                            # v0.8.1.0.1: Load TWCS 1-minute window around exit.
                            candles_1m_exit, window_meta_1m_exit = load_twcs_minute_window(
                                symbol=sym,
                                date_str=date_str,
                                target_time_str=exit_time_iso,
                                window_before=10,
                                window_after=0,
                            )

                            # v0.8.1.0.4: load 1-second TWCS window around SL exit time
                            sl_candles_1s, sl_meta_1s = load_twcs_second_window(
                                symbol=sym,
                                date_str=date_str,
                                target_time_str=exit_time_iso,
                                window_before_seconds=60,
                                window_after_seconds=0,
                            )

                            exit_indicators: Dict[str, Any] = {}  # default

                            # v0.8.1.0.2: attempt to build TWCS exit indicators (non-blocking)
                            try:
                                exit_when = datetime.fromisoformat(f"{date_str}T{exit_time_iso}".replace("Z", ""))
                                exit_indicators = build_twcs_indicators(
                                    symbol=sym,
                                    date_str=date_str,
                                    when=exit_when,
                                    candles_1m=candles_1m_exit,
                                    strategy_state=None,
                                )
                            except Exception as exc:
                                print(f"[WARN] v0.8.1.0.2: Failed to build TWCS exit indicators for {sym}: {exc}", file=sys.stderr)
                                exit_indicators = {}

                            exit_meta: Dict[str, Any] = {
                                "symbol": sym,
                                "scenario": (scenario_name or scn),
                                "trade_id": trade_id_for_twcs,  # v0.8.1.0.1: use normalized trade_id
                                "date": date_str,
                                "exit_time": f"{date_str} {exit_time_iso}",
                                "window_type": "exit",
                                "candles_1m": candles_1m_exit,  # v0.8.1.0.1: populated from loader
                                "window_size_1m": window_meta_1m_exit.get("window_size_1m", 0),  # v0.8.1.0.1
                                "window_before_1m": window_meta_1m_exit.get("window_before_1m", 10),  # v0.8.1.0.1
                                "window_after_1m": window_meta_1m_exit.get("window_after_1m", 0),  # v0.8.1.0.1
                                "candles_1s": sl_candles_1s,  # v0.8.1.0.4
                                "window_size_1s": sl_meta_1s.get("window_size_1s", 0),  # v0.8.1.0.4
                                "window_before_1s": sl_meta_1s.get("window_before_1s", 60),  # v0.8.1.0.4
                                "window_after_1s": sl_meta_1s.get("window_after_1s", 0),  # v0.8.1.0.4
                                "indicators": exit_indicators,
                                "mfe": mfe_value,
                                "mae": mae_value,
                                "pnl_raw": pnl_raw,
                                "pnl_pct": pnl_pct,
                                "outcome": outcome_label,
                            }  # v0.8.1.0.0

                            twcs.save_exit_snapshot(snapshot_dir, exit_meta)  # v0.8.1.0.0
                            
                            # v0.8.1.0.5: render exit TWCS PNG if enabled
                            if plot_twcs_flag:  # v0.8.1.0.5
                                try:
                                    out_png = os.path.join(snapshot_dir, "trade_snapshot_exit.png")
                                    plot_twcs_snapshot(exit_meta, out_png)
                                except Exception as exc:
                                    print(f"[WARN] v0.8.1.0.5: Failed to plot exit TWCS for {sym}: {exc}", file=sys.stderr)
                        except Exception as exc:
                            print(f"[WARN] v0.8.1.0.1: Failed to save TWCS exit snapshot for {sym}: {exc}", file=sys.stderr)

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