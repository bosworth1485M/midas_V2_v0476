# v0.8.1.0.0: TWCS core (snapshots)
from __future__ import annotations
import os
import sys  # v0.8.1.0.0: needed for stderr messages from TWCS hooks
from typing import List, Dict, Any, Optional  # v0.8.1.7.0: added Optional
from collections import defaultdict
from datetime import datetime  # v0.8.1.7.1: needed for TWCS timestamp parsing

from ..utils_logging import setup_logging
from ..settings import Settings
from ..dataprov.csv_local import CsvLocalProvider
from ..datamodel import Bar  # v0.8.1.7.0: needed to create frozen OHLC copies for TP/SL
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


# v0.8.1.20.0: Helper to parse "HH:MM" into minutes since midnight for hold_minutes computation
def _hhmm_to_minutes(ts: str):
    """Convert HH:MM timestamp to minutes since midnight. Returns None if invalid."""
    if not ts or not isinstance(ts, str):
        return None
    parts = ts.split(":")
    if len(parts) != 2:
        return None
    try:
        hh = int(parts[0])
        mm = int(parts[1])
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return hh * 60 + mm
    except (ValueError, IndexError):
        pass
    return None


def _print_trade_card_entry(sym, date_str, scenario, entry_time, entry_price, tp, sl, qty, risk_usd, daily_max_loss, max_trades_per_symbol, trades_count_before, day_pnl_before, day_class, close_gt_vwap_count, gate_minutes, day_gate_failed, require_day_follow_through, bar, strat, telemetry, reject_reclaim_after_damage_effective, auto_enabled, vwap_extension_max_pct, entry_idx, should_enter, allow_new_trade, confirm_bar_guard_enabled=None, marginal_vwap_gate_enabled=None, post_damage_weak_reclaim_guard_enabled=None, post_expansion_confirmed=False, expansion_bps=None):  # v0.8.1.20.0: added guard status parameters
    """v0.8.1.20.0: Print comprehensive entry trade card (observability only, ASCII-only formatting)."""
    try:
        # v0.8.1.20.0: Handle None risk_usd gracefully
        risk_per_share = abs(entry_price - sl) if (entry_price and sl) else 0.0
        if risk_usd is not None and risk_per_share > 0:
            approx_shares_calc = f"{risk_usd:.2f} / {risk_per_share:.2f} ~= {qty}"
        else:
            approx_shares_calc = "N/A"  # v0.8.1.20.0
        
        # Strategy trigger snapshot
        vwap_val = bar.vwap if hasattr(bar, 'vwap') else "N/A"
        close_val = bar.c if hasattr(bar, 'c') else "N/A"
        
        # v0.8.1.20.0: Post-damage context - compute minutes_since_damage only if both indices are ints
        minutes_since_damage = "N/A"
        if (isinstance(entry_idx, int) and 
            isinstance(telemetry.get("last_damage_idx"), int)):
            minutes_since_damage = entry_idx - telemetry["last_damage_idx"]
        
        print("\n" + "="*80)
        print(f"TRADE: {sym} | LONG | ENTRY | {date_str} {entry_time} | Scenario: {scenario}")
        print("="*80)
        
        print(f"\nPOSITION & RISK:")
        print(f"  - Entry price: ${entry_price:.2f}")
        print(f"  - Stop price: ${sl:.2f}")
        print(f"  - Target price: ${tp:.2f}")
        print(f"  - Quantity: {qty}")
        print(f"  - Risk USD: ${risk_usd:.2f}" if risk_usd is not None else "  - Risk USD: N/A")  # v0.8.1.20.0
        print(f"  - Risk per share: ${risk_per_share:.2f}")
        print(f"  - Shares calculation: {approx_shares_calc}")
        print(f"  - Daily max loss: ${daily_max_loss:.2f}")
        print(f"  - Day PnL before trade: ${day_pnl_before:.2f}")
        print(f"  - Trades this symbol before: {trades_count_before}/{max_trades_per_symbol}")
        
        print(f"\nSTRATEGY TRIGGER SNAPSHOT:")
        print(f"  - Timestamp: {entry_time}")
        print(f"  - Close: {close_val}")
        print(f"  - VWAP: {vwap_val}")
        print(f"  - should_enter: {should_enter if should_enter is not None else 'N/A'}")  # v0.8.1.20.0
        print(f"  - allow_new_trade: {allow_new_trade if allow_new_trade is not None else 'N/A'}")  # v0.8.1.20.0
        if post_expansion_confirmed:
            print(f"  - Post-expansion confirmed: Yes (expansion_bps={expansion_bps:.2f})")
        
        print(f"\nDAY / REGIME CONTEXT:")
        print(f"  - Day classification: {day_class}")
        print(f"  - DAY_GATE enabled: {require_day_follow_through}")
        if require_day_follow_through:
            print(f"  - DAY_GATE result: {'PASS' if not day_gate_failed else 'FAIL'}")
            print(f"  - close_gt_vwap_count: {close_gt_vwap_count}")
            print(f"  - gate_minutes: {gate_minutes}")
        
        print(f"\nGUARD STATUS SUMMARY:")
        # v0.8.1.20.0: Print truthful guard status (N/A if not provided)
        confirm_status = confirm_bar_guard_enabled if confirm_bar_guard_enabled is not None else "N/A"
        marginal_status = marginal_vwap_gate_enabled if marginal_vwap_gate_enabled is not None else "N/A"
        post_damage_status = post_damage_weak_reclaim_guard_enabled if post_damage_weak_reclaim_guard_enabled is not None else "N/A"
        print(f"  - CONFIRM_BAR_GUARD v0.8.1.8.1 enabled: {confirm_status}")
        print(f"  - MARGINAL_VWAP_GATE v0.8.1.11.0 enabled: {marginal_status}")
        print(f"  - POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD v0.8.1.19.0 enabled: {post_damage_status}")
        print(f"  - VWAP_EXTENSION_GATE enabled: {vwap_extension_max_pct is not None}, max_pct: {vwap_extension_max_pct}")
        print(f"  - STRUCT_DAMAGE auto_mode effective: {reject_reclaim_after_damage_effective} (auto_enabled={auto_enabled})")
        
        print(f"\nPOST-DAMAGE CONTEXT (DIAGNOSTIC):")
        print(f"  - Last damage timestamp: {telemetry.get('last_damage_ts', 'N/A')}")
        print(f"  - Minutes since damage at entry: {minutes_since_damage}")
        print(f"  - Blocks today (struct_damage): {telemetry.get('count_struct_damage_blocks', 0)}")
        print(f"  - Blocks today (post_damage_weak_reclaim): {telemetry.get('count_post_damage_weak_reclaim_blocks', 0)}")
        print(f"  - Blocks today (vwap_ext): {telemetry.get('count_vwap_ext_blocks', 0)}")
        print(f"  - Blocks today (marginal_vwap_gate): {telemetry.get('count_marginal_vwap_gate_blocks', 0)}")
        
        print(f"\nDATA QUALITY FLAGS (SYMBOL/DAY):")
        print(f"  - Duplicate timestamps: {telemetry.get('dup_ts_count', 0)}")
        print(f"  - POS_MGMT_MISMATCH occurred: {telemetry.get('pos_mgmt_mismatch_occurred', False)}")
        if telemetry.get('pos_mgmt_mismatch_last'):
            print(f"    Last mismatch: {telemetry['pos_mgmt_mismatch_last']}")
        print(f"  - 1s CSV missing: {telemetry.get('missing_1s_csv', False)}")
        
        print("="*80 + "\n")
    except Exception:
        pass  # v0.8.1.20.0: silent failure


def _print_trade_card_exit(sym, date_str, scenario, entry_time, exit_time, entry_price, exit_price, tp, sl, qty, pnl, outcome, telemetry, hold_minutes=None, hold_bars=None, exit_reason="N/A", bar_details="N/A"):
    """v0.8.1.20.0: Print comprehensive exit trade card (observability only, ASCII-only formatting)."""
    try:
        profit_per_share = exit_price - entry_price if (exit_price and entry_price) else 0.0
        risk_per_share = abs(entry_price - sl) if (entry_price and sl) else 0.0
        r_multiple = (profit_per_share / risk_per_share) if risk_per_share > 0 else "N/A"
        hold_mins_display = f"{hold_minutes} minutes" if hold_minutes is not None else "N/A"
        hold_bars_display = f"{hold_bars} bars" if hold_bars is not None else "N/A"
        
        print("\n" + "="*80)
        print(f"TRADE: {sym} | EXIT | {date_str} {exit_time} | Outcome: {outcome}")
        print("="*80)
        
        print(f"\nEXIT TRIGGER DETAILS (CONCRETE):")
        print(f"  - Exit reason: {exit_reason}")
        print(f"  - Exit price: ${exit_price:.2f}" if exit_price else "  - Exit price: N/A")
        print(f"  - Entry price: ${entry_price:.2f}" if entry_price else "  - Entry price: N/A")
        print(f"  - PnL USD: ${pnl:.2f}")
        print(f"  - PnL per share: ${profit_per_share:.2f}")
        print(f"  - R-multiple: {r_multiple if r_multiple != 'N/A' else 'N/A'}")
        print(f"  - Hold time: {hold_mins_display}")
        print(f"  - Hold bars: {hold_bars_display}")
        
        print(f"\n'WHY WE EXITED' SNAPSHOT:")
        print(f"  - Exit timestamp: {exit_time}")
        print(f"  - Bar details: {bar_details}")
        
        print(f"\nDATA QUALITY FLAGS (SYMBOL/DAY):")
        print(f"  - Duplicate timestamps: {telemetry.get('dup_ts_count', 0)}")
        print(f"  - POS_MGMT_MISMATCH occurred: {telemetry.get('pos_mgmt_mismatch_occurred', False)}")
        if telemetry.get('pos_mgmt_mismatch_last'):
            print(f"    Last mismatch: {telemetry['pos_mgmt_mismatch_last']}")
        print(f"  - 1s CSV missing: {telemetry.get('missing_1s_csv', False)}")
        
        print("="*80 + "\n")
    except Exception:
        pass  # v0.8.1.20.0: silent failure


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

    log.info("STRUCT_DAMAGE v0.8.1.4.0: CONFIG reject_reclaim_after_damage=%s", scenario_params.get("reject_reclaim_after_damage", False) if isinstance(scenario_params, dict) else False)  # v0.8.1.4.0
    log.info("CONFIRM_BAR_GUARD v0.8.1.8.1: enabled=True")  # v0.8.1.8.0
    log.info("MARGINAL_VWAP_GATE v0.8.1.11.0: enabled=True")  # v0.8.1.11.0
    log.info("POST_DAMAGE_WEAK_VWAP_RECLAIM_GUARD v0.8.1.19.0: enabled=True")  # v0.8.1.19.0
    log.info("POST_DAMAGE_ENTRY_LOCKOUT v0.8.1.23.0: enabled=True")  # v0.8.1.23.0
    log.info("POST_DAMAGE_VWAP_HEAL_ESCAPE v0.8.1.24.0: enabled=True")  # v0.8.1.24.0

    # v0.4.8: load feature registry once (safe no-op if registry missing)
    if FeatureRegistry is not None:  # v0.4.8
        try:  # v0.4.8
            FeatureRegistry.load(Path(__file__).resolve().parents[2])  # v0.4.8
            log.debug("[FEATURES] registry loaded")  # v0.4.8
        except Exception as e:  # v0.4.8
            log.debug(f"[FEATURES] registry load skipped: {e}")  # v0.4.8

    # Instantiate modules
    data = CsvLocalProvider(settings.data.data_root)
    print(f"[DATA_PROVIDER] v0.8.1.7.0 type={type(data)}")  # v0.8.1.7.0
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
    reject_reclaim_after_damage = scenario_params.get("reject_reclaim_after_damage", False) if isinstance(scenario_params, dict) else False  # v0.8.1.4.0
    auto_struct_damage_from_day_gate = scenario_params.get("auto_struct_damage_from_day_gate", False) if isinstance(scenario_params, dict) else False  # v0.8.1.5.0

    # v0.8.1.5.0: Initialize close_gt_vwap_count before DAY_GATE block
    close_gt_vwap_count = 0  # v0.8.1.5.0
    green_body_count = 0  # v0.8.1.5.0
    require_day_gate_close_gt_vwap = False  # v0.8.1.8.2: Initialize for summary log

    # v0.8.1.3.0: Always emit check log
    log.info(  # v0.8.1.3.0
        "DAY_GATE: CHECK enabled=%s minutes=%d min_symbols=%d universe=%d",  # v0.8.1.3.0
        require_day_follow_through, day_follow_through_minutes, day_follow_through_min_symbols, len(symbols)  # v0.8.1.3.0
    )  # v0.8.1.3.0

    if require_day_follow_through:  # v0.8.1.3.0
        # v0.8.1.3.0: Prepass to evaluate day follow-through across universe
        i_eval = day_follow_through_minutes  # v0.8.1.3.0
        follow_through_count = 0  # v0.8.1.3.0
        # v0.8.1.3.1: Read toggle for requiring ≥1 close_gt_vwap qualifier
        require_day_gate_close_gt_vwap = scenario_params.get("require_day_gate_close_gt_vwap", False) if isinstance(scenario_params, dict) else False  # v0.8.1.3.1
        log.info("DAY_GATE v0.8.1.6.0: CONFIG require_day_gate_close_gt_vwap=%s", require_day_gate_close_gt_vwap)  # v0.8.1.6.0
        close_gt_vwap_count = 0  # v0.8.1.3.1: track count of close_gt_vwap qualifiers
        green_body_count = 0  # v0.8.1.3.1: track count of green_body qualifiers
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
                # v0.8.1.3.1: Track rule counts for ≥1 close_gt_vwap requirement
                if pass_rule == "close_gt_vwap":  # v0.8.1.3.1
                    close_gt_vwap_count += 1  # v0.8.1.3.1
                elif pass_rule == "green_body":  # v0.8.1.3.1
                    green_body_count += 1  # v0.8.1.3.1
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
        # v0.8.1.3.1: Emit rule counts summary
        log.info("DAY_GATE: RULE_COUNTS total=%d close_gt_vwap=%d green_body=%d", follow_through_count, close_gt_vwap_count, green_body_count)  # v0.8.1.3.1
        # v0.8.1.3.0: Determine gate outcome
        if follow_through_count < day_follow_through_min_symbols:  # v0.8.1.3.0
            day_gate_failed = True  # v0.8.1.3.0
            log.info("DAY_GATE: FAILED symbols=%d reason=insufficient_follow_through", follow_through_count)  # v0.8.1.3.0
        else:  # v0.8.1.3.0
            # v0.8.1.3.1: Apply ≥1 close_gt_vwap qualifier requirement if enabled
            if require_day_gate_close_gt_vwap and close_gt_vwap_count == 0:  # v0.8.1.3.1
                day_gate_failed = True  # v0.8.1.3.1
                log.info("DAY_GATE: FAILED reason=no_close_gt_vwap_qualifier")  # v0.8.1.3.1
            else:  # v0.8.1.3.1
                log.info("DAY_GATE: PASSED symbols=%d", follow_through_count)  # v0.8.1.3.0
    else:  # v0.8.1.5.0: DAY_GATE disabled
        close_gt_vwap_count = 0  # v0.8.1.5.0: force to 0 when DAY_GATE disabled

    # v0.8.1.5.0: Day-level auto-switch for structural damage guard
    base_reject = reject_reclaim_after_damage  # v0.8.1.5.0
    auto_mode = auto_struct_damage_from_day_gate  # v0.8.1.5.0
    day_gate_pass = (not day_gate_failed) if require_day_follow_through else True  # v0.8.1.5.0
    auto_enabled = False  # v0.8.1.5.0
    reject_reclaim_after_damage_effective = False  # v0.8.1.5.0
    reason = ""  # v0.8.1.5.0
    if base_reject:  # v0.8.1.5.0
        reject_reclaim_after_damage_effective = True  # v0.8.1.5.0
        auto_enabled = False  # v0.8.1.5.0
        reason = "manual_true_forced"  # v0.8.1.5.0
    else:  # v0.8.1.5.0
        if not auto_mode:  # v0.8.1.5.0
            reject_reclaim_after_damage_effective = False  # v0.8.1.5.0
            auto_enabled = False  # v0.8.1.5.0
            reason = "auto_mode_off"  # v0.8.1.5.0
        else:  # v0.8.1.5.0
            if day_gate_failed:  # v0.8.1.5.0
                reject_reclaim_after_damage_effective = False  # v0.8.1.5.0
                auto_enabled = False  # v0.8.1.5.0
                reason = "auto_disabled_day_gate_failed"  # v0.8.1.5.0
            elif close_gt_vwap_count >= 1:  # v0.8.1.5.0
                reject_reclaim_after_damage_effective = True  # v0.8.1.5.0
                auto_enabled = True  # v0.8.1.5.0
                reason = "auto_enabled_day_gate_close_gt_vwap"  # v0.8.1.5.0
            else:  # v0.8.1.5.0
                reject_reclaim_after_damage_effective = False  # v0.8.1.5.0
                auto_enabled = False  # v0.8.1.5.0
                reason = "auto_disabled_no_close_gt_vwap"  # v0.8.1.5.0
    log.info(  # v0.8.1.5.0
        "STRUCT_DAMAGE v0.8.1.5.0: CONFIG base=%s auto_mode=%s day_gate_pass=%s close_gt_vwap_cnt=%d auto_enabled=%s effective=%s reason=%s",  # v0.8.1.5.0
        base_reject, auto_mode, day_gate_pass, close_gt_vwap_count, auto_enabled, reject_reclaim_after_damage_effective, reason  # v0.8.1.5.0
    )  # v0.8.1.5.0

    # v0.8.1.8.2: Day-level DAY_GATE summary (logging only)
    log.info("[WHY] v0.8.1.8.2 DAY_GATE_SUMMARY details=enabled=%s gate_minutes=%d min_symbols=%d close_gt_vwap_cnt=%d require_close_gt_vwap=%s day_gate_failed=%s", require_day_follow_through, day_follow_through_minutes, day_follow_through_min_symbols, close_gt_vwap_count, require_day_gate_close_gt_vwap if require_day_follow_through else False, day_gate_failed)  # v0.8.1.8.2

    # v0.8.1.9.0: Define day-gate classification flags
    is_day_gate_on = bool(require_day_follow_through)  # v0.8.1.9.0
    is_hostile_day = (is_day_gate_on and close_gt_vwap_count == 0)  # v0.8.1.9.0
    is_marginal_day = (is_day_gate_on and close_gt_vwap_count == 1)  # v0.8.1.9.0
    is_healthy_day = (is_day_gate_on and close_gt_vwap_count >= 2)  # v0.8.1.9.0
    day_class = "off"  # v0.8.1.9.0
    if is_hostile_day:  # v0.8.1.9.0
        day_class = "hostile"  # v0.8.1.9.0
    elif is_marginal_day:  # v0.8.1.9.0
        day_class = "marginal"  # v0.8.1.9.0
    elif is_healthy_day:  # v0.8.1.9.0
        day_class = "healthy"  # v0.8.1.9.0
    marginal_cap_str = "1" if is_marginal_day else "n/a"  # v0.8.1.9.0

    # v0.8.1.9.0: Day-level trade counter (increments only when trade finalizes at TP or SL)
    day_trade_count = 0  # v0.8.1.9.0
    
    # v0.8.1.17.0: Marginal stop-after-1-loss policy enablement and state
    scenario_on = bool(getattr(strat.p, "marginal_stop_after_1_loss", False))  # v0.8.1.17.0
    env_on = os.getenv("MIDAS_MARGINAL_STOP1LOSS", "").strip().lower() in {"1", "true", "yes"}  # v0.8.1.17.0
    marginal_stop1loss_enabled = bool(scenario_on or env_on)  # v0.8.1.17.0
    source = "scenario" if scenario_on else "env" if env_on else "off"  # v0.8.1.17.0
    marginal_sl_seen = False  # v0.8.1.17.0
    marginal_stop_trigger_logged = False  # v0.8.1.17.0
    log.info("MARGINAL_STOP_AFTER_1_LOSS v0.8.1.17.0: enabled=%s source=%s", marginal_stop1loss_enabled, source)  # v0.8.1.17.0

    # v0.8.1.9.0: Day-level DAY_GATE summary (with marginal participation)
    log.info("DAY_GATE v0.8.1.9.0 summary: on=%d close_gt_vwap_count=%d class=%s marginal_cap=%s day_trade_count=%d", 1 if is_day_gate_on else 0, close_gt_vwap_count, day_class, marginal_cap_str, day_trade_count)  # v0.8.1.9.0

    # v0.8.1.21.0: Initialize day-level REGIME_SUMMARY aggregators (observability only)
    REGIME_DAMAGE_LOOKBACK_BARS = 60  # v0.8.1.21.0: damage scan lookback for minutes_since_damage
    universe_symbols = len(symbols)  # v0.8.1.21.0
    day_struct_damage_blocks_total = 0  # v0.8.1.21.0
    day_post_damage_weak_reclaim_blocks_total = 0  # v0.8.1.21.0
    day_vwap_ext_blocks_total = 0  # v0.8.1.21.0
    day_marginal_vwap_gate_blocks_total = 0  # v0.8.1.21.0
    day_post_damage_entry_lockout_blocks_total = 0  # v0.8.1.23.0
    day_post_damage_heal_entries_allowed_total = 0  # v0.8.1.24.0
    day_dup_ts_total = 0  # v0.8.1.21.0
    day_pos_mgmt_mismatch_symbols = 0  # v0.8.1.21.0
    day_missing_1s_symbols = 0  # v0.8.1.21.0
    day_minutes_since_damage_at_entry_list = []  # v0.8.1.21.0
    regime_summary_emitted = False  # v0.8.1.21.0: ensure exactly once per day

    # Guardrail trackers
    trades_by_symbol = defaultdict(int)
    cum_pnl = 0.0

    # v0.8.1.8.1: Log-once latch for EARLY_REJECT to prevent spam
    early_reject_logged = set()  # keys: f"{date_str}:{sym}:{reason}"
    # v0.8.1.9.0: Log-once latches for marginal-day (separate for eligibility and cap-reached)
    marginal_eligible_logged = False  # v0.8.1.9.0
    marginal_cap_reached_logged = False  # v0.8.1.9.0
    marginal_stop1loss_eligible_logged = False  # v0.8.1.17.0: separate latch for policy A eligibility log

    trades = []
    for sym in symbols:
        try:
            bars = data.load_minute_bars(sym, date_str)
        except FileNotFoundError as e:
            log.warning(str(e))
            continue

        # v0.8.1.20.0: Telemetry dict for per-symbol/per-day diagnostics (initialize BEFORE any writes)
        telemetry = {
            "count_struct_damage_blocks": 0,
            "count_post_damage_weak_reclaim_blocks": 0,
            "count_vwap_ext_blocks": 0,
            "count_marginal_vwap_gate_blocks": 0,
            "count_post_damage_entry_lockout_blocks": 0,  # v0.8.1.23.0
            "last_damage_ts": None,
            "last_damage_idx": None,
            "dup_ts_count": 0,
            "pos_mgmt_mismatch_occurred": False,
            "pos_mgmt_mismatch_last": None,
            "missing_1s_csv": False,
        }

        # v0.8.1.7.0: freeze original OHLC for TP/SL, keyed by timestamp
        # Create NEW Bar objects so later mutations to bars do not affect TP/SL checks
        # Duplicate-safe merge: preserve max wicks when duplicate timestamps occur
        pos_bar_by_ts: dict[str, Bar] = {}
        dup_count = 0
        for b in bars:
            if b.ts not in pos_bar_by_ts:
                pos_bar_by_ts[b.ts] = Bar(ts=b.ts, o=b.o, h=b.h, l=b.l, c=b.c, v=b.v, vwap=b.vwap)
            else:
                dup_count += 1
                prev = pos_bar_by_ts[b.ts]
                pos_bar_by_ts[b.ts] = Bar(
                    ts=b.ts,
                    o=prev.o,
                    h=max(prev.h, b.h),
                    l=min(prev.l, b.l),
                    c=b.c,
                    v=(prev.v or 0) + (b.v or 0),
                    vwap=prev.vwap if prev.vwap is not None else b.vwap
                )
        if dup_count > 0:
            log.warning("[WARN] [DUP_TS] v0.8.1.7.0 symbol=%s date=%s duplicates=%d", sym, date_str, dup_count)
            telemetry["dup_ts_count"] = dup_count  # v0.8.1.20.0

        # v0.4.8: set per-symbol identity & scenario on the strategy
        try:  # v0.4.8
            strat.symbol = sym  # v0.4.8
            strat.session_date = date_str  # v0.4.8 (lets the strategy convert 'HH:MM' to epoch)
            strat.scenario_id = scn  # v0.4.8
        except Exception:
            pass  # v0.4.8

        position = None
        entry = None
        pending_entry = None  # v0.8.1.7.0: pending entry confirmation state
        
        # v0.8.1.23.0: POST_DAMAGE_ENTRY_LOCKOUT per-symbol tracking
        damage_first_idx = None  # v0.8.1.23.0
        damage_first_ts = None  # v0.8.1.23.0
        post_damage_lockout_logged = False  # v0.8.1.23.0: log-once latch per symbol/day
        
        # v0.8.1.24.0: POST_DAMAGE_VWAP_HEAL_ESCAPE per-symbol tracking
        heal_reclaim_idx = None  # v0.8.1.24.0
        heal_confirm_count = 0  # v0.8.1.24.0
        heal_window_damage_seen = False  # v0.8.1.24.0
        heal_ready_idx = None  # v0.8.1.24.0
        post_damage_heal_attempt_used = False  # v0.8.1.24.0
        heal_running_pv = 0.0  # v0.8.1.24.0: VWAP fallback state
        heal_running_v = 0.0  # v0.8.1.24.0: VWAP fallback state
        heal_reclaim_logged = False  # v0.8.1.24.0: log-once latch for reclaim
        heal_ready_logged = False  # v0.8.1.24.0: log-once latch for ready
        
        # Tiering context (scenario-level until per-symbol features are wired)
        tier_ctx = {
            # ONE-LINE PATCH: make sizing "score-aware" for this run
            "news_score": float(norm_params.get("news_min_score", 0.0)),
            "min_rvol_open": float(norm_params.get("min_rvol_open", 0.0)),  # scenario-level fallback
        }

        for i in range(len(bars)):
            bar = bars[i]
            if sym == "TCMD" and date_str == "2025-08-05" and getattr(bar, "ts", None) == "14:19":
                print(f"[BAR_STREAM] v0.8.1.7.0 PRE symbol={sym} ts={bar.ts} o={bar.o} h={bar.h} l={bar.l} c={bar.c}")

            # v0.8.1.23.0: Continuous damage tracking (track first structural damage bar)
            if damage_first_idx is None:  # v0.8.1.23.0: only capture first damage
                body = abs(bar.c - bar.o)  # v0.8.1.23.0
                rng = max(bar.h - bar.l, 1e-9)  # v0.8.1.23.0
                body_fraction = body / rng  # v0.8.1.23.0
                if bar.c < bar.o and body_fraction >= 0.60:  # v0.8.1.23.0: structural damage definition
                    damage_first_idx = i  # v0.8.1.23.0
                    damage_first_ts = bar.ts if hasattr(bar, 'ts') else f"bar_{i}"  # v0.8.1.23.0

            # v0.8.1.24.0: Continuous heal tracking (post-damage VWAP reclaim + 2-bar confirmation)
            is_rth_bar = (isinstance(bar.ts, str) and bar.ts >= "09:30" and bar.ts <= "16:00")  # v0.8.1.24.0: RTH-only
            if is_rth_bar and damage_first_idx is not None:  # v0.8.1.24.0: only track heal after damage exists
                # v0.8.1.24.0: Compute heal_vwap_i (prefer bar.vwap, else incremental)
                heal_vwap_i = None  # v0.8.1.24.0
                if hasattr(bar, 'vwap') and bar.vwap is not None and bar.vwap > 0:  # v0.8.1.24.0
                    heal_vwap_i = bar.vwap  # v0.8.1.24.0
                else:  # v0.8.1.24.0: fallback to incremental computation
                    typical = (bar.h + bar.l + bar.c) / 3.0  # v0.8.1.24.0
                    heal_running_pv += typical * bar.v  # v0.8.1.24.0
                    heal_running_v += bar.v  # v0.8.1.24.0
                    if heal_running_v > 0:  # v0.8.1.24.0
                        heal_vwap_i = heal_running_pv / heal_running_v  # v0.8.1.24.0
                
                # v0.8.1.24.0: Determine close_above_vwap and structural damage for this bar
                close_above_vwap = (heal_vwap_i is not None and heal_vwap_i > 0 and bar.c > heal_vwap_i)  # v0.8.1.24.0
                body = abs(bar.c - bar.o)  # v0.8.1.24.0
                rng = max(bar.h - bar.l, 1e-9)  # v0.8.1.24.0
                body_fraction = body / rng  # v0.8.1.24.0
                is_struct_damage_bar_i = (bar.c < bar.o and body_fraction >= 0.60)  # v0.8.1.24.0
                
                # v0.8.1.24.0: Reclaim detection (first close above VWAP after damage)
                if heal_reclaim_idx is None and close_above_vwap:  # v0.8.1.24.0
                    heal_reclaim_idx = i  # v0.8.1.24.0
                    heal_confirm_count = 0  # v0.8.1.24.0
                    heal_window_damage_seen = False  # v0.8.1.24.0
                    heal_ready_idx = None  # v0.8.1.24.0
                    if not heal_reclaim_logged:  # v0.8.1.24.0: log once per symbol/day
                        log.info(f"[WHY] v0.8.1.24.0 VWAP_HEAL_RECLAIM symbol={sym} ts={bar.ts} reclaim_i={i}")  # v0.8.1.24.0
                        heal_reclaim_logged = True  # v0.8.1.24.0
                
                # v0.8.1.24.0: Damage-in-window tracking (abandon if damage seen after reclaim)
                if heal_reclaim_idx is not None and i >= heal_reclaim_idx and is_struct_damage_bar_i:  # v0.8.1.24.0
                    heal_window_damage_seen = True  # v0.8.1.24.0
                
                # v0.8.1.24.0: Confirmation counting (reclaim bar does NOT count; must be i > heal_reclaim_idx)
                if heal_reclaim_idx is not None and i > heal_reclaim_idx:  # v0.8.1.24.0
                    if close_above_vwap:  # v0.8.1.24.0
                        heal_confirm_count += 1  # v0.8.1.24.0
                    else:  # v0.8.1.24.0: reset confirmation count if close drops <= VWAP
                        heal_confirm_count = 0  # v0.8.1.24.0
                
                # v0.8.1.24.0: Window failure / restart (if damage seen in window, abandon)
                if heal_window_damage_seen:  # v0.8.1.24.0
                    heal_reclaim_idx = None  # v0.8.1.24.0
                    heal_confirm_count = 0  # v0.8.1.24.0
                    heal_window_damage_seen = False  # v0.8.1.24.0
                    heal_ready_idx = None  # v0.8.1.24.0
                
                # v0.8.1.24.0: Heal readiness (2 confirmations after reclaim)
                if heal_reclaim_idx is not None and heal_confirm_count >= 2 and heal_ready_idx is None:  # v0.8.1.24.0
                    heal_ready_idx = i  # v0.8.1.24.0: this i is the 2nd confirmation bar
                    if not heal_ready_logged:  # v0.8.1.24.0: log once per symbol/day
                        log.info(f"[WHY] v0.8.1.24.0 VWAP_HEAL_READY symbol={sym} ts={bar.ts} reclaim_i={heal_reclaim_idx} confirm2_i={i}")  # v0.8.1.24.0
                        heal_ready_logged = True  # v0.8.1.24.0
            elif damage_first_idx is None:  # v0.8.1.24.0: reset heal state if no damage yet
                heal_reclaim_idx = None  # v0.8.1.24.0
                heal_confirm_count = 0  # v0.8.1.24.0
                heal_window_damage_seen = False  # v0.8.1.24.0
                heal_ready_idx = None  # v0.8.1.24.0

            # Guardrail: stop new trades if daily loss exceeded
            if daily_max_loss and cum_pnl <= -abs(daily_max_loss):
                # v0.8.1.8.1: Log-once latch
                reject_key = f"{date_str}:{sym}:DAILY_MAX_LOSS"
                if reject_key not in early_reject_logged:
                    candidate_ts = bar.ts if hasattr(bar, 'ts') else f"bar_{i}"
                    log.warning(f"[WHY] v0.8.1.8.1 EARLY_REJECT reason=DAILY_MAX_LOSS symbol={sym} ts={candidate_ts} details=cum_pnl={cum_pnl:.2f} thresh={-abs(daily_max_loss):.2f}")
                    early_reject_logged.add(reject_key)
                continue

            # Guardrail: per-symbol trade cap
            if max_trades_per_symbol and trades_by_symbol[sym] >= max_trades_per_symbol:
                # v0.8.1.8.1: Log-once latch
                reject_key = f"{date_str}:{sym}:MAX_TRADES_PER_SYMBOL"
                if reject_key not in early_reject_logged:
                    candidate_ts = bar.ts if hasattr(bar, 'ts') else f"bar_{i}"
                    log.warning(f"[WHY] v0.8.1.8.1 EARLY_REJECT reason=MAX_TRADES_PER_SYMBOL symbol={sym} ts={candidate_ts} details=count={trades_by_symbol[sym]} limit={max_trades_per_symbol}")
                    early_reject_logged.add(reject_key)
                continue

            # v0.8.1.7.0: Check pending entry confirmation (if any)
            if pending_entry is not None and position is None:  # v0.8.1.7.0
                signal_idx = pending_entry["signal_idx"]  # v0.8.1.7.0
                expires_idx = pending_entry["expires_idx"]  # v0.8.1.7.0
                vwap_at_signal = pending_entry["vwap_at_signal"]  # v0.8.1.7.0
                max_high_since_signal = pending_entry["max_high_since_signal"]  # v0.8.1.7.0
                  # v0.8.1.7.0
                # Update max_high_since_signal with current bar  # v0.8.1.7.0
                max_high_since_signal = max(max_high_since_signal, bar.h)  # v0.8.1.7.0
                pending_entry["max_high_since_signal"] = max_high_since_signal  # v0.8.1.7.0
                  # v0.8.1.7.0
                # Check if confirmation condition is met  # v0.8.1.7.0
                confirmed = strat._post_entry_expansion_confirmed(sym, max_high_since_signal, vwap_at_signal)  # v0.8.1.7.0
                  # v0.8.1.7.0
                if confirmed:  # v0.8.1.7.0: expansion confirmed, enter now
                    expansion_bps = (max_high_since_signal - vwap_at_signal) / vwap_at_signal * 10_000 if vwap_at_signal > 0 else 0.0  # v0.8.1.7.0
                    log.info(f"[WHY] v0.8.1.7.0 POST_EXP: CONFIRMED symbol={sym} confirm_time={bar.ts} "  # v0.8.1.7.0
                            f"observed_bps={expansion_bps:.2f} required_bps={strat.p.post_entry_expansion_min_bps}")  # v0.8.1.7.0
                    # Enter on this bar (using pending entry data)  # v0.8.1.7.0
                    entry = bar.c  # v0.8.1.7.0: enter at current bar close
                    # v0.8.1.7.1: Rebase TP/SL to confirm-time entry (fixes TP-but-negative-pnl bug)
                    old_tp = pending_entry["tp"]  # v0.8.1.7.1
                    old_sl = pending_entry["sl"]  # v0.8.1.7.1
                    new_tp, new_sl = strat.targets(entry)  # v0.8.1.7.1: recompute from confirm-time entry
                    log.info(f"[WHY] v0.8.1.7.1 TP_SL_REBASE symbol={sym} entry={entry} old_tp={old_tp} old_sl={old_sl} new_tp={new_tp} new_sl={new_sl}")  # v0.8.1.7.1
                    tp = new_tp  # v0.8.1.7.1
                    sl = new_sl  # v0.8.1.7.1
                    
                    # v0.8.1.8.0: Confirm-Bar Execution Safety Guard
                    # Reject trade if confirmation bar breaches stop intrabar (structurally invalid execution)
                    confirm_bar = pos_bar_by_ts.get(bar.ts, bar)  # v0.8.1.8.0: bar is the confirmation bar
                    direction = "long"  # v0.8.1.8.0: SimpleBreakoutStrategy is long-only
                    if direction == "long" and confirm_bar.l <= sl:  # v0.8.1.8.0
                        log.warning(f"[WHY] v0.8.1.8.1 CONFIRM_BAR_STOP_VIOLATION symbol={sym} direction={direction} ts={confirm_bar.ts} low={confirm_bar.l} stop={sl}")  # v0.8.1.8.0
                        pending_entry = None  # v0.8.1.8.0: clear pending, no position created
                        continue  # v0.8.1.8.0: skip entry, proceed to next bar
                    
                    # v0.8.1.23.0 / v0.8.1.24.0: POST_DAMAGE_ENTRY_LOCKOUT with VWAP_HEAL_ESCAPE (pending_entry confirmation path)
                    if damage_first_idx is not None and damage_first_idx < i:  # v0.8.1.23.0 / v0.8.1.24.0
                        # v0.8.1.24.0: Check escape hatch conditions
                        is_rth_bar_check = (isinstance(bar.ts, str) and bar.ts >= "09:30" and bar.ts <= "16:00")  # v0.8.1.24.0
                        escape_hatch_allowed_at_i = (  # v0.8.1.24.0
                            post_damage_heal_attempt_used is False  # v0.8.1.24.0
                            and heal_ready_idx is not None  # v0.8.1.24.0
                            and i == heal_ready_idx + 1  # v0.8.1.24.0: entry only on next bar after 2nd confirmation
                            and heal_reclaim_idx is not None  # v0.8.1.24.0
                            and heal_window_damage_seen is False  # v0.8.1.24.0
                            and is_rth_bar_check  # v0.8.1.24.0
                        )  # v0.8.1.24.0
                        
                        if not escape_hatch_allowed_at_i:  # v0.8.1.24.0: escape hatch does NOT apply, enforce lockout
                            if not post_damage_lockout_logged:  # v0.8.1.23.0: log once per symbol/day
                                log.warning(f"[WHY] v0.8.1.23.0 POST_DAMAGE_ENTRY_LOCKOUT symbol={sym} day_class={day_class} entry_ts={bar.ts} entry_i={i} damage_ts={damage_first_ts} damage_i={damage_first_idx} source=pending_confirm")  # v0.8.1.23.0
                                post_damage_lockout_logged = True  # v0.8.1.23.0
                            telemetry["count_post_damage_entry_lockout_blocks"] += 1  # v0.8.1.23.0
                            day_post_damage_entry_lockout_blocks_total += 1  # v0.8.1.23.0
                            pending_entry = None  # v0.8.1.23.0: clear pending, no position created
                            continue  # v0.8.1.23.0: skip entry, proceed to next bar
                        # v0.8.1.24.0: else escape_hatch_allowed_at_i is True, allow confirmation to proceed
                    
                    qty = pending_entry["qty"]  # v0.8.1.7.0
                    position = {"symbol": sym, "entry": entry, "i": i, "tp": tp, "sl": sl, "qty": qty}  # v0.8.1.7.0: use current bar index
                    
                    # v0.8.1.24.0: Track heal entry if escape hatch was used
                    if damage_first_idx is not None and damage_first_idx < i:  # v0.8.1.24.0: lockout condition was met
                        is_rth_bar_check = (isinstance(bar.ts, str) and bar.ts >= "09:30" and bar.ts <= "16:00")  # v0.8.1.24.0
                        escape_hatch_was_used = (  # v0.8.1.24.0
                            post_damage_heal_attempt_used is False  # v0.8.1.24.0: check before setting
                            and heal_ready_idx is not None  # v0.8.1.24.0
                            and i == heal_ready_idx + 1  # v0.8.1.24.0
                            and heal_reclaim_idx is not None  # v0.8.1.24.0
                            and heal_window_damage_seen is False  # v0.8.1.24.0
                            and is_rth_bar_check  # v0.8.1.24.0
                        )  # v0.8.1.24.0
                        if escape_hatch_was_used:  # v0.8.1.24.0
                            post_damage_heal_attempt_used = True  # v0.8.1.24.0
                            day_post_damage_heal_entries_allowed_total += 1  # v0.8.1.24.0
                            log.info(f"[WHY] v0.8.1.24.0 POST_DAMAGE_HEAL_ENTRY_ALLOWED symbol={sym} day_class={day_class} entry_ts={bar.ts} entry_i={i} reclaim_i={heal_reclaim_idx} confirm2_i={heal_ready_idx} allow_i={i} source=pending_confirm")  # v0.8.1.24.0
                    
                    log.info(f"[WHY] v0.8.1.7.0 POST_EXP: POSITION_SET symbol={sym} i={i} bar_ts={bar.ts} entry={entry} tp={tp} sl={sl} qty={qty}")  # v0.8.1.7.0
                    position["trade_id"] = pending_entry.get("trade_id")  # v0.8.1.7.0
                    position["entry_time_iso"] = bar.ts  # v0.8.1.7.0: actual entry time is now
                    
                    # v0.8.1.21.0: Compute minutes_since_damage at entry (observability only)
                    if isinstance(i, int) and i >= 8:  # v0.8.1.21.0
                        for j in range(i - 1, max(0, i - REGIME_DAMAGE_LOOKBACK_BARS) - 1, -1):  # v0.8.1.21.0: scan backwards up to REGIME_DAMAGE_LOOKBACK_BARS bars
                            b = bars[j]  # v0.8.1.21.0
                            body = abs(b.c - b.o)  # v0.8.1.21.0
                            rng = max(b.h - b.l, 1e-9)  # v0.8.1.21.0
                            body_fraction = body / rng  # v0.8.1.21.0
                            if b.c < b.o and body_fraction >= 0.60:  # v0.8.1.21.0: structural damage (same as guard)
                                day_minutes_since_damage_at_entry_list.append(i - j)  # v0.8.1.21.0
                                break  # v0.8.1.21.0
                    
                    # v0.8.1.20.0: Console TRADE CARD output (observability only, ASCII-only)
                    # v0.8.1.20.0: Compute truthful guard status
                    confirm_bar_guard_enabled_val = True  # v0.8.1.20.0: always on by design
                    marginal_vwap_gate_enabled_val = bool(require_day_follow_through and is_marginal_day)  # v0.8.1.20.0
                    post_damage_weak_reclaim_guard_enabled_val = bool((scenario_name or scn) == "B" and is_hostile_day)  # v0.8.1.22.0 hostile-only
                    
                    _print_trade_card_entry(
                        sym=sym,
                        date_str=date_str,
                        scenario=scenario_name or scn or "UNKNOWN",
                        entry_time=bar.ts if bar.ts else f"bar_{i}",
                        entry_price=entry,
                        tp=tp,
                        sl=sl,
                        qty=qty,
                        risk_usd=pending_entry.get("risk_usd", None),  # v0.8.1.20.0: no fallback, None prints N/A
                        daily_max_loss=daily_max_loss,
                        max_trades_per_symbol=max_trades_per_symbol,
                        trades_count_before=trades_by_symbol[sym],
                        day_pnl_before=cum_pnl,
                        day_class=day_class,
                        close_gt_vwap_count=close_gt_vwap_count,
                        gate_minutes=day_follow_through_minutes,
                        day_gate_failed=day_gate_failed,
                        require_day_follow_through=require_day_follow_through,
                        bar=bar,
                        strat=strat,
                        telemetry=telemetry,
                        reject_reclaim_after_damage_effective=reject_reclaim_after_damage_effective,
                        auto_enabled=auto_enabled,
                        vwap_extension_max_pct=vwap_extension_max_pct,
                        entry_idx=i,  # v0.8.1.20.0
                        should_enter=pending_entry.get("should_enter_at_signal", None),  # v0.8.1.20.0: signal-time truth
                        allow_new_trade=pending_entry.get("allow_new_trade_at_signal", None),  # v0.8.1.20.0: signal-time truth
                        confirm_bar_guard_enabled=confirm_bar_guard_enabled_val,  # v0.8.1.20.0
                        marginal_vwap_gate_enabled=marginal_vwap_gate_enabled_val,  # v0.8.1.20.0
                        post_damage_weak_reclaim_guard_enabled=post_damage_weak_reclaim_guard_enabled_val,  # v0.8.1.20.0
                        post_expansion_confirmed=True,
                        expansion_bps=expansion_bps,
                    )
                    
                    # TWCS snapshot for confirmed entry (reuse existing TWCS logic below)  # v0.8.1.7.0
                    # Clear pending entry  # v0.8.1.7.0
                    pending_entry = None  # v0.8.1.7.0
                    
                    # v0.8.1.0.0: TWCS entry snapshot hook (non-blocking, best-effort) - reused for confirmed entries
                    if twcs_enabled:
                        try:
                            entry_time_iso = bar.ts
                            trade_id = position.get("trade_id", f"{sym}_{date_str}_{entry_time_iso.replace(':','')}")
                            root_out = Path(settings.out_root) if hasattr(settings, "out_root") else Path("out")
                            snapshot_dir = twcs.build_snapshot_dir(
                                root_out=root_out,
                                date_str=date_str,
                                scenario=(scenario_name or scn),
                                symbol=sym,
                                trade_id=trade_id,
                            )
                            candles_1m, window_meta_1m = load_twcs_minute_window(
                                symbol=sym,
                                date_str=date_str,
                                target_time_str=entry_time_iso,
                                window_before=10,
                                window_after=0,
                            )
                            entry_candles_1s, entry_meta_1s = load_twcs_second_window(
                                symbol=sym,
                                date_str=date_str,
                                target_time_str=entry_time_iso,
                                window_before_seconds=60,
                                window_after_seconds=0,
                            )
                            entry_indicators: Dict[str, Any] = {}
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
                                "candles_1m": candles_1m,
                                "window_size_1m": window_meta_1m.get("window_size_1m", 0),
                                "window_before_1m": window_meta_1m.get("window_before_1m", 10),
                                "window_after_1m": window_meta_1m.get("window_after_1m", 0),
                                "candles_1s": entry_candles_1s,
                                "window_size_1s": entry_meta_1s.get("window_size_1s", 0),
                                "window_before_1s": entry_meta_1s.get("window_before_1s", 60),
                                "window_after_1s": entry_meta_1s.get("window_after_1s", 0),
                                "indicators": entry_indicators,
                            }
                            twcs.save_entry_snapshot(snapshot_dir, entry_meta)
                            if plot_twcs_flag:
                                try:
                                    out_png = os.path.join(snapshot_dir, "trade_snapshot_entry.png")
                                    plot_twcs_snapshot(entry_meta, out_png)
                                except Exception as exc:
                                    print(f"[WARN] v0.8.1.0.5: Failed to plot entry TWCS for {sym}: {exc}", file=sys.stderr)
                        except Exception as exc:
                            print(f"[WARN] v0.8.1.0.1: Failed to save TWCS entry snapshot for {sym}: {exc}", file=sys.stderr)
                elif i > expires_idx:  # v0.8.1.7.0: confirmation window expired
                    expansion_bps = (max_high_since_signal - vwap_at_signal) / vwap_at_signal * 10_000 if vwap_at_signal > 0 else 0.0  # v0.8.1.7.0
                    log.info(f"[WHY] v0.8.1.7.0 POST_EXP: EXPIRED symbol={sym} reason=no_expansion "  # v0.8.1.7.0
                            f"observed_bps={expansion_bps:.2f} required_bps={strat.p.post_entry_expansion_min_bps}")  # v0.8.1.7.0
                    pending_entry = None  # v0.8.1.7.0: drop pending entry
                # else: still within window, keep checking  # v0.8.1.7.0

            # entry logic
            # v0.8.1.9.0: Compute effective_day_gate_failed (override for marginal days)
            effective_day_gate_failed = day_gate_failed  # v0.8.1.9.0: start with computed value
            if is_marginal_day and marginal_stop1loss_enabled:  # v0.8.1.17.0: new policy branch
                if marginal_sl_seen:  # v0.8.1.17.0: SL occurred, block all further entries
                    effective_day_gate_failed = True  # v0.8.1.17.0
                    reject_key = f"{date_str}:{sym}:MARGINAL_STOP_AFTER_1_LOSS_BLOCK"  # v0.8.1.17.0
                    if reject_key not in early_reject_logged:  # v0.8.1.17.0
                        candidate_ts = bar.ts if hasattr(bar, 'ts') else f"bar_{i}"  # v0.8.1.17.0
                        log.warning(f"[WHY] v0.8.1.17.0 EARLY_REJECT reason=MARGINAL_STOP_AFTER_1_LOSS_BLOCK symbol={sym} ts={candidate_ts} details=sl_seen=True day_trade_count={day_trade_count}")  # v0.8.1.17.0
                        early_reject_logged.add(reject_key)  # v0.8.1.17.0
                else:  # v0.8.1.17.0: no SL yet, allow entries
                    effective_day_gate_failed = False  # v0.8.1.17.0
                    if not marginal_stop1loss_eligible_logged:  # v0.8.1.17.0: use separate latch
                        log.info("[INFO] v0.8.1.17.0 MARGINAL_STOP_AFTER_1_LOSS_ELIGIBLE sl_seen=False day_trade_count=%d", day_trade_count)  # v0.8.1.17.0
                        marginal_stop1loss_eligible_logged = True  # v0.8.1.17.0
            elif is_marginal_day and day_trade_count < 1:  # v0.8.1.9.0: baseline behavior (feature disabled)
                effective_day_gate_failed = False  # v0.8.1.9.0: allow first trade on marginal day
                if not marginal_eligible_logged:  # v0.8.1.9.0: log once per day
                    log.info("[INFO] v0.8.1.9.0 MARGINAL_DAY_ELIGIBLE override_day_gate_failed=True day_trade_count=%d", day_trade_count)  # v0.8.1.9.0
                    marginal_eligible_logged = True  # v0.8.1.9.0
            elif is_marginal_day and day_trade_count >= 1:  # v0.8.1.9.0: enforce 1-trade cap on marginal days (baseline)
                effective_day_gate_failed = True  # v0.8.1.9.0: block further entries
                if not marginal_cap_reached_logged:  # v0.8.1.9.0: log once per day
                    log.info("[WHY] v0.8.1.9.0 MARGINAL_DAY_TRADE_CAP_REACHED day_trade_count=%d", day_trade_count)  # v0.8.1.9.0
                    marginal_cap_reached_logged = True  # v0.8.1.9.0

            # v0.8.1.8.1: Log early reject for day gate before combined check
            if effective_day_gate_failed and position is None and pending_entry is None:  # v0.8.1.9.0: use effective_day_gate_failed
                # v0.8.1.17.0: Skip misleading DAY_GATE_FAILED log when stop-after-loss is the controlling reason
                if not (is_marginal_day and marginal_stop1loss_enabled and marginal_sl_seen):  # v0.8.1.17.0
                    # v0.8.1.8.1: Log-once latch
                    reject_key = f"{date_str}:{sym}:DAY_GATE_FAILED"
                    if reject_key not in early_reject_logged:
                        candidate_ts = bar.ts if hasattr(bar, 'ts') else f"bar_{i}"
                        log.warning(f"[WHY] v0.8.1.8.1 EARLY_REJECT reason=DAY_GATE_FAILED symbol={sym} ts={candidate_ts} details=gate_minutes={day_follow_through_minutes} min_symbols={day_follow_through_min_symbols} close_gt_vwap_cnt={close_gt_vwap_count} require_close_gt_vwap={require_day_gate_close_gt_vwap}")
                        early_reject_logged.add(reject_key)
            
            # v0.8.1.11.0: Marginal VWAP acceptance (windowed, 2-of-3)
            # Only applies when: DAY_GATE on, marginal day, entry otherwise eligible
            # v0.8.1.17.0: updated condition to support stop-after-1-loss policy
            if (require_day_follow_through and is_marginal_day and position is None and pending_entry is None and not effective_day_gate_failed
                and (
                    (not marginal_stop1loss_enabled and day_trade_count < 1)  # v0.8.1.17.0: baseline behavior
                    or (marginal_stop1loss_enabled and not marginal_sl_seen)  # v0.8.1.17.0: new policy behavior
                )
            ):  # v0.8.1.11.0 / v0.8.1.17.0
                # v0.8.1.11.0: Compute VWAP incrementally from bar 0 through i-1
                cum_pv = 0.0  # v0.8.1.11.0
                cum_v = 0.0  # v0.8.1.11.0
                vwap_map = {}  # v0.8.1.11.0: store vwap for each bar index
                for k in range(i):  # v0.8.1.11.0: k = 0..i-1
                    b_k = bars[k]  # v0.8.1.11.0
                    tp = (b_k.h + b_k.l + b_k.c) / 3.0  # v0.8.1.11.0
                    cum_pv += tp * b_k.v  # v0.8.1.11.0
                    cum_v += b_k.v  # v0.8.1.11.0
                    if cum_v > 0:  # v0.8.1.11.0
                        vwap_map[k] = cum_pv / cum_v  # v0.8.1.11.0
                    else:  # v0.8.1.11.0
                        vwap_map[k] = None  # v0.8.1.11.0
                
                # v0.8.1.11.0: Windowed acceptance — require hits>=2 in window {i-1, i-2, i-3}
                window = [i - 1, i - 2, i - 3]  # v0.8.1.11.0
                hits = 0  # v0.8.1.11.0
                fail_close = 0.0  # v0.8.1.11.0: for logging only
                fail_vwap = 0.0  # v0.8.1.11.0: for logging only
                fail_idx = None  # v0.8.1.11.0: for logging only
                
                for check_idx in window:  # v0.8.1.11.0
                    if check_idx < 0:  # v0.8.1.11.0: skip out-of-bounds
                        continue  # v0.8.1.11.0
                    
                    b_check = bars[check_idx]  # v0.8.1.11.0
                    vwap_check = vwap_map.get(check_idx)  # v0.8.1.11.0
                    
                    # v0.8.1.11.0: capture representative values for first checked bar (logging only)
                    if fail_idx is None:  # v0.8.1.11.0
                        fail_idx = check_idx  # v0.8.1.11.0
                        fail_close = b_check.c  # v0.8.1.11.0
                        fail_vwap = vwap_check if vwap_check is not None else 0.0  # v0.8.1.11.0
                    
                    # v0.8.1.11.0: qualifies := green AND close > VWAP
                    if vwap_check is not None and vwap_check > 0:  # v0.8.1.11.0
                        if b_check.c > b_check.o and b_check.c > vwap_check:  # v0.8.1.11.0
                            hits += 1  # v0.8.1.11.0
                
                if hits < 2:  # v0.8.1.11.0: reject this entry attempt (delay behavior)
                    reject_key = f"{date_str}:{sym}:MARGINAL_VWAP_WINDOW_REJECT"  # v0.8.1.11.0
                    if reject_key not in early_reject_logged:  # v0.8.1.11.0
                        candidate_ts = bar.ts if hasattr(bar, 'ts') else f"bar_{i}"  # v0.8.1.11.0
                        log.warning(f"[WHY] v0.8.1.11.0 MARGINAL_VWAP_WINDOW_REJECT symbol={sym} ts={candidate_ts} hits={hits} fail_idx={fail_idx} window=i-1,i-2,i-3 close={fail_close:.2f} vwap={fail_vwap:.2f}")  # v0.8.1.11.0
                        early_reject_logged.add(reject_key)  # v0.8.1.11.0
                    telemetry["count_marginal_vwap_gate_blocks"] += 1  # v0.8.1.20.0
                    continue  # v0.8.1.11.0: skip this bar's entry attempt
            
            # v0.8.1.19.0: Compute entry conditions once to avoid double-evaluation (guard + final entry share same result)
            should_enter_now = strat.should_enter(bars, i)
            allow_new_trade_now = risk.allow_new_trade()
            
            # v0.8.1.19.0: Post-Damage Weak VWAP Reclaim Guard (Healthy Days)
            # Scenario B-only: block late/weak VWAP reclaims after structural damage on healthy days
            if (scenario_name or scn) == "B" and is_hostile_day and position is None and pending_entry is None and (not effective_day_gate_failed) and should_enter_now and allow_new_trade_now:  # v0.8.1.22.0 hostile-only
                # v0.8.1.19.0: Hardcoded thresholds
                DAMAGE_LOOKBACK_BARS = 60  # v0.8.1.19.0
                LATE_RECLAIM_MINUTES = 15  # v0.8.1.19.0
                MIN_HOLD_CANDLES_PRE = 2  # v0.8.1.19.0
                
                # v0.8.1.19.0: Current bar context
                ts_now = bar.ts if hasattr(bar, 'ts') else f"bar_{i}"  # v0.8.1.19.0
                close_now = bar.c  # v0.8.1.19.0
                vwap_now = bar.vwap if hasattr(bar, 'vwap') else None  # v0.8.1.19.0
                
                # v0.8.1.19.0: Reclaim detection (close-cross only)
                is_reclaim_bar = False  # v0.8.1.19.0
                if i > 0 and vwap_now is not None and vwap_now > 0:  # v0.8.1.19.0
                    close_prev = bars[i - 1].c  # v0.8.1.19.0
                    vwap_prev = bars[i - 1].vwap if hasattr(bars[i - 1], 'vwap') else None  # v0.8.1.19.0
                    if vwap_prev is not None and vwap_prev > 0:  # v0.8.1.19.0
                        is_reclaim_bar = (close_prev <= vwap_prev) and (close_now > vwap_now)  # v0.8.1.19.0
                
                # v0.8.1.19.0: Above-VWAP streak BEFORE entry (excluding current bar i)
                above_vwap_streak_pre = 0  # v0.8.1.19.0
                k = i - 1  # v0.8.1.19.0
                while k >= 0:  # v0.8.1.19.0
                    vwap_k = bars[k].vwap if hasattr(bars[k], 'vwap') else None  # v0.8.1.19.0
                    if vwap_k is not None and vwap_k > 0 and bars[k].c > vwap_k:  # v0.8.1.19.0
                        above_vwap_streak_pre += 1  # v0.8.1.19.0
                        k -= 1  # v0.8.1.19.0
                    else:  # v0.8.1.19.0
                        break  # v0.8.1.19.0
                
                # v0.8.1.19.0: Find last damage index within lookback (reuse existing damage definition)
                last_damage_idx = None  # v0.8.1.19.0
                start_j = max(0, i - DAMAGE_LOOKBACK_BARS)  # v0.8.1.19.0
                for j in range(i - 1, start_j - 1, -1):  # v0.8.1.19.0: scan backwards
                    b = bars[j]  # v0.8.1.19.0
                    body = abs(b.c - b.o)  # v0.8.1.19.0
                    rng = max(b.h - b.l, 1e-9)  # v0.8.1.19.0
                    body_fraction = body / rng  # v0.8.1.19.0
                    if b.c < b.o and body_fraction >= 0.60:  # v0.8.1.19.0: structural damage candle
                        last_damage_idx = j  # v0.8.1.19.0
                        break  # v0.8.1.19.0
                
                # v0.8.1.19.0: Compute minutes since damage
                if last_damage_idx is not None:  # v0.8.1.19.0
                    minutes_since_damage = i - last_damage_idx  # v0.8.1.19.0
                    
                    # v0.8.1.19.0: Block condition (narrow, matches hypothesis)
                    if (minutes_since_damage >= LATE_RECLAIM_MINUTES  # v0.8.1.19.0
                        and (is_reclaim_bar or above_vwap_streak_pre < MIN_HOLD_CANDLES_PRE)):  # v0.8.1.19.0
                        # v0.8.1.19.0: De-dupe via existing early_reject_logged set
                        reject_key = f"{date_str}:{sym}:POST_DAMAGE_WEAK_VWAP_RECLAIM_BLOCK"  # v0.8.1.19.0
                        if reject_key not in early_reject_logged:  # v0.8.1.19.0
                            vwap_str = f"{vwap_now:.2f}" if (vwap_now is not None and vwap_now > 0) else "N/A"  # v0.8.1.19.0: safe formatting
                            log.warning(  # v0.8.1.19.0
                                f"[WHY] v0.8.1.19.0 POST_DAMAGE_WEAK_VWAP_RECLAIM_BLOCK "  # v0.8.1.19.0
                                f"symbol={sym} ts={ts_now} is_healthy_day={is_healthy_day} "  # v0.8.1.19.0
                                f"minutes_since_damage={minutes_since_damage} "  # v0.8.1.19.0
                                f"above_vwap_streak_pre={above_vwap_streak_pre} "  # v0.8.1.19.0
                                f"is_reclaim_bar={is_reclaim_bar} "  # v0.8.1.19.0
                                f"close={close_now:.2f} vwap={vwap_str}"  # v0.8.1.19.0
                            )  # v0.8.1.19.0
                            early_reject_logged.add(reject_key)  # v0.8.1.19.0
                        telemetry["count_post_damage_weak_reclaim_blocks"] += 1  # v0.8.1.20.0
                        continue  # v0.8.1.19.0: skip this bar's entry attempt
            
            # v0.8.1.19.0: Reuse should_enter_now / allow_new_trade_now to prevent double evaluation
            if (not effective_day_gate_failed) and position is None and pending_entry is None and should_enter_now and allow_new_trade_now:  # v0.8.1.3.0: added day gate check; v0.8.1.7.0: added pending_entry check; v0.8.1.9.0: use effective_day_gate_failed
                # v0.8.1.4.0: Structural damage guard (reject weak VWAP reclaim after structural damage)
                blocked = False  # v0.8.1.4.0
                if reject_reclaim_after_damage_effective:  # v0.8.1.4.0 / v0.8.1.5.0: use effective flag
                    # v0.8.1.4.0: STEP 1 — Detect structural damage in lookback window [i-8, i-1]
                    recent_structural_damage = False  # v0.8.1.4.0
                    if i >= 8:  # v0.8.1.4.0: need at least 8 candles before entry
                        for j in range(i - 8, i):  # v0.8.1.4.0: scan [i-8, i-1]
                            b = bars[j]  # v0.8.1.4.0
                            body = abs(b.c - b.o)  # v0.8.1.4.0
                            rng = max(b.h - b.l, 1e-9)  # v0.8.1.4.0
                            body_fraction = body / rng  # v0.8.1.4.0
                            if b.c < b.o and body_fraction >= 0.60:  # v0.8.1.4.0: structural damage candle
                                recent_structural_damage = True  # v0.8.1.4.0
                                # v0.8.1.20.0: Track last damage for telemetry
                                telemetry["last_damage_idx"] = j
                                telemetry["last_damage_ts"] = bars[j].ts if hasattr(bars[j], 'ts') else f"bar_{j}"
                                break  # v0.8.1.4.0
                    if recent_structural_damage:  # v0.8.1.4.0
                        log.info(f"STRUCT_DAMAGE v0.8.1.4.0: detected symbol={sym}")  # v0.8.1.4.0
                    # v0.8.1.4.0: STEP 2 — If damage detected, verify strong VWAP acceptance [i-1, i]
                    if recent_structural_damage:  # v0.8.1.4.0
                        if i < 1:  # v0.8.1.4.0: insufficient bars → BLOCK
                            blocked = True  # v0.8.1.4.0
                            log.info(f"STRUCT_DAMAGE v0.8.1.4.0: BLOCKED symbol={sym} reason=weak_vwap_reclaim")  # v0.8.1.4.0
                        else:  # v0.8.1.4.0
                            # v0.8.1.4.0: Compute VWAP incrementally from bar 0 (must match day-gate logic)
                            running_pv_guard = 0.0  # v0.8.1.4.0
                            running_v_guard = 0.0  # v0.8.1.4.0
                            vwap_map = {}  # v0.8.1.4.0: store VWAP for each bar index
                            for k in range(i + 1):  # v0.8.1.4.0: compute up to i (entry bar)
                                b_k = bars[k]  # v0.8.1.4.0
                                typical_k = (b_k.h + b_k.l + b_k.c) / 3.0  # v0.8.1.4.0
                                running_pv_guard += typical_k * b_k.v  # v0.8.1.4.0
                                running_v_guard += b_k.v  # v0.8.1.4.0
                                if running_v_guard > 0:  # v0.8.1.4.0
                                    vwap_map[k] = running_pv_guard / running_v_guard  # v0.8.1.4.0
                                else:  # v0.8.1.4.0
                                    vwap_map[k] = None  # v0.8.1.4.0
                            # v0.8.1.4.0: Recovery requirement (STRICT) — BOTH candles [i-1, i] must pass
                            recovery_passed = True  # v0.8.1.4.0
                            for j_rec in [i - 1, i]:  # v0.8.1.4.0: last completed + entry candle
                                b_rec = bars[j_rec]  # v0.8.1.4.0
                                vwap_rec = vwap_map.get(j_rec)  # v0.8.1.4.0
                                if vwap_rec is None or vwap_rec == 0:  # v0.8.1.4.0: treat as FAIL
                                    recovery_passed = False  # v0.8.1.4.0
                                    break  # v0.8.1.4.0
                                if not (b_rec.c > b_rec.o and b_rec.c > vwap_rec):  # v0.8.1.4.0: must be green AND above VWAP
                                    recovery_passed = False  # v0.8.1.4.0
                                    break  # v0.8.1.4.0
                            if not recovery_passed:  # v0.8.1.4.0
                                blocked = True  # v0.8.1.4.0
                                log.info(f"STRUCT_DAMAGE v0.8.1.4.0: BLOCKED symbol={sym} reason=weak_vwap_reclaim")  # v0.8.1.4.0
                            else:  # v0.8.1.4.0
                                log.info(f"STRUCT_DAMAGE v0.8.1.4.0: PASSED symbol={sym} reason=accepted_above_vwap")  # v0.8.1.4.0
                                
                                # v0.8.1.12.0: Post-Damage VWAP Reclaim Continuation Guard
                                # v0.8.1.12.0: Count green candles above VWAP in last 3 completed bars before entry
                                green_above_vwap_count = 0  # v0.8.1.12.0
                                continuation_window = [i - 1, i - 2, i - 3]  # v0.8.1.12.0
                                
                                for j in continuation_window:  # v0.8.1.12.0
                                    if j < 0:  # v0.8.1.12.0: skip out-of-bounds
                                        continue  # v0.8.1.12.0
                                    
                                    b_cont = bars[j]  # v0.8.1.12.0
                                    vwap_cont = vwap_map.get(j)  # v0.8.1.12.0: use existing vwap_map
                                    
                                    # v0.8.1.12.0: qualifies := green AND close > VWAP
                                    if vwap_cont is not None and b_cont.c > b_cont.o and b_cont.c > vwap_cont:  # v0.8.1.12.0
                                        green_above_vwap_count += 1  # v0.8.1.12.0
                                
                                # v0.8.1.12.0: Require at least 2 continuation bars to proceed
                                if green_above_vwap_count < 2:  # v0.8.1.12.0
                                    reject_key = f"{date_str}:{sym}:POST_DAMAGE_CONTINUATION_FAIL"  # v0.8.1.12.0
                                    if reject_key not in early_reject_logged:  # v0.8.1.12.0
                                        candidate_ts = bar.ts if hasattr(bar, 'ts') else f"bar_{i}"  # v0.8.1.12.0
                                        log.warning(f"[WHY] v0.8.1.12.0 POST_DAMAGE_CONTINUATION_BLOCK symbol={sym} ts={candidate_ts} count={green_above_vwap_count} window=i-1,i-2,i-3 recovery_passed=True recent_structural_damage=True")  # v0.8.1.12.x: enhanced observability
                                        early_reject_logged.add(reject_key)  # v0.8.1.12.0
                                        
                                        # v0.8.1.13.0: Write blocked-trade JSON snapshot (best-effort, diagnostics-only)
                                        try:  # v0.8.1.13.0
                                            import json  # v0.8.1.13.0
                                            blocked_dir = os.path.join(out_dir, "blocked_candidates")  # v0.8.1.13.0
                                            os.makedirs(blocked_dir, exist_ok=True)  # v0.8.1.13.0
                                            ts_clean = candidate_ts.replace(":", "").replace("/", "_").replace("\\", "_").replace(" ", "_")  # v0.8.1.13.0
                                            json_filename = f"POST_DAMAGE_CONTINUATION_BLOCK_{sym}_{ts_clean}.json"  # v0.8.1.13.0
                                            json_path = os.path.join(blocked_dir, json_filename)  # v0.8.1.13.0
                                            payload = {  # v0.8.1.13.0
                                                "version": "v0.8.1.13.0",  # v0.8.1.13.0
                                                "reason": "POST_DAMAGE_CONTINUATION_BLOCK",  # v0.8.1.13.0
                                                "symbol": sym,  # v0.8.1.13.0
                                                "date": date_str,  # v0.8.1.13.0
                                                "ts": candidate_ts,  # v0.8.1.13.0
                                                "i": i,  # v0.8.1.13.0
                                                "count": green_above_vwap_count,  # v0.8.1.13.0
                                                "window": "i-1,i-2,i-3",  # v0.8.1.13.0
                                                "recent_structural_damage": True,  # v0.8.1.13.0
                                                "recovery_passed": True,  # v0.8.1.13.0
                                                "scenario": (scenario_name or scn),  # v0.8.1.13.0
                                                "day_class": day_class,  # v0.8.1.13.0
                                                "auto_struct_damage": auto_enabled,  # v0.8.1.13.0
                                                "reject_reclaim_effective": reject_reclaim_after_damage_effective,  # v0.8.1.13.0
                                            }  # v0.8.1.13.0
                                            with open(json_path, "w", encoding="utf-8") as f:  # v0.8.1.13.0
                                                json.dump(payload, f, indent=2, sort_keys=True)  # v0.8.1.13.0
                                        except Exception:  # v0.8.1.13.0
                                            pass  # v0.8.1.13.0: silent failure, never block trading logic
                                    continue  # v0.8.1.12.0: skip this bar's entry attempt
                
                if blocked:  # v0.8.1.4.0: skip entry on this bar
                    # v0.8.1.8.1: Log-once latch
                    reject_key = f"{date_str}:{sym}:STRUCT_DAMAGE_FAIL"
                    if reject_key not in early_reject_logged:
                        candidate_ts = bar.ts if hasattr(bar, 'ts') else f"bar_{i}"  # v0.8.1.8.1
                        log.warning(f"[WHY] v0.8.1.8.1 EARLY_REJECT reason=STRUCT_DAMAGE_FAIL symbol={sym} ts={candidate_ts} details=weak_vwap_reclaim recovery_failed lookback_bars=8 body_thresh=0.60")  # v0.8.1.8.1
                        early_reject_logged.add(reject_key)
                    telemetry["count_struct_damage_blocks"] += 1  # v0.8.1.20.0
                    continue  # v0.8.1.4.0
                
                # v0.8.1.23.0 / v0.8.1.24.0: POST_DAMAGE_ENTRY_LOCKOUT with VWAP_HEAL_ESCAPE (normal entry path, before position creation)
                if damage_first_idx is not None and damage_first_idx < i:  # v0.8.1.23.0 / v0.8.1.24.0
                    # v0.8.1.24.0: Check escape hatch conditions
                    is_rth_bar_check = (isinstance(bar.ts, str) and bar.ts >= "09:30" and bar.ts <= "16:00")  # v0.8.1.24.0
                    escape_hatch_allowed_at_i = (  # v0.8.1.24.0
                        post_damage_heal_attempt_used is False  # v0.8.1.24.0
                        and heal_ready_idx is not None  # v0.8.1.24.0
                        and i == heal_ready_idx + 1  # v0.8.1.24.0: entry only on next bar after 2nd confirmation
                        and heal_reclaim_idx is not None  # v0.8.1.24.0
                        and heal_window_damage_seen is False  # v0.8.1.24.0
                        and is_rth_bar_check  # v0.8.1.24.0
                    )  # v0.8.1.24.0
                    
                    if not escape_hatch_allowed_at_i:  # v0.8.1.24.0: escape hatch does NOT apply, enforce lockout
                        if not post_damage_lockout_logged:  # v0.8.1.23.0: log once per symbol/day
                            log.warning(f"[WHY] v0.8.1.23.0 POST_DAMAGE_ENTRY_LOCKOUT symbol={sym} day_class={day_class} entry_ts={bar.ts} entry_i={i} damage_ts={damage_first_ts} damage_i={damage_first_idx} source=normal")  # v0.8.1.23.0
                            post_damage_lockout_logged = True  # v0.8.1.23.0
                        telemetry["count_post_damage_entry_lockout_blocks"] += 1  # v0.8.1.23.0
                        day_post_damage_entry_lockout_blocks_total += 1  # v0.8.1.23.0
                        continue  # v0.8.1.23.0: skip this bar's entry attempt
                    # v0.8.1.24.0: else escape_hatch_allowed_at_i is True, allow entry attempt to proceed
                
                # v0.8.1.7.0: Post-entry expansion gate — create pending entry or enter immediately
                entry = bar.c  # v0.8.1.7.0: tentative entry price
                tp, sl = strat.targets(entry)  # v0.8.1.7.0

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

                # v0.8.1.7.0: build trade_id
                try:
                    entry_time_iso = bars[i].ts  # expected "HH:MM"
                    trade_id = f"{sym}_{date_str}_{entry_time_iso.replace(':','')}"
                except Exception:
                    entry_time_iso = bars[i].ts if i < len(bars) else ""
                    trade_id = f"{sym}_{date_str}_{i}"

                # v0.8.1.7.0: Check if post-entry expansion gate is enabled
                if getattr(strat.p, "post_entry_expansion_gate", False):  # v0.8.1.8.2
                    # v0.8.1.7.0: Create pending entry instead of immediate entry
                    # Compute VWAP at signal bar
                    running_pv_signal = 0.0  # v0.8.1.7.0
                    running_v_signal = 0.0  # v0.8.1.7.0
                    for k in range(i + 1):  # v0.8.1.7.0: compute up to signal bar i
                        b_k = bars[k]  # v0.8.1.7.0
                        typical_k = (b_k.h + b_k.l + b_k.c) / 3.0  # v0.8.1.7.0
                        running_pv_signal += typical_k * b_k.v  # v0.8.1.7.0
                        running_v_signal += b_k.v  # v0.8.1.7.0
                    vwap_at_signal = running_pv_signal / running_v_signal if running_v_signal > 0 else None  # v0.8.1.7.0
                    
                    if vwap_at_signal is None or vwap_at_signal <= 0:  # v0.8.1.7.0: fail closed
                        # v0.8.1.8.1: Log-once latch
                        reject_key = f"{date_str}:{sym}:VWAP_MISSING"
                        if reject_key not in early_reject_logged:
                            candidate_ts = bar.ts if hasattr(bar, 'ts') else f"bar_{i}"  # v0.8.1.8.1
                            log.info(f"[WHY] v0.8.1.7.0 POST_EXP: BLOCKED symbol={sym} reason=missing_vwap")  # v0.8.1.7.0
                            log.warning(f"[WHY] v0.8.1.8.1 EARLY_REJECT reason=VWAP_MISSING symbol={sym} ts={candidate_ts} details=vwap=None bar_ts={candidate_ts} bar_idx={i} running_v={running_v_signal:.0f}")  # v0.8.1.8.1
                            early_reject_logged.add(reject_key)
                        continue  # v0.8.1.7.0: skip this signal
                    
                    # v0.8.1.7.0: Create pending entry
                    expires_idx = i + strat.p.post_entry_expansion_minutes  # v0.8.1.7.0
                    pending_entry = {  # v0.8.1.7.0
                        "symbol": sym,  # v0.8.1.7.0
                        "signal_idx": i,  # v0.8.1.7.0
                        "signal_time": bars[i].ts,  # v0.8.1.7.0
                        "vwap_at_signal": vwap_at_signal,  # v0.8.1.7.0
                        "expires_idx": expires_idx,  # v0.8.1.7.0
                        "max_high_since_signal": bar.h,  # v0.8.1.7.0: start with signal bar high
                        "tp": tp,  # v0.8.1.7.0
                        "sl": sl,  # v0.8.1.7.0
                        "qty": qty,  # v0.8.1.7.0
                        "trade_id": trade_id,  # v0.8.1.7.0
                        "risk_usd": risk_usd,  # v0.8.1.20.0: store risk_usd for trade card
                        "should_enter_at_signal": should_enter_now,  # v0.8.1.20.0: capture signal-time truth
                        "allow_new_trade_at_signal": allow_new_trade_now,  # v0.8.1.20.0: capture signal-time truth
                    }  # v0.8.1.7.0
                    
                    # v0.8.1.24.0: Track heal entry if escape hatch was used (expansion gate ON path)
                    if damage_first_idx is not None and damage_first_idx < i:  # v0.8.1.24.0: lockout condition was met
                        is_rth_bar_check = (isinstance(bar.ts, str) and bar.ts >= "09:30" and bar.ts <= "16:00")  # v0.8.1.24.0
                        escape_hatch_was_used = (  # v0.8.1.24.0
                            post_damage_heal_attempt_used is False  # v0.8.1.24.0: check before setting
                            and heal_ready_idx is not None  # v0.8.1.24.0
                            and i == heal_ready_idx + 1  # v0.8.1.24.0
                            and heal_reclaim_idx is not None  # v0.8.1.24.0
                            and heal_window_damage_seen is False  # v0.8.1.24.0
                            and is_rth_bar_check  # v0.8.1.24.0
                        )  # v0.8.1.24.0
                        if escape_hatch_was_used:  # v0.8.1.24.0
                            post_damage_heal_attempt_used = True  # v0.8.1.24.0
                            day_post_damage_heal_entries_allowed_total += 1  # v0.8.1.24.0
                            log.info(f"[WHY] v0.8.1.24.0 POST_DAMAGE_HEAL_ENTRY_ALLOWED symbol={sym} day_class={day_class} entry_ts={bar.ts} entry_i={i} reclaim_i={heal_reclaim_idx} confirm2_i={heal_ready_idx} allow_i={i} source=normal")  # v0.8.1.24.0
                    
                    log.info(f"[WHY] v0.8.1.7.0 POST_EXP: PENDING symbol={sym} signal_time={bars[i].ts} "  # v0.8.1.7.0
                            f"minutes={strat.p.post_entry_expansion_minutes} min_bps={strat.p.post_entry_expansion_min_bps}")  # v0.8.1.7.0
                    # Do NOT create position yet; wait for confirmation  # v0.8.1.7.0
                else:  # v0.8.1.7.0: gate is OFF, enter immediately (legacy behavior)
                    position = {"symbol": sym, "entry": entry, "i": i, "tp": tp, "sl": sl, "qty": qty}
                    
                    # v0.8.1.24.0: Track heal entry if escape hatch was used (expansion gate OFF path)
                    if damage_first_idx is not None and damage_first_idx < i:  # v0.8.1.24.0: lockout condition was met
                        is_rth_bar_check = (isinstance(bar.ts, str) and bar.ts >= "09:30" and bar.ts <= "16:00")  # v0.8.1.24.0
                        escape_hatch_was_used = (  # v0.8.1.24.0
                            post_damage_heal_attempt_used is False  # v0.8.1.24.0: check before setting
                            and heal_ready_idx is not None  # v0.8.1.24.0
                            and i == heal_ready_idx + 1  # v0.8.1.24.0
                            and heal_reclaim_idx is not None  # v0.8.1.24.0
                            and heal_window_damage_seen is False  # v0.8.1.24.0
                            and is_rth_bar_check  # v0.8.1.24.0
                        )  # v0.8.1.24.0
                        if escape_hatch_was_used:  # v0.8.1.24.0
                            post_damage_heal_attempt_used = True  # v0.8.1.24.0
                            day_post_damage_heal_entries_allowed_total += 1  # v0.8.1.24.0
                            log.info(f"[WHY] v0.8.1.24.0 POST_DAMAGE_HEAL_ENTRY_ALLOWED symbol={sym} day_class={day_class} entry_ts={bar.ts} entry_i={i} reclaim_i={heal_reclaim_idx} confirm2_i={heal_ready_idx} allow_i={i} source=normal")  # v0.8.1.24.0

                    # attach to position for later use
                    if isinstance(position, dict):
                        position["trade_id"] = trade_id  # v0.8.1.0.0
                        position["entry_time_iso"] = entry_time_iso  # v0.8.1.0.0
                    
                    # v0.8.1.21.0: Compute minutes_since_damage at entry (observability only)
                    if isinstance(i, int) and i >= 8:  # v0.8.1.21.0
                        for j in range(i - 1, max(0, i - REGIME_DAMAGE_LOOKBACK_BARS) - 1, -1):  # v0.8.1.21.0: scan backwards up to REGIME_DAMAGE_LOOKBACK_BARS bars
                            b = bars[j]  # v0.8.1.21.0
                            body = abs(b.c - b.o)  # v0.8.1.21.0
                            rng = max(b.h - b.l, 1e-9)  # v0.8.1.21.0
                            body_fraction = body / rng  # v0.8.1.21.0
                            if b.c < b.o and body_fraction >= 0.60:  # v0.8.1.21.0: structural damage (same as guard)
                                day_minutes_since_damage_at_entry_list.append(i - j)  # v0.8.1.21.0
                                break  # v0.8.1.21.0
                    
                    # v0.8.1.20.0: Console TRADE CARD output (observability only, ASCII-only)
                    # v0.8.1.20.0: Compute truthful guard status
                    confirm_bar_guard_enabled_val = True  # v0.8.1.20.0: always on by design
                    marginal_vwap_gate_enabled_val = bool(require_day_follow_through and is_marginal_day)  # v0.8.1.20.0
                    post_damage_weak_reclaim_guard_enabled_val = bool((scenario_name or scn) == "B" and is_hostile_day)  # v0.8.1.22.0 hostile-only
                    
                    _print_trade_card_entry(
                        sym=sym,
                        date_str=date_str,
                        scenario=scenario_name or scn or "UNKNOWN",
                        entry_time=entry_time_iso if entry_time_iso else f"bar_{i}",
                        entry_price=entry,
                        tp=tp,
                        sl=sl,
                        qty=qty,
                        risk_usd=risk_usd,
                        daily_max_loss=daily_max_loss,
                        max_trades_per_symbol=max_trades_per_symbol,
                        trades_count_before=trades_by_symbol[sym],
                        day_pnl_before=cum_pnl,
                        day_class=day_class,
                        close_gt_vwap_count=close_gt_vwap_count,
                        gate_minutes=day_follow_through_minutes,
                        day_gate_failed=day_gate_failed,
                        require_day_follow_through=require_day_follow_through,
                        bar=bar,
                        strat=strat,
                        telemetry=telemetry,
                        reject_reclaim_after_damage_effective=reject_reclaim_after_damage_effective,
                        auto_enabled=auto_enabled,
                        vwap_extension_max_pct=vwap_extension_max_pct,
                        entry_idx=i,  # v0.8.1.20.0
                        should_enter=should_enter_now,  # v0.8.1.20.0: pass actual value
                        allow_new_trade=allow_new_trade_now,  # v0.8.1.20.0: pass actual value
                        confirm_bar_guard_enabled=confirm_bar_guard_enabled_val,  # v0.8.1.20.0
                        marginal_vwap_gate_enabled=marginal_vwap_gate_enabled_val,  # v0.8.1.20.0
                        post_damage_weak_reclaim_guard_enabled=post_damage_weak_reclaim_guard_enabled_val,  # v0.8.1.20.0
                    )

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
                # v0.8.1.7.0: Use frozen provider bar for TP/SL checks (matched by timestamp)
                pos_bar = pos_bar_by_ts.get(bar.ts, bar)  # v0.8.1.7.0: TP/SL must check against true OHLC
                
                # v0.8.1.7.0: Diagnostic - detect bar mutation before TP/SL evaluation
                if (bar.o, bar.h, bar.l, bar.c) != (pos_bar.o, pos_bar.h, pos_bar.l, pos_bar.c):
                    log.warning("[WARN] [POS_MGMT_MISMATCH] v0.8.1.7.0 symbol=%s ts=%s eval_ohlc=(%.4f,%.4f,%.4f,%.4f) pos_ohlc=(%.4f,%.4f,%.4f,%.4f)",
                                sym, bar.ts,
                                bar.o, bar.h, bar.l, bar.c,
                                pos_bar.o, pos_bar.h, pos_bar.l, pos_bar.c)
                    # v0.8.1.20.0: Telemetry ONLY when mismatch actually occurs
                    telemetry["pos_mgmt_mismatch_occurred"] = True
                    telemetry["pos_mgmt_mismatch_last"] = f"ts={bar.ts} eval=({bar.o:.4f},{bar.h:.4f},{bar.l:.4f},{bar.c:.4f}) pos=({pos_bar.o:.4f},{pos_bar.h:.4f},{pos_bar.l:.4f},{pos_bar.c:.4f})"
                tp = position["tp"]
                sl = position["sl"]
                qty = position["qty"]
                if sym == "TCMD" and date_str == "2025-08-05" and getattr(pos_bar, "ts", None) == "14:19":
                    print(f"[POS_MGMT_BAR] v0.8.1.7.0 symbol={sym} ts={pos_bar.ts} o={pos_bar.o} h={pos_bar.h} l={pos_bar.l} c={pos_bar.c} tp={tp} sl={sl}")
                if pos_bar.h >= tp:
                    pnl = (tp - entry) * qty
                    # v0.8.1.7.1: Enforce TP outcome invariant (TP must never lose money)
                    outcome = "ERR_TP_NEG_PNL" if pnl < 0 else "TP"  # v0.8.1.7.1
                    if outcome == "ERR_TP_NEG_PNL":  # v0.8.1.7.1
                        log.warning(f"[WHY] v0.8.1.7.1 OUTCOME_PNL_MISMATCH TP_NEG_PNL symbol={sym} entry={entry} tp={tp} sl={sl} qty={qty} pnl={pnl}")  # v0.8.1.7.1
                    trades.append((sym, outcome, pnl))  # v0.8.1.7.1

                    # v0.8.1.0.0: TWCS exit snapshot hook (non-blocking, best-effort)
                    if twcs_enabled:
                        try:
                            raw_trade_id = position.get("trade_id") if isinstance(position, dict) else None
                            entry_time_iso = position.get("entry_time_iso") if isinstance(position, dict) else None
                            exit_time_iso = pos_bar.ts  # v0.8.1.7.0: use pos_bar for exit time
                            
                            # v0.8.1.0.1: Ensure a stable TWCS trade_id for exit snapshots.
                            if raw_trade_id:
                                trade_id_for_twcs = str(raw_trade_id)
                            else:
                                trade_id_for_twcs = f"{sym}_{date_str}_{exit_time_iso.replace(':', '')}"

                            mfe_value = None  # v0.8.1.0.0: placeholder
                            mae_value = None  # v0.8.1.0.0: placeholder
                            pnl_raw = pnl
                            gross_entry_val = qty * entry if entry else 0.0
                            pnl_pct = (pnl / gross_entry_val * 100.0) if gross_entry_val else None
                            outcome_label = outcome  # v0.8.1.7.1: use exact outcome (TP or ERR_TP_NEG_PNL)

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

                    # v0.8.1.20.0: Console TRADE CARD output (observability only, ASCII-only)
                    entry_time_val = position.get('entry_time_iso', 'N/A')
                    entry_idx = position.get('i', None)
                    hold_bars = (i - entry_idx) if entry_idx is not None else None
                    # v0.8.1.20.0: Compute hold_minutes from HH:MM timestamps
                    exit_ts = pos_bar.ts if hasattr(pos_bar, 'ts') else None
                    entry_m = _hhmm_to_minutes(entry_time_val)
                    exit_m = _hhmm_to_minutes(exit_ts)
                    hold_minutes = (exit_m - entry_m) if (entry_m is not None and exit_m is not None) else None
                    bar_details_str = f"bar_high={pos_bar.h:.2f}, target={tp:.2f} => reached" if hasattr(pos_bar, 'h') else "N/A"
                    _print_trade_card_exit(
                        sym=sym,
                        date_str=date_str,
                        scenario=scenario_name or scn or "UNKNOWN",
                        entry_time=entry_time_val,
                        exit_time=pos_bar.ts if hasattr(pos_bar, 'ts') else f"bar_{i}",
                        entry_price=entry,
                        exit_price=tp,
                        tp=tp,
                        sl=sl,
                        qty=qty,
                        pnl=pnl,
                        outcome=outcome,
                        telemetry=telemetry,
                        hold_minutes=hold_minutes,  # v0.8.1.20.0
                        hold_bars=hold_bars,
                        exit_reason="Target price reached",
                        bar_details=bar_details_str,
                    )
                    
                    risk.on_trade_closed(pnl)
                    sizer.on_exit(pnl)  # NEW: update sizing state
                    trades_by_symbol[sym] += 1
                    cum_pnl += pnl
                    day_trade_count += 1  # v0.8.1.9.0: increment day-level trade counter when trade finalizes
                    position = None
                elif pos_bar.l <= sl:  # v0.8.1.7.0: use pos_bar for SL check
                    pnl = (sl - entry) * qty
                    # v0.8.1.7.1: Enforce SL outcome invariant (SL must never make money)
                    outcome = "ERR_SL_POS_PNL" if pnl > 0 else "SL"  # v0.8.1.7.1
                    if outcome == "ERR_SL_POS_PNL":  # v0.8.1.7.1
                        log.warning(f"[WHY] v0.8.1.7.1 OUTCOME_PNL_MISMATCH SL_POS_PNL symbol={sym} entry={entry} tp={tp} sl={sl} qty={qty} pnl={pnl}")  # v0.8.1.7.1
                    trades.append((sym, outcome, pnl))  # v0.8.1.7.1
                    
                    # v0.8.1.20.0: Console TRADE CARD output (observability only, ASCII-only)
                    entry_time_val = position.get('entry_time_iso', 'N/A')
                    entry_idx = position.get('i', None)
                    hold_bars = (i - entry_idx) if entry_idx is not None else None
                    # v0.8.1.20.0: Compute hold_minutes from HH:MM timestamps
                    exit_ts = pos_bar.ts if hasattr(pos_bar, 'ts') else None
                    entry_m = _hhmm_to_minutes(entry_time_val)
                    exit_m = _hhmm_to_minutes(exit_ts)
                    hold_minutes = (exit_m - entry_m) if (entry_m is not None and exit_m is not None) else None
                    bar_details_str = f"bar_low={pos_bar.l:.2f}, stop={sl:.2f} => breached" if hasattr(pos_bar, 'l') else "N/A"
                    _print_trade_card_exit(
                        sym=sym,
                        date_str=date_str,
                        scenario=scenario_name or scn or "UNKNOWN",
                        entry_time=entry_time_val,
                        exit_time=pos_bar.ts if hasattr(pos_bar, 'ts') else f"bar_{i}",
                        entry_price=entry,
                        exit_price=sl,
                        tp=tp,
                        sl=sl,
                        qty=qty,
                        pnl=pnl,
                        outcome=outcome,
                        telemetry=telemetry,
                        hold_minutes=hold_minutes,  # v0.8.1.20.0
                        hold_bars=hold_bars,
                        exit_reason="Stop loss hit",
                        bar_details=bar_details_str,
                    )
                    
                    # v0.8.1.17.0: Trigger marginal stop-after-1-loss policy
                    if is_marginal_day and marginal_stop1loss_enabled and outcome in {"SL", "ERR_SL_POS_PNL"} and not marginal_sl_seen:  # v0.8.1.17.0
                        marginal_sl_seen = True  # v0.8.1.17.0
                        if not marginal_stop_trigger_logged:  # v0.8.1.17.0
                            log.warning("[WHY] v0.8.1.17.0 MARGINAL_STOP_AFTER_1_LOSS_TRIGGERED date=%s symbol=%s pnl=%.2f day_trade_count=%d",
                                        date_str, sym, pnl, day_trade_count)  # v0.8.1.17.0
                            marginal_stop_trigger_logged = True  # v0.8.1.17.0

                    # v0.8.1.0.0: TWCS exit snapshot hook for stop-loss (non-blocking)
                    if twcs_enabled:
                        try:
                            raw_trade_id = position.get("trade_id") if isinstance(position, dict) else None
                            entry_time_iso = position.get("entry_time_iso") if isinstance(position, dict) else None
                            exit_time_iso = pos_bar.ts  # v0.8.1.7.0: use pos_bar for exit time
                            
                            # v0.8.1.0.1: Ensure a stable TWCS trade_id for exit snapshots.
                            if raw_trade_id:
                                trade_id_for_twcs = str(raw_trade_id)
                            else:
                                trade_id_for_twcs = f"{sym}_{date_str}_{exit_time_iso.replace(':', '')}"

                            mfe_value = None
                            mae_value = None
                            pnl_raw = pnl
                            gross_entry_val = qty * entry if entry else 0.0
                            pnl_pct = (pnl / gross_entry_val * 100.0) if gross_entry_val else None
                            outcome_label = outcome  # v0.8.1.7.1: use exact outcome (SL or ERR_SL_POS_PNL)

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
                    day_trade_count += 1  # v0.8.1.9.0: increment day-level trade counter when trade finalizes
                    position = None
        
        # v0.8.1.21.0: Accumulate per-symbol telemetry for REGIME_SUMMARY (observability only)
        day_struct_damage_blocks_total += telemetry.get("count_struct_damage_blocks", 0)  # v0.8.1.21.0
        day_post_damage_weak_reclaim_blocks_total += telemetry.get("count_post_damage_weak_reclaim_blocks", 0)  # v0.8.1.21.0
        day_vwap_ext_blocks_total += telemetry.get("count_vwap_ext_blocks", 0)  # v0.8.1.21.0
        day_marginal_vwap_gate_blocks_total += telemetry.get("count_marginal_vwap_gate_blocks", 0)  # v0.8.1.21.0
        day_post_damage_entry_lockout_blocks_total += telemetry.get("count_post_damage_entry_lockout_blocks", 0)  # v0.8.1.23.0
        day_dup_ts_total += telemetry.get("dup_ts_count", 0)  # v0.8.1.21.0
        day_pos_mgmt_mismatch_symbols += (1 if telemetry.get("pos_mgmt_mismatch_occurred", False) else 0)  # v0.8.1.21.0
        day_missing_1s_symbols += (1 if telemetry.get("missing_1s_csv", False) else 0)  # v0.8.1.21.0

    # v0.8.1.21.0: Emit REGIME_SUMMARY exactly once per day (observability only)
    if not regime_summary_emitted:  # v0.8.1.21.0
        regime_summary_emitted = True  # v0.8.1.21.0
        trades_closed = len(trades)  # v0.8.1.21.0
        tp_count = sum(1 for _, outcome, _ in trades if outcome.startswith("TP") or outcome.startswith("ERR_TP_"))  # v0.8.1.21.0
        sl_count = sum(1 for _, outcome, _ in trades if outcome.startswith("SL") or outcome.startswith("ERR_SL_"))  # v0.8.1.21.0
        winrate = (tp_count / trades_closed) if trades_closed > 0 else 0.0  # v0.8.1.21.0
        
        # v0.8.1.21.0: Compute minutes_since_damage stats (min, median, max)
        if day_minutes_since_damage_at_entry_list:  # v0.8.1.21.0
            sorted_minutes = sorted(day_minutes_since_damage_at_entry_list)  # v0.8.1.21.0
            min_minutes = sorted_minutes[0]  # v0.8.1.21.0
            max_minutes = sorted_minutes[-1]  # v0.8.1.21.0
            n = len(sorted_minutes)  # v0.8.1.21.0
            if n % 2 == 1:  # v0.8.1.21.0
                p50_minutes = sorted_minutes[n // 2]  # v0.8.1.21.0
            else:  # v0.8.1.21.0
                p50_minutes = (sorted_minutes[n // 2 - 1] + sorted_minutes[n // 2]) / 2.0  # v0.8.1.21.0
            minutes_stats = f"count={len(day_minutes_since_damage_at_entry_list)} min={min_minutes} p50={p50_minutes} max={max_minutes}"  # v0.8.1.21.0
        else:  # v0.8.1.21.0
            minutes_stats = "count=0 min=N/A p50=N/A max=N/A"  # v0.8.1.21.0
        
        log.info("="*80)  # v0.8.1.21.0
        log.info(f"REGIME_SUMMARY v0.8.1.21.0 | date={date_str} | scenario={scenario_name or scn or 'UNKNOWN'} | class={day_class}")  # v0.8.1.21.0
        log.info(f"- universe_symbols={universe_symbols}")  # v0.8.1.21.0
        log.info(f"- trades_closed={trades_closed} tp={tp_count} sl={sl_count} winrate={winrate:.2f}")  # v0.8.1.21.0
        log.info(f"- day_pnl_realized={cum_pnl:.2f}")  # v0.8.1.21.0
        log.info(f"- blocks_total: struct_damage={day_struct_damage_blocks_total} post_damage_weak_reclaim={day_post_damage_weak_reclaim_blocks_total} vwap_ext={day_vwap_ext_blocks_total} marginal_vwap_gate={day_marginal_vwap_gate_blocks_total} post_damage_entry_lockout={day_post_damage_entry_lockout_blocks_total} post_damage_heal_entries_allowed={day_post_damage_heal_entries_allowed_total}")  # v0.8.1.21.0 / v0.8.1.23.0 / v0.8.1.24.0
        log.info(f"- minutes_since_damage_at_entry (damage_scan_lookback_bars={REGIME_DAMAGE_LOOKBACK_BARS}): {minutes_stats}")  # v0.8.1.21.0
        log.info(f"- data_quality: dup_ts_total={day_dup_ts_total} pos_mgmt_mismatch_symbols={day_pos_mgmt_mismatch_symbols} missing_1s_symbols={day_missing_1s_symbols}")  # v0.8.1.21.0
        log.info("="*80)  # v0.8.1.21.0

    # Write results csv
    out_csv = os.path.join(out_dir, f"results_{date_str}.csv")
    with open(out_csv, "w", newline="") as f:
        f.write("symbol,outcome,pnl\n")
        for sym, outcome, pnl in trades:
            f.write(f"{sym},{outcome},{pnl:.2f}\n")
    return out_csv