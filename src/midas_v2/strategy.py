from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import math
import csv  # v0.8.1.0.8
import logging  # v0.8.1.0.8
from pathlib import Path  # v0.8.1.0.8
from datetime import datetime, date, time  # v0.8.1.0.8

logger = logging.getLogger(__name__)  # v0.8.1.0.8

# v0.4.8: Sidecar-driven feature hook (generic, OFF by default)
# This v0.4.8 update adds a minimal import and a tiny guarded call into the external
# micro plug-in. Behavior is unchanged unless config/features/micro.json enables it.  # v0.4.8
from midas_v2.features.micro_feature import should_block_entry  # v0.4.8

# v0.7.9.7.6: config unification – import scenario params loader for strategy config.
from midas_v2.config_models import load_scenario_params


@dataclass
class StrategyParams:
    """
    Configuration parameters for the breakout trading strategy.
    
    This class encapsulates all tunable parameters that control entry conditions,
    exit levels, and various confirmation filters for the trading strategy.
    """
    
    # Basic entry timing and risk management
    gate_minutes: int = 5  # Minimum number of minutes after market open before allowing entries
    tp_pct: float = 1.2    # Take profit percentage above entry price
    sl_pct: float = 2.7    # Stop loss percentage below entry price
    
    # Confirmation indicators (boolean toggles)
    vwap_confirm: bool = False  # Require VWAP confirmation for entry
    ema_confirm: bool = True    # Require EMA confirmation for entry
    macd_confirm: bool = False  # Legacy boolean MACD confirmation (for dip reclaim mode)
    
    # Price action requirements
    rise_bars: int = 2              # Number of consecutive rising price bars required
    green_body_min: float = 0.0     # Minimum real-body fraction per bar (0 = no filter)
    
    # Pre-market filters (optional)
    min_pm_vol: Optional[int] = None    # Minimum pre-market volume required
    reclaim_pmh: Optional[bool] = None  # Require reclaim of pre-market high
    
    # ========== Dip Reclaim Strategy Parameters ==========
    dip_reclaim: bool = False      # Enable dip-and-reclaim entry mode (alternative to basic breakout)
    reclaim_ref: str = "ema"       # Reference for reclaim check: "ema" or "vwap"
    min_dip_pct: float = 2.0       # Minimum percentage dip from swing high required
    min_reclaim_pct: float = 0.5   # Percentage above reference (EMA/VWAP) required to confirm reclaim
    ema_period: int = 5            # EMA period when using EMA as reclaim reference
    reclaim_buffer_bps: float = 0.0      # Extra buffer above reference in basis points (e.g., 5.0 = +0.05%)
    vwap_slope_bps: Optional[int] = None # Require VWAP slope >= this value in bps (optional filter)
    vwap_period_min: int = 1             # Minimum VWAP period (guard; VWAP is cumulative)
    
    # ========== Opening Relative Volume Filter (v0.3.21) ==========
    min_rvol_open: Optional[float] = None   # Minimum opening RVOL (e.g., 1.5 = 150% of yesterday's pace)
    rvol_open_minutes: int = 15             # Number of minutes to compare for RVOL calculation
    
    # ========== MACD Rising Filter (v0.4.x) ==========
    require_macd_rise: bool = False         # Enable explicit MACD histogram rising requirement
    macd_rise_bars: int = 0                 # Number of consecutive rising MACD histogram bars required
    
    # ========== Microstructure Expansion Gate (v0.8.1.0.8) ==========  # v0.8.1.0.8
    micro_expansion_gate: bool = False      # Enable microstructure expansion gate (Scenario B only)  # v0.8.1.0.8
    micro_expansion_window_s: int = 30      # Window size in seconds for microstructure analysis  # v0.8.1.0.8
    micro_expansion_breakout_bps: int = 10  # Breakout threshold above prior high in basis points  # v0.8.1.0.8
    
    # ========== Microstructure Pressure Gate (v0.8.1.0.9) ==========  # v0.8.1.0.9
    micro_pressure_gate: bool = False       # Enable rising 1s pressure gate (Definition B)  # v0.8.1.0.9
    micro_pressure_window_s: int = 20       # Window size in seconds for pressure analysis  # v0.8.1.0.9
    micro_pressure_min_rising: int = 3      # Minimum consecutive higher highs required  # v0.8.1.0.9
    
    # ========== VWAP Extension Gate (v0.8.1.1.0) ==========  # v0.8.1.1.0
    vwap_extension_gate: bool = False       # Enable VWAP over-extension filter  # v0.8.1.1.0
    vwap_extension_max_pct: float = 1.5     # Max allowed distance from VWAP in percentage  # v0.8.1.1.0
    
    # ========== Marginal Day Policy (v0.8.1.17.0) ==========  # v0.8.1.17.0
    marginal_stop_after_1_loss: bool = False  # Stop all entries after first SL on marginal days  # v0.8.1.17.0


# v0.7.9.7.6: config unification – factory to create StrategyParams with scenario-aware defaults.
def create_strategy_params(scenario_name: Optional[str] = None, **override_kwargs) -> StrategyParams:
    """
    Factory function to create StrategyParams with optional scenario-backed defaults.
    
    When scenario_name is provided, loads strategy parameters from scenarios.json
    (via load_scenario_params helper) and uses them as defaults. Any fields not
    provided in the scenario fall back to StrategyParams dataclass defaults.
    Override kwargs always take precedence over scenario values.
    
    Args:
        scenario_name: Name of scenario (e.g., 'B') to load params from JSON
        **override_kwargs: Explicit overrides that take precedence over scenario/defaults
    
    Returns:
        A configured StrategyParams instance with scenario-aware values.
    
    Example:
        # Load Scenario B params from JSON, use those as base, then override tp_pct if provided
        params = create_strategy_params(scenario_name="B", tp_pct=2.5)
    """
    # v0.7.9.7.6: load scenario params for strategy config.
    scenario_params = None
    if scenario_name:
        try:
            scenario_params = load_scenario_params(scenario_name)
        except Exception:
            scenario_params = None  # fail safe: fall back to defaults if something goes wrong
    
    def _get_strategy_param(name: str, default: Any) -> Any:
        """
        v0.7.9.7.6: Resolve a strategy parameter from scenario params (if available),
        otherwise return the provided default value.
        """
        if scenario_params is None:
            return default
        # Support dict-style access (Scenario.params is a dict)
        if isinstance(scenario_params, dict) and name in scenario_params:
            return scenario_params[name]
        return default
    
    # v0.7.9.7.6: build param dict from scenario or defaults; override_kwargs always win.
    param_dict = {
        # Basic entry timing and risk management
        "gate_minutes": _get_strategy_param("gate_minutes", 5),
        "tp_pct": _get_strategy_param("tp_pct", 1.2),
        "sl_pct": _get_strategy_param("sl_pct", 2.7),
        
        # Confirmation indicators
        "vwap_confirm": _get_strategy_param("vwap_confirm", False),
        "ema_confirm": _get_strategy_param("ema_confirm", True),
        "macd_confirm": _get_strategy_param("macd_confirm", False),
        
        # Price action requirements
        "rise_bars": _get_strategy_param("rise_bars", 2),
        "green_body_min": _get_strategy_param("green_body_min", 0.0),
        
        # Pre-market filters
        "min_pm_vol": _get_strategy_param("min_pm_vol", None),
        "reclaim_pmh": _get_strategy_param("reclaim_pmh", None),
        
        # Dip Reclaim Strategy Parameters
        "dip_reclaim": _get_strategy_param("dip_reclaim", False),
        "reclaim_ref": _get_strategy_param("reclaim_ref", "ema"),
        "min_dip_pct": _get_strategy_param("min_dip_pct", 2.0),
        "min_reclaim_pct": _get_strategy_param("min_reclaim_pct", 0.5),
        "ema_period": _get_strategy_param("ema_period", 5),
        "reclaim_buffer_bps": _get_strategy_param("reclaim_buffer_bps", 0.0),
        "vwap_slope_bps": _get_strategy_param("vwap_slope_bps", None),
        "vwap_period_min": _get_strategy_param("vwap_period_min", 1),
        
        # Opening Relative Volume Filter
        "min_rvol_open": _get_strategy_param("min_rvol_open", None),
        "rvol_open_minutes": _get_strategy_param("rvol_open_minutes", 15),
        
        # MACD Rising Filter
        "require_macd_rise": _get_strategy_param("require_macd_rise", False),
        "macd_rise_bars": _get_strategy_param("macd_rise_bars", 0),
        
        # Microstructure Expansion Gate (v0.8.1.0.8)  # v0.8.1.0.8
        "micro_expansion_gate": _get_strategy_param("micro_expansion_gate", False),  # v0.8.1.0.8
        "micro_expansion_window_s": _get_strategy_param("micro_expansion_window_s", 30),  # v0.8.1.0.8
        "micro_expansion_breakout_bps": _get_strategy_param("micro_expansion_breakout_bps", 10),  # v0.8.1.0.8
        
        # Microstructure Pressure Gate (v0.8.1.0.9)  # v0.8.1.0.9
        "micro_pressure_gate": _get_strategy_param("micro_pressure_gate", False),  # v0.8.1.0.9
        "micro_pressure_window_s": _get_strategy_param("micro_pressure_window_s", 20),  # v0.8.1.0.9
        "micro_pressure_min_rising": _get_strategy_param("micro_pressure_min_rising", 3),  # v0.8.1.0.9
        
        # VWAP Extension Gate (v0.8.1.1.0)  # v0.8.1.1.0
        "vwap_extension_gate": _get_strategy_param("vwap_extension_gate", False),  # v0.8.1.1.0
        "vwap_extension_max_pct": _get_strategy_param("vwap_extension_max_pct", 1.5),  # v0.8.1.1.0
        
        # Marginal Day Policy (v0.8.1.17.0)  # v0.8.1.17.0
        "marginal_stop_after_1_loss": _get_strategy_param("marginal_stop_after_1_loss", False),  # v0.8.1.17.0
    }
    
    # Apply any explicit overrides (these always win)
    param_dict.update(override_kwargs)
    
    return StrategyParams(**param_dict)


class Bar:
    """
    Represents a single price bar (candlestick) with OHLCV data.
    
    Attributes:
        t: Timestamp
        o: Open price
        h: High price
        l: Low price
        c: Close price
        v: Volume
    """
    def __init__(self, t, o, h, l, c, v):
        self.t = t  # Time
        self.o = o  # Open
        self.h = h  # High
        self.l = l  # Low
        self.c = c  # Close
        self.v = v  # Volume


def ema(series: List[float], period: int) -> List[Optional[float]]:
    """
    Calculate Exponential Moving Average (EMA) for a price series.
    
    The EMA gives more weight to recent prices and responds faster to price changes
    than a simple moving average.
    
    Args:
        series: List of prices (typically closing prices)
        period: Number of periods for the EMA calculation
    
    Returns:
        List of EMA values (same length as input series). Early values may be None
        until enough data is available for proper EMA calculation.
    
    Notes:
        - Uses standard EMA smoothing constant: k = 2/(period+1)
        - Seeds the EMA with a simple average once enough data is available
        - For period <= 1, returns the original series as floats
    """
    # Special case: no smoothing needed
    if period <= 1:
        return [float(x) for x in series]
    
    out: List[Optional[float]] = [None] * len(series)
    k = 2.0 / (period + 1.0)  # EMA smoothing constant
    val: Optional[float] = None
    
    for i, x in enumerate(series):
        if val is None:
            # Seed the EMA with a simple moving average once we have enough data
            if i + 1 >= period:
                seed = sum(series[i + 1 - period : i + 1]) / float(period)
                val = seed
            else:
                # Not enough data yet; use current price
                val = x
        else:
            # Apply EMA formula: EMA = (Price - PrevEMA) * k + PrevEMA
            val = (x - val) * k + val
        out[i] = val
    
    return out


def macd(series: List[float], fast=12, slow=26, signal=9):
    """
    Calculate MACD (Moving Average Convergence Divergence) indicator.
    
    MACD is a trend-following momentum indicator that shows the relationship between
    two moving averages of prices. It consists of:
    - MACD Line: Difference between fast and slow EMAs
    - Signal Line: EMA of the MACD line
    - Histogram: Difference between MACD line and signal line
    
    Args:
        series: List of prices (typically closing prices)
        fast: Period for fast EMA (default 12)
        slow: Period for slow EMA (default 26)
        signal: Period for signal line EMA (default 9)
    
    Returns:
        Tuple of (macd_line, signal_line, histogram) - all lists of Optional[float]
    
    Notes:
        - Positive histogram suggests bullish momentum
        - Rising histogram suggests strengthening momentum
        - MACD line crossing above signal line is a bullish signal
    """
    # Ensure slow > fast
    if slow < fast:
        fast, slow = slow, fast
    
    # Calculate fast and slow EMAs
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    
    # Calculate MACD line (difference between fast and slow EMAs)
    macd_line: List[Optional[float]] = [None] * len(series)
    for i in range(len(series)):
        if ema_fast[i] is None or ema_slow[i] is None:
            macd_line[i] = None
        else:
            macd_line[i] = float(ema_fast[i]) - float(ema_slow[i])
    
    # Calculate signal line (EMA of MACD line)
    signal_line = ema([x if x is not None else 0.0 for x in macd_line], signal)
    
    # Calculate histogram (difference between MACD line and signal line)
    hist: List[Optional[float]] = [None] * len(series)
    for i in range(len(series)):
        if macd_line[i] is None or signal_line[i] is None:
            hist[i] = None
        else:
            hist[i] = float(macd_line[i]) - float(signal_line[i])
    
    return macd_line, signal_line, hist


class SimpleBreakoutStrategy:
    """
    A configurable breakout trading strategy with multiple entry modes and filters.
    
    This strategy supports two main entry modes:
    1. Basic Breakout: Requires consecutive rising green bars with optional confirmations
    2. Dip Reclaim: Looks for a dip below a reference (EMA/VWAP) followed by a reclaim
    
    The strategy includes various filters and confirmations:
    - Time-based gate (wait X minutes after open)
    - Opening relative volume filter
    - MACD rising momentum filter
    - Price action filters (green body size, consecutive rises)
    - Technical indicator confirmations (EMA, VWAP, MACD)
    """
    
    def __init__(self, params: StrategyParams):
        """
        Initialize the strategy with given parameters.
        
        Args:
            params: StrategyParams object containing all strategy configuration
        """
        self.p = params
        self._yday_bars: Optional[List[Bar]] = None  # Store yesterday's bars for RVOL calculation
        self._gate_debug_count: Dict[str, int] = {}  # v0.8.1.0.8 TEMP: track bar_time debug logs per symbol

    def set_yesterday_bars(self, bars: Optional[List[Bar]]) -> None:
        """
        Provide yesterday's intraday bars for relative volume calculations.
        
        Args:
            bars: List of bars from the previous trading day
        """
        self._yday_bars = bars

    def targets(self, entry: float):
        """
        Calculate take profit and stop loss levels based on entry price.
        
        Args:
            entry: Entry price
        
        Returns:
            Tuple of (take_profit_price, stop_loss_price)
        """
        tp = entry * (1.0 + self.p.tp_pct / 100.0)  # Calculate TP price
        sl = entry * (1.0 - self.p.sl_pct / 100.0)  # Calculate SL price
        return tp, sl

    def _opening_rvol_ok(self, today: List[Bar], yesterday: Optional[List[Bar]], 
                         minutes: int, thresh: float) -> bool:
        """
        Check if opening relative volume meets the minimum threshold.
        
        Relative volume (RVOL) compares today's volume pace to yesterday's at the same
        time. An RVOL of 1.5 means today is trading at 150% of yesterday's volume pace.
        
        Args:
            today: List of today's bars
            yesterday: List of yesterday's bars (optional)
            minutes: Number of minutes to compare
            thresh: Minimum RVOL threshold (e.g., 1.5)
        
        Returns:
            True if RVOL meets threshold or if data is unavailable (fail-open)
        """
        # Fail-open if we don't have yesterday's data
        if yesterday is None or not today:
            return True
        
        # Compare the first N minutes
        n = min(minutes, len(today), len(yesterday))
        if n <= 0:
            return True
        
        # Sum volume for the first N bars
        vol_today = sum(b.v for b in today[:n]) or 0
        vol_yday  = sum(b.v for b in yesterday[:n]) or 1  # Avoid division by zero
        
        # Calculate relative volume
        rvol = vol_today / vol_yday
        return rvol >= thresh

    def _vwap_series(self, bars: List[Bar]) -> List[Optional[float]]:
        """
        Calculate cumulative Volume Weighted Average Price (VWAP) for each bar.
        
        VWAP is the average price weighted by volume and is calculated cumulatively
        throughout the day. It's commonly used as a benchmark for execution quality
        and as a dynamic support/resistance level.
        
        Args:
            bars: List of price bars
        
        Returns:
            List of VWAP values (one per bar)
        
        Formula:
            VWAP = Cumulative(Typical Price × Volume) / Cumulative(Volume)
            Typical Price = (High + Low + Close) / 3
        """
        vwap: List[Optional[float]] = [None] * len(bars)
        pv_cum = 0.0  # Cumulative price × volume
        v_cum = 0.0   # Cumulative volume
        
        for i, b in enumerate(bars):
            # Calculate typical price for this bar
            price = (b.h + b.l + b.c) / 3.0
            
            # Update cumulative values
            pv_cum += price * (b.v or 0.0)
            v_cum  += (b.v or 0.0)
            
            # Calculate VWAP (avoid division by zero)
            vwap[i] = (pv_cum / v_cum) if v_cum > 0 else None
        
        return vwap

    def _vwap_slope_bps(self, vwap: List[Optional[float]], i: int, 
                        lookback: int = 3) -> Optional[float]:
        """
        Calculate the approximate slope of VWAP in basis points.
        
        This helps determine if VWAP is trending upward (positive slope) or
        downward (negative slope), which can confirm trend direction.
        
        Args:
            vwap: List of VWAP values
            i: Current bar index
            lookback: Number of bars to look back for slope calculation
        
        Returns:
            VWAP slope in basis points (100 bps = 1%), or None if insufficient data
        
        Example:
            A slope of 50 bps means VWAP rose 0.5% over the lookback period
        """
        # Need enough data for lookback
        if i < lookback or lookback <= 0:
            return None
        
        # Get VWAP values from lookback bars ago and current bar
        a = vwap[i - lookback]
        b = vwap[i]
        
        # Ensure we have valid data
        if a is None or b is None or a <= 0:
            return None
        
        # Calculate percentage change and convert to basis points
        return ((b - a) / a) * 1e4  # 1e4 converts to basis points

    def _required_price_above_ref(self, ref_val: Optional[float], 
                                   pct: float, bps: float) -> Optional[float]:
        """
        Calculate the required price level above a reference value.
        
        This is used in dip reclaim logic to determine how far above the reference
        (EMA or VWAP) the price must be to consider it a valid reclaim.
        
        Args:
            ref_val: Reference value (e.g., EMA or VWAP)
            pct: Percentage above reference required (e.g., 0.5 for 0.5%)
            bps: Additional buffer in basis points (e.g., 5.0 for +5 bps)
        
        Returns:
            Required price level, or None if ref_val is invalid
        
        Example:
            ref_val=100, pct=0.5, bps=5.0 → 100.55 (0.5% + 5 bps above reference)
        """
        if ref_val is None or ref_val <= 0:
            return None
        
        # Apply percentage requirement
        req = ref_val * (1.0 + (pct / 100.0 if pct else 0.0))
        
        # Apply basis points buffer if specified
        if bps and bps != 0.0:
            req *= (1.0 + bps / 1e4)
        
        return req

    def _passes_price_rise_gate(self, bars: List[Bar], i: int) -> bool:
        """
        Check if the recent price action shows consecutive rising green bars.
        
        This filter ensures we only enter during clear upward momentum, requiring
        each recent bar to close higher than the previous bar. Optionally also
        checks for minimum real body size to filter out doji-like bars.
        
        Args:
            bars: List of all bars
            i: Current bar index
        
        Returns:
            True if price rise requirements are met (or if rise_bars=0)
        """
        # If no rise bars required, pass automatically
        if self.p.rise_bars and self.p.rise_bars > 0:
            # Determine how many bars we can actually look back
            look = min(self.p.rise_bars, i)
            if look <= 0:
                return False
            
            # Check each of the last N bars
            for k in range(look):
                cur = bars[i - k]       # Current bar in the lookback
                prv = bars[i - k - 1]   # Previous bar
                
                # Require current bar closes higher than previous
                if not (cur.c > prv.c):
                    return False
                
                # Optional: check minimum green body size
                if self.p.green_body_min and self.p.green_body_min > 0.0:
                    body = abs(cur.c - cur.o)      # Real body size
                    rng  = max(1e-9, cur.h - cur.l) # Full bar range (avoid div by 0)
                    
                    # Require body to be at least X% of the full range
                    if (body / rng) < self.p.green_body_min:
                        return False
        
        return True

    def _passes_macd_gate(self, closes: List[float], i: int) -> bool:
        """
        Check if MACD histogram shows rising momentum.
        
        When enabled, this requires the MACD histogram to be:
        1. Rising for N consecutive bars
        2. Above zero (positive momentum)
        
        This helps confirm that momentum is not only present but accelerating.
        
        Args:
            closes: List of closing prices
            i: Current bar index
        
        Returns:
            True if MACD requirements are met (or if filter is disabled)
        """
        # If filter is disabled, pass automatically
        if not self.p.require_macd_rise:
            return True
        
        n = int(self.p.macd_rise_bars or 0)
        
        # If no bars required or insufficient data, fail
        if n <= 0 or i < n + 1:
            return False
        
        # Calculate MACD components
        macd_line, signal_line, hist = macd(closes)
        
        # Check that histogram has been rising for N consecutive bars
        # and is currently positive
        for k in range(n):
            h_cur = hist[i - k]       # Current histogram value
            h_prev = hist[i - k - 1]  # Previous histogram value
            
            # Require: rising and positive
            if h_cur is None or h_prev is None or not (h_cur > h_prev and h_cur > 0):
                return False
        
        return True

    def _bar_time(self, bar) -> Any:  # v0.8.1.0.8
        """  # v0.8.1.0.8
        Safely extract timestamp from a Bar object.  # v0.8.1.0.8
        Backtester uses .ts, some contexts may use .t.  # v0.8.1.0.8
        """  # v0.8.1.0.8
        return getattr(bar, "ts", getattr(bar, "t", None))  # v0.8.1.0.8

    def _normalize_target_time(self, target_time: Any, current_bar: Any, date_str: Optional[str] = None) -> Optional[datetime]:  # v0.8.1.0.8
        """  # v0.8.1.0.8
        Normalize target_time to a full datetime object.  # v0.8.1.0.8
          # v0.8.1.0.8
        Handles cases where bar.ts is datetime.time (e.g., 09:58) or HH:MM string.  # v0.8.1.0.8
          # v0.8.1.0.8
        Args:  # v0.8.1.0.8
            target_time: Raw timestamp from bar (datetime, time, or string)  # v0.8.1.0.8
            current_bar: Bar object to extract date if needed  # v0.8.1.0.8
            date_str: Optional YYYY-MM-DD date string for combining with time strings  # v0.8.1.0.8
          # v0.8.1.0.8
        Returns:  # v0.8.1.0.8
            Full datetime object, or None if unparseable  # v0.8.1.0.8
        """  # v0.8.1.0.8
        # Case 1: Already a full datetime  # v0.8.1.0.8
        if isinstance(target_time, datetime):  # v0.8.1.0.8
            return target_time  # v0.8.1.0.8
          # v0.8.1.0.8
        # Case 2: It's a time object (e.g., 09:58) - need to combine with date  # v0.8.1.0.8
        if isinstance(target_time, time):  # v0.8.1.0.8
            # Try to get trading date from multiple sources  # v0.8.1.0.8
            trading_date = None  # v0.8.1.0.8
            # Try provided date_str first  # v0.8.1.0.8
            if date_str:  # v0.8.1.0.8
                try:  # v0.8.1.0.8
                    trading_date = datetime.strptime(date_str, "%Y-%m-%d").date()  # v0.8.1.0.8
                except Exception:  # v0.8.1.0.8
                    pass  # v0.8.1.0.8
            # Try self.date  # v0.8.1.0.8
            if trading_date is None and hasattr(self, "date") and self.date:  # v0.8.1.0.8
                if isinstance(self.date, date):  # v0.8.1.0.8
                    trading_date = self.date  # v0.8.1.0.8
                elif isinstance(self.date, str):  # v0.8.1.0.8
                    try:  # v0.8.1.0.8
                        trading_date = datetime.strptime(self.date, "%Y-%m-%d").date()  # v0.8.1.0.8
                    except Exception:  # v0.8.1.0.8
                        pass  # v0.8.1.0.8
            # Try current_bar.date  # v0.8.1.0.8
            if trading_date is None and hasattr(current_bar, "date") and current_bar.date:  # v0.8.1.0.8
                if isinstance(current_bar.date, date):  # v0.8.1.0.8
                    trading_date = current_bar.date  # v0.8.1.0.8
                elif isinstance(current_bar.date, str):  # v0.8.1.0.8
                    try:  # v0.8.1.0.8
                        trading_date = datetime.strptime(current_bar.date, "%Y-%m-%d").date()  # v0.8.1.0.8
                    except Exception:  # v0.8.1.0.8
                        pass  # v0.8.1.0.8
            # If we found a date, combine it  # v0.8.1.0.8
            if trading_date:  # v0.8.1.0.8
                return datetime.combine(trading_date, target_time)  # v0.8.1.0.8
            return None  # v0.8.1.0.8
          # v0.8.1.0.8
        # Case 3: String - check if it's HH:MM or HH:MM:SS format  # v0.8.1.0.8
        if isinstance(target_time, str):  # v0.8.1.0.8
            # Try to parse as HH:MM or HH:MM:SS if date_str is provided  # v0.8.1.0.8
            if date_str and ":" in target_time and len(target_time) <= 8:  # v0.8.1.0.8
                try:  # v0.8.1.0.8
                    if target_time.count(":") == 1:  # v0.8.1.0.8
                        time_obj = datetime.strptime(target_time, "%H:%M").time()  # v0.8.1.0.8
                    else:  # v0.8.1.0.8
                        time_obj = datetime.strptime(target_time, "%H:%M:%S").time()  # v0.8.1.0.8
                    trading_date = datetime.strptime(date_str, "%Y-%m-%d").date()  # v0.8.1.0.8
                    return datetime.combine(trading_date, time_obj)  # v0.8.1.0.8
                except Exception:  # v0.8.1.0.8
                    pass  # v0.8.1.0.8
            # Try ISO datetime parsing  # v0.8.1.0.8
            return self._parse_iso_dt(target_time)  # v0.8.1.0.8
          # v0.8.1.0.8
        # Case 4: Unknown type  # v0.8.1.0.8
        return None  # v0.8.1.0.8

    def _load_1s_candles(self, symbol: str, target_date: str) -> Optional[List[Dict[str, Any]]]:  # v0.8.1.0.8
        """  # v0.8.1.0.8
        Load 1-second candles from CSV file for microstructure analysis.  # v0.8.1.0.8
        Supports both schemas: (t,o,h,l,c,v) preferred, (timestamp,open,high,low,close,volume) fallback.  # v0.8.1.0.8
          # v0.8.1.0.8
        Args:  # v0.8.1.0.8
            symbol: Stock symbol  # v0.8.1.0.8
            target_date: Date string in YYYY-MM-DD format  # v0.8.1.0.8
          # v0.8.1.0.8
        Returns:  # v0.8.1.0.8
            List of candle dicts with keys: timestamp (str), high (float), close (float)  # v0.8.1.0.8
            Returns None if file missing/unparseable (fail closed)  # v0.8.1.0.8
        """  # v0.8.1.0.8
        try:  # v0.8.1.0.8
            csv_path = Path(f"data/samples/sample_1s_{target_date}_{symbol}.csv")  # v0.8.1.0.8
            if not csv_path.exists():  # v0.8.1.0.8
                return None  # v0.8.1.0.8
            candles = []  # v0.8.1.0.8
            with open(csv_path, "r") as f:  # v0.8.1.0.8
                reader = csv.DictReader(f)  # v0.8.1.0.8
                for row in reader:  # v0.8.1.0.8
                    # Detect schema and normalize  # v0.8.1.0.8
                    if "t" in row:  # v0.8.1.0.8
                        # Preferred schema: t,o,h,l,c,v  # v0.8.1.0.8
                        if "h" not in row or "c" not in row:  # v0.8.1.0.8
                            return None  # v0.8.1.0.8
                        candles.append({  # v0.8.1.0.8
                            "timestamp": row["t"],  # v0.8.1.0.8
                            "high": float(row["h"]),  # v0.8.1.0.8
                            "close": float(row["c"])  # v0.8.1.0.8
                        })  # v0.8.1.0.8
                    elif "timestamp" in row:  # v0.8.1.0.8
                        # Fallback schema: timestamp,open,high,low,close,volume  # v0.8.1.0.8
                        if "high" not in row or "close" not in row:  # v0.8.1.0.8
                            return None  # v0.8.1.0.8
                        candles.append({  # v0.8.1.0.8
                            "timestamp": row["timestamp"],  # v0.8.1.0.8
                            "high": float(row["high"]),  # v0.8.1.0.8
                            "close": float(row["close"])  # v0.8.1.0.8
                        })  # v0.8.1.0.8
                    else:  # v0.8.1.0.8
                        # Missing required columns => fail closed  # v0.8.1.0.8
                        return None  # v0.8.1.0.8
            return candles  # v0.8.1.0.8
        except Exception:  # v0.8.1.0.8
            return None  # v0.8.1.0.8

    def _parse_iso_dt(self, ts_str: str) -> Optional[datetime]:  # v0.8.1.0.8
        """  # v0.8.1.0.8
        Parse ISO timestamp string to datetime object.  # v0.8.1.0.8
          # v0.8.1.0.8
        Supports both 'YYYY-MM-DD HH:MM:SS' and 'YYYY-MM-DDTHH:MM:SS' formats.  # v0.8.1.0.8
          # v0.8.1.0.8
        Args:  # v0.8.1.0.8
            ts_str: Timestamp string  # v0.8.1.0.8
          # v0.8.1.0.8
        Returns:  # v0.8.1.0.8
            datetime object or None if unparseable  # v0.8.1.0.8
        """  # v0.8.1.0.8
        try:  # v0.8.1.0.8
            if "T" in ts_str:  # v0.8.1.0.8
                return datetime.fromisoformat(ts_str.replace("Z", ""))  # v0.8.1.0.8
            else:  # v0.8.1.0.8
                return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")  # v0.8.1.0.8
        except Exception:  # v0.8.1.0.8
            return None  # v0.8.1.0.8

    def _micro_expansion_ok(self, bars: List[Bar], i: int) -> bool:  # v0.8.1.0.8
        """  # v0.8.1.0.8
        Microstructure Expansion Gate (Definition A) - v0.8.1.0.8  # v0.8.1.0.8
          # v0.8.1.0.8
        Analyzes 1-second candles in window [T-30s, T) to verify breakout+hold pattern.  # v0.8.1.0.8
          # v0.8.1.0.8
        Logic:  # v0.8.1.0.8
        1. prior_high = max(high) in window  # v0.8.1.0.8
        2. breakout_level = prior_high * (1 + 10/10000)  # v0.8.1.0.8
        3. Pass iff: (any high >= breakout_level) AND (last_close >= breakout_level)  # v0.8.1.0.8
        4. Missing/empty/unparseable data => FAIL CLOSED (block entry)  # v0.8.1.0.8
          # v0.8.1.0.8
        Args:  # v0.8.1.0.8
            bars: List of 1-minute bars  # v0.8.1.0.8
            i: Current bar index  # v0.8.1.0.8
          # v0.8.1.0.8
        Returns:  # v0.8.1.0.8
            True if microstructure shows valid expansion, False otherwise  # v0.8.1.0.8
        """  # v0.8.1.0.8
        try:  # v0.8.1.0.8
            current_bar = bars[i]  # v0.8.1.0.8
            target_time = self._bar_time(current_bar)  # v0.8.1.0.8
            symbol = getattr(self, "symbol", "UNKNOWN")  # v0.8.1.0.8
              # v0.8.1.0.8
            # Infer date_str from 1s CSV filename if target_time is a time-only string  # v0.8.1.0.8
            date_str = None  # v0.8.1.0.8
            if isinstance(target_time, str) and ":" in target_time:  # v0.8.1.0.8
                # Scan data/samples for sample_1s_*_{symbol}.csv files  # v0.8.1.0.8
                samples_dir = Path("data/samples")  # v0.8.1.0.8
                if samples_dir.exists():  # v0.8.1.0.8
                    pattern = f"sample_1s_*_{symbol}.csv"  # v0.8.1.0.8
                    matches = list(samples_dir.glob(pattern))  # v0.8.1.0.8
                    if matches:  # v0.8.1.0.8
                        # Extract YYYY-MM-DD from first match: sample_1s_YYYY-MM-DD_SYMBOL.csv  # v0.8.1.0.8
                        filename = matches[0].name  # v0.8.1.0.8
                        parts = filename.split("_")  # v0.8.1.0.8
                        if len(parts) >= 3:  # v0.8.1.0.8
                            date_str = parts[2]  # v0.8.1.0.8
              # v0.8.1.0.8
            # Normalize target_time to full datetime (handles time-only objects)  # v0.8.1.0.8
            target_dt = self._normalize_target_time(target_time, current_bar, date_str)  # v0.8.1.0.8
            if target_dt is None:  # v0.8.1.0.8
                self._log_gate_block("unparseable_target_time", symbol, target_time, None, None, None, 0)  # v0.8.1.0.8
                return False  # v0.8.1.0.8
              # v0.8.1.0.8
            # Extract date string for CSV filename  # v0.8.1.0.8
            target_date = target_dt.strftime("%Y-%m-%d")  # v0.8.1.0.8
              # v0.8.1.0.8
            # Load 1s candles  # v0.8.1.0.8
            candles = self._load_1s_candles(symbol, target_date)  # v0.8.1.0.8
            if candles is None or len(candles) == 0:  # v0.8.1.0.8
                self._log_gate_block("no_1s_data", symbol, target_time, None, None, None, 0)  # v0.8.1.0.8
                return False  # v0.8.1.0.8
              # v0.8.1.0.8
            # Define window: [T-30s, T)  # v0.8.1.0.8
            window_s = int(self.p.micro_expansion_window_s)  # v0.8.1.0.8
            breakout_bps = int(self.p.micro_expansion_breakout_bps)  # v0.8.1.0.8
              # v0.8.1.0.8
            # Filter candles in window  # v0.8.1.0.8
            window_candles = []  # v0.8.1.0.8
            for c in candles:  # v0.8.1.0.8
                c_dt = self._parse_iso_dt(c["timestamp"])  # v0.8.1.0.8
                if c_dt is None:  # v0.8.1.0.8
                    continue  # v0.8.1.0.8
                delta_s = (target_dt - c_dt).total_seconds()  # v0.8.1.0.8
                if 0 < delta_s <= window_s:  # v0.8.1.0.8
                    window_candles.append(c)  # v0.8.1.0.8
              # v0.8.1.0.8
            if len(window_candles) == 0:  # v0.8.1.0.8
                self._log_gate_block("empty_window", symbol, target_time, None, None, None, 0)  # v0.8.1.0.8
                return False  # v0.8.1.0.8
              # v0.8.1.0.8
            # Calculate prior_high = max(high) in window  # v0.8.1.0.8
            prior_high = max(c["high"] for c in window_candles)  # v0.8.1.0.8
            breakout_level = prior_high * (1.0 + breakout_bps / 10000.0)  # v0.8.1.0.8
              # v0.8.1.0.8
            # Check if any high >= breakout_level  # v0.8.1.0.8
            any_breakout = any(c["high"] >= breakout_level for c in window_candles)  # v0.8.1.0.8
              # v0.8.1.0.8
            # Get last_close: select latest candle from FULL list where candle_time <= T  # v0.8.1.0.8
            # (Definition A: not restricted to window, just needs to be at/before T)  # v0.8.1.0.8
            valid_candles = []  # v0.8.1.0.8
            for c in candles:  # v0.8.1.0.8
                c_dt = self._parse_iso_dt(c["timestamp"])  # v0.8.1.0.8
                if c_dt is not None and c_dt <= target_dt:  # v0.8.1.0.8
                    valid_candles.append((c_dt, c))  # v0.8.1.0.8
            if len(valid_candles) == 0:  # v0.8.1.0.8
                self._log_gate_block("no_valid_candles_at_T", symbol, target_time, prior_high, breakout_level, None, len(window_candles))  # v0.8.1.0.8
                return False  # v0.8.1.0.8
            # Sort by timestamp and take the latest  # v0.8.1.0.8
            valid_candles.sort(key=lambda x: x[0])  # v0.8.1.0.8
            last_close = valid_candles[-1][1]["close"]  # v0.8.1.0.8
              # v0.8.1.0.8
            # Pass iff: any_breakout AND last_close >= breakout_level  # v0.8.1.0.8
            if any_breakout and last_close >= breakout_level:  # v0.8.1.0.8
                return True  # v0.8.1.0.8
            else:  # v0.8.1.0.8
                self._log_gate_block("failed_criteria", symbol, target_time, prior_high, breakout_level, last_close, len(window_candles))  # v0.8.1.0.8
                return False  # v0.8.1.0.8
              # v0.8.1.0.8
        except Exception as e:  # v0.8.1.0.8
            # Fail closed on any exception - ALWAYS log before returning  # v0.8.1.0.8
            symbol_safe = getattr(self, "symbol", "UNKNOWN")  # v0.8.1.0.8
            time_safe = self._bar_time(bars[i]) if i < len(bars) else "n/a"  # v0.8.1.0.8
            exc_type = type(e).__name__  # v0.8.1.0.8
            self._log_gate_block(f"exception:{exc_type}", symbol_safe, time_safe, None, None, None, 0)  # v0.8.1.0.8
            return False  # v0.8.1.0.8

    def _micro_pressure_ok(self, bars: List[Bar], i: int) -> bool:  # v0.8.1.0.9
        """  # v0.8.1.0.9
        Microstructure Pressure Gate (Definition B) - v0.8.1.0.9  # v0.8.1.0.9
          # v0.8.1.0.9
        Analyzes 1-second candles to verify rising pressure (consecutive higher highs).  # v0.8.1.0.9
          # v0.8.1.0.9
        Logic:  # v0.8.1.0.9
        1. Load 1s candles in window [T-window_s, T)  # v0.8.1.0.9
        2. Count max streak of consecutive higher highs  # v0.8.1.0.9
        3. Pass if max_streak >= micro_pressure_min_rising  # v0.8.1.0.9
        4. Missing/empty/insufficient data => FAIL CLOSED (block entry)  # v0.8.1.0.9
          # v0.8.1.0.9
        Args:  # v0.8.1.0.9
            bars: List of 1-minute bars  # v0.8.1.0.9
            i: Current bar index  # v0.8.1.0.9
          # v0.8.1.0.9
        Returns:  # v0.8.1.0.9
            True if rising pressure detected, False otherwise  # v0.8.1.0.9
        """  # v0.8.1.0.9
        try:  # v0.8.1.0.9
            current_bar = bars[i]  # v0.8.1.0.9
            target_time = self._bar_time(current_bar)  # v0.8.1.0.9
            symbol = getattr(self, "symbol", "UNKNOWN")  # v0.8.1.0.9
              # v0.8.1.0.9
            # Infer date_str from 1s CSV filename if needed  # v0.8.1.0.9
            date_str = None  # v0.8.1.0.9
            if isinstance(target_time, str) and ":" in target_time:  # v0.8.1.0.9
                samples_dir = Path("data/samples")  # v0.8.1.0.9
                if samples_dir.exists():  # v0.8.1.0.9
                    pattern = f"sample_1s_*_{symbol}.csv"  # v0.8.1.0.9
                    matches = list(samples_dir.glob(pattern))  # v0.8.1.0.9
                    if matches:  # v0.8.1.0.9
                        filename = matches[0].name  # v0.8.1.0.9
                        parts = filename.split("_")  # v0.8.1.0.9
                        if len(parts) >= 3:  # v0.8.1.0.9
                            date_str = parts[2]  # v0.8.1.0.9
              # v0.8.1.0.9
            # Normalize target_time to full datetime  # v0.8.1.0.9
            target_dt = self._normalize_target_time(target_time, current_bar, date_str)  # v0.8.1.0.9
            if target_dt is None:  # v0.8.1.0.9
                logger.info(f"[WHY] v0.8.1.0.9 MICRO_PRESSURE_GATE: BLOCKED symbol={symbol} time={target_time} reason=unparseable_time")  # v0.8.1.0.9
                return False  # v0.8.1.0.9
              # v0.8.1.0.9
            # Extract date string for CSV filename  # v0.8.1.0.9
            target_date = target_dt.strftime("%Y-%m-%d")  # v0.8.1.0.9
              # v0.8.1.0.9
            # Load 1s candles  # v0.8.1.0.9
            candles = self._load_1s_candles(symbol, target_date)  # v0.8.1.0.9
            if candles is None or len(candles) == 0:  # v0.8.1.0.9
                logger.info(f"[WHY] v0.8.1.0.9 MICRO_PRESSURE_GATE: BLOCKED symbol={symbol} time={target_time} reason=no_1s_data")  # v0.8.1.0.9
                return False  # v0.8.1.0.9
              # v0.8.1.0.9
            # Define window: [T-window_s, T)  # v0.8.1.0.9
            window_s = int(self.p.micro_pressure_window_s)  # v0.8.1.0.9
            min_rising = int(self.p.micro_pressure_min_rising)  # v0.8.1.0.9
              # v0.8.1.0.9
            # Filter candles in window and parse timestamps  # v0.8.1.0.9
            window_candles = []  # v0.8.1.0.9
            for c in candles:  # v0.8.1.0.9
                c_dt = self._parse_iso_dt(c["timestamp"])  # v0.8.1.0.9
                if c_dt is None:  # v0.8.1.0.9
                    continue  # v0.8.1.0.9
                delta_s = (target_dt - c_dt).total_seconds()  # v0.8.1.0.9
                if 0 < delta_s <= window_s:  # v0.8.1.0.9
                    window_candles.append((c_dt, c))  # v0.8.1.0.9
              # v0.8.1.0.9
            # Check if we have enough candles  # v0.8.1.0.9
            if len(window_candles) < (min_rising + 1):  # v0.8.1.0.9
                logger.info(f"[WHY] v0.8.1.0.9 MICRO_PRESSURE_GATE: BLOCKED symbol={symbol} time={target_time} "
                           f"max_streak=0 required={min_rising} reason=insufficient_candles n={len(window_candles)}")  # v0.8.1.0.9
                return False  # v0.8.1.0.9
              # v0.8.1.0.9
            # Sort by timestamp  # v0.8.1.0.9
            window_candles.sort(key=lambda x: x[0])  # v0.8.1.0.9
              # v0.8.1.0.9
            # Count max streak of consecutive higher highs  # v0.8.1.0.9
            max_streak = 0  # v0.8.1.0.9
            current_streak = 0  # v0.8.1.0.9
            for k in range(1, len(window_candles)):  # v0.8.1.0.9
                prev_high = window_candles[k-1][1]["high"]  # v0.8.1.0.9
                curr_high = window_candles[k][1]["high"]  # v0.8.1.0.9
                if curr_high > prev_high:  # v0.8.1.0.9
                    current_streak += 1  # v0.8.1.0.9
                    max_streak = max(max_streak, current_streak)  # v0.8.1.0.9
                else:  # v0.8.1.0.9
                    current_streak = 0  # v0.8.1.0.9
              # v0.8.1.0.9
            # Pass if max_streak >= min_rising  # v0.8.1.0.9
            if max_streak >= min_rising:  # v0.8.1.0.9
                return True  # v0.8.1.0.9
            else:  # v0.8.1.0.9
                logger.info(f"[WHY] v0.8.1.0.9 MICRO_PRESSURE_GATE: BLOCKED symbol={symbol} time={target_time} "
                           f"max_streak={max_streak} required={min_rising}")  # v0.8.1.0.9
                return False  # v0.8.1.0.9
              # v0.8.1.0.9
        except Exception as e:  # v0.8.1.0.9
            # Fail closed on any exception  # v0.8.1.0.9
            symbol_safe = getattr(self, "symbol", "UNKNOWN")  # v0.8.1.0.9
            time_safe = self._bar_time(bars[i]) if i < len(bars) else "n/a"  # v0.8.1.0.9
            exc_type = type(e).__name__  # v0.8.1.0.9
            logger.info(f"[WHY] v0.8.1.0.9 MICRO_PRESSURE_GATE: BLOCKED symbol={symbol_safe} time={time_safe} "
                       f"reason=exception:{exc_type}")  # v0.8.1.0.9
            return False  # v0.8.1.0.9

    def _log_gate_block(self, reason: str, symbol: str, time, prior_high, breakout_level, last_close, n_window: int) -> None:  # v0.8.1.0.8
        """  # v0.8.1.0.8
        Log when microstructure expansion gate blocks entry.  # v0.8.1.0.8
          # v0.8.1.0.8
        Args:  # v0.8.1.0.8
            reason: Why the gate blocked (e.g., 'no_1s_data', 'failed_criteria')  # v0.8.1.0.8
            symbol: Stock symbol  # v0.8.1.0.8
            time: Target timestamp  # v0.8.1.0.8
            prior_high: Max high in window (or None)  # v0.8.1.0.8
            breakout_level: Calculated breakout level (or None)  # v0.8.1.0.8
            last_close: Last close in window (or None)  # v0.8.1.0.8
            n_window: Number of candles in window  # v0.8.1.0.8
        """  # v0.8.1.0.8
        logger.info(f"[WHY] v0.8.1.0.8 MICRO_EXPANSION_GATE: BLOCKED symbol={symbol} time={time} "  # v0.8.1.0.8
                    f"prior_high={prior_high} breakout_level={breakout_level} last_close={last_close} "  # v0.8.1.0.8
                    f"n_window={n_window} reason={reason}")  # v0.8.1.0.8

    def _vwap_extension_ok(self, entry_price: float, vwap: float, max_pct: float):  # v0.8.1.1.0
        """  # v0.8.1.1.0
        VWAP Extension Gate (v0.8.1.1.0)  # v0.8.1.1.0
          # v0.8.1.1.0
        Check if entry price is not over-extended from VWAP.  # v0.8.1.1.0
        Blocks entries that are too far above VWAP (stretched).  # v0.8.1.1.0
          # v0.8.1.1.0
        Args:  # v0.8.1.1.0
            entry_price: The actual price used by strategy for entry decision  # v0.8.1.1.0
            vwap: VWAP value at the entry bar  # v0.8.1.1.0
            max_pct: Maximum allowed distance from VWAP in percentage  # v0.8.1.1.0
          # v0.8.1.1.0
        Returns:  # v0.8.1.1.0
            Tuple: (ok: bool, dist_pct: float | None)  # v0.8.1.1.0
                ok=True if entry is acceptable, False if blocked  # v0.8.1.1.0
                dist_pct=percentage distance from VWAP (None if VWAP invalid)  # v0.8.1.1.0
        """  # v0.8.1.1.0
        # Fail closed if VWAP is missing or invalid  # v0.8.1.1.0
        if vwap is None or vwap <= 0:  # v0.8.1.1.0
            return (False, None)  # v0.8.1.1.0
          # v0.8.1.1.0
        # Calculate distance from VWAP in percentage  # v0.8.1.1.0
        dist_pct = (entry_price - vwap) / vwap * 100.0  # v0.8.1.1.0
          # v0.8.1.1.0
        # If entry is below VWAP, not over-extended (pass)  # v0.8.1.1.0
        if dist_pct <= 0:  # v0.8.1.1.0
            return (True, dist_pct)  # v0.8.1.1.0
          # v0.8.1.1.0
        # Block if over-extended above VWAP  # v0.8.1.1.0
        if dist_pct > max_pct:  # v0.8.1.1.0
            return (False, dist_pct)  # v0.8.1.1.0
          # v0.8.1.1.0
        # Within acceptable range  # v0.8.1.1.0
        return (True, dist_pct)  # v0.8.1.1.0

    def should_enter(self, bars: List[Bar], i: int) -> bool:
        """
        Main entry logic: determine if we should enter a trade at bar i.
        
        This method coordinates all entry filters and confirmation checks.
        It supports two main modes:
        1. Dip Reclaim Mode (if dip_reclaim=True)
        2. Basic Breakout Mode (default)
        
        Args:
            bars: List of all bars up to current time
            i: Index of current bar to evaluate
        
        Returns:
            True if all entry conditions are met
        
        Entry Flow:
        1. Check time-based gate (minimum minutes after open)
        2. Check opening relative volume (if enabled)
        3. Route to appropriate entry mode (dip reclaim vs basic breakout)
        4. Apply mode-specific filters and confirmations
        5. Check plug-in hook (v0.4.8 feature)
        """
        # Gate 1: Minimum time after market open
        # Don't enter until we're past the specified number of minutes
        if i < max(0, int(self.p.gate_minutes)):
            return False

        # Gate 2: Opening RVOL filter (v0.3.21)
        # Ensure today's opening volume is strong relative to yesterday
        if self.p.min_rvol_open is not None and self.p.min_rvol_open > 0:
            if not self._opening_rvol_ok(bars, self._yday_bars, 
                                        int(self.p.rvol_open_minutes), 
                                        float(self.p.min_rvol_open)):
                return False

        # Route to dip reclaim logic if that mode is enabled
        if self.p.dip_reclaim:
            return self._dip_reclaim_should_enter(bars, i)

        # ========== Basic Breakout Mode ==========
        
        # Gate 3: Require consecutive rising green bars
        if not self._passes_price_rise_gate(bars, i):
            return False

        # Gate 4: MACD rising momentum filter (when enabled)
        closes = [b.c for b in bars]
        if not self._passes_macd_gate(closes, i):
            return False

        # Gate 5: Microstructure expansion gate (v0.8.1.0.8, Scenario B only)  # v0.8.1.0.8
        if self.p.micro_expansion_gate:  # v0.8.1.0.8
            symbol = getattr(self, "symbol", "UNKNOWN")  # v0.8.1.0.8
            logger.info(f"[WHY] v0.8.1.0.8 MICRO_EXPANSION_GATE: CHECK symbol={symbol} i={i}")  # v0.8.1.0.8
            # v0.8.1.0.9: removed TEMP BAR_TIME debug logs
            if not self._micro_expansion_ok(bars, i):  # v0.8.1.0.8
                return False  # v0.8.1.0.8

        # Gate 6: Microstructure pressure gate (v0.8.1.0.9, Definition B)  # v0.8.1.0.9
        if self.p.micro_pressure_gate:  # v0.8.1.0.9
            symbol = getattr(self, "symbol", "UNKNOWN")  # v0.8.1.0.9
            target_time = self._bar_time(bars[i])  # v0.8.1.0.9
            logger.info(f"[WHY] v0.8.1.0.9 MICRO_PRESSURE_GATE: CHECK symbol={symbol} time={target_time} "
                       f"window_s={self.p.micro_pressure_window_s} min_rising={self.p.micro_pressure_min_rising}")  # v0.8.1.0.9
            if not self._micro_pressure_ok(bars, i):  # v0.8.1.0.9
                return False  # v0.8.1.0.9

        # Gate 7: VWAP Extension Gate (v0.8.1.1.0)  # v0.8.1.1.0
        if self.p.vwap_extension_gate:  # v0.8.1.1.0
            symbol = getattr(self, "symbol", "UNKNOWN")  # v0.8.1.1.0
            target_time = self._bar_time(bars[i])  # v0.8.1.1.0
            # v0.8.1.1.0: entry_price uses the strategy's actual entry decision price (bar close)  # v0.8.1.1.0
            entry_price = bars[i].c  # v0.8.1.1.0
            vwap_vals = self._vwap_series(bars)  # v0.8.1.1.0
            vwap = vwap_vals[i] if i < len(vwap_vals) else None  # v0.8.1.1.0
            max_pct = self.p.vwap_extension_max_pct  # v0.8.1.1.0
              # v0.8.1.1.0
            ok, dist_pct = self._vwap_extension_ok(entry_price, vwap, max_pct)  # v0.8.1.1.0
              # v0.8.1.1.0
            # Always log CHECK when gate is enabled and VWAP is valid  # v0.8.1.1.0
            if vwap is not None and vwap > 0:  # v0.8.1.1.0
                logger.info(f"[WHY] v0.8.1.1.0 VWAP_EXT: CHECK symbol={symbol} time={target_time} "  # v0.8.1.1.0
                           f"entry_price={entry_price:.4f} vwap={vwap:.4f} dist_pct={dist_pct:.2f} max_pct={max_pct}")  # v0.8.1.1.0
              # v0.8.1.1.0
            # Block if check failed  # v0.8.1.1.0
            if not ok:  # v0.8.1.1.0
                if vwap is None or vwap <= 0:  # v0.8.1.1.0
                    logger.info(f"[WHY] v0.8.1.1.0 VWAP_EXT: BLOCKED symbol={symbol} time={target_time} "  # v0.8.1.1.0
                               f"entry_price={entry_price:.4f} vwap={vwap} dist_pct=NA max_pct={max_pct} reason=missing_vwap")  # v0.8.1.1.0
                else:  # v0.8.1.1.0
                    logger.info(f"[WHY] v0.8.1.1.0 VWAP_EXT: BLOCKED symbol={symbol} time={target_time} "  # v0.8.1.1.0
                               f"entry_price={entry_price:.4f} vwap={vwap:.4f} dist_pct={dist_pct:.2f} max_pct={max_pct} reason=overextended")  # v0.8.1.1.0
                return False  # v0.8.1.1.0

        # Note: Additional confirmations (EMA, VWAP, legacy MACD boolean)
        # would be implemented here in production code
        
        # v0.4.8: External plug-in hook (sidecar-driven; OFF by default)
        # This allows external modules to add custom blocking logic without
        # modifying core strategy code. The try-except ensures fail-open behavior.
        try:
            # Call external function to check if entry should be blocked
            if should_block_entry(getattr(self, "scenario_id", ""), 
                                 getattr(self, "symbol", ""), 
                                 bars[i], self):
                return False  # External module blocked the entry
        except Exception:
            pass  # Fail-open: if plug-in fails, continue with baseline behavior

        # All gates passed
        return True

    def _dip_reclaim_should_enter(self, bars: List[Bar], i: int) -> bool:
        """
        Dip-and-reclaim entry logic: look for price dipping below a reference
        and then reclaiming it.
        
        Strategy:
        1. Find recent swing high
        2. Measure the dip (lowest point since swing high)
        3. Verify the dip is significant enough (min_dip_pct)
        4. Check if price has reclaimed above the reference (EMA or VWAP)
        5. Apply additional confirmations (MACD, rising bars, etc.)
        
        This pattern often indicates strong buyers stepping in at support.
        
        Args:
            bars: List of all bars
            i: Current bar index
        
        Returns:
            True if dip-and-reclaim pattern is confirmed with all filters
        """
        p = self.p
        
        # Need minimum data
        if i < 3:
            return False

        # Step 1: Identify swing high and trough
        closes = [b.c for b in bars]
        lookback = min(20, i)  # Look back up to 20 bars
        
        # Find the highest close in the lookback period (before current bar)
        swing_high = max(closes[i - lookback : i])
        curr_close = closes[i]
        
        # Find the lowest point in recent price action (including current bar)
        recent_segment = closes[i - lookback : i + 1]
        trough = min(recent_segment)
        
        # Step 2: Calculate dip percentage
        if swing_high <= 0:
            return False
        
        dip_pct = (swing_high - trough) / swing_high * 100.0
        
        # Step 3: Verify dip meets minimum threshold
        if dip_pct < p.min_dip_pct:
            return False  # Dip not significant enough

        # Step 4: Check reclaim above reference (EMA or VWAP)
        ref_kind = p.reclaim_ref.lower().strip()
        ref_val: Optional[float] = None
        
        if ref_kind == "ema":
            # Use EMA as reference
            ema_vals = ema(closes, max(2, int(p.ema_period)))
            ref_val = ema_vals[i]
            
        elif ref_kind == "vwap":
            # Use VWAP as reference
            vwap_vals = self._vwap_series(bars)
            ref_val = vwap_vals[i]
            
            # Optional VWAP slope filter: require upward-sloping VWAP
            if p.vwap_slope_bps is not None:
                slope = self._vwap_slope_bps(vwap_vals, i, lookback=3)
                if slope is None or slope < float(p.vwap_slope_bps):
                    return False  # VWAP not sloping up enough
        else:
            return False  # Invalid reference type

        # Calculate required price for reclaim (reference + pct + bps buffer)
        req_price = self._required_price_above_ref(ref_val, p.min_reclaim_pct, 
                                                   p.reclaim_buffer_bps)
        
        # Verify price has reclaimed above the reference
        if req_price is None or curr_close < req_price:
            return False  # Not above required reclaim level

        # Step 5: MACD confirmation (if enabled for dip reclaim)
        if p.macd_confirm:
            macd_line, signal_line, hist = macd(closes)
            
            # Require all MACD values to be available
            if macd_line[i] is None or signal_line[i] is None or hist[i] is None:
                return False
            
            # Require MACD line above signal line (bullish crossover)
            if not (macd_line[i] > signal_line[i]):
                return False
            
            # Require histogram to be rising (increasing momentum)
            if hist[i] <= (hist[i - 1] if hist[i - 1] is not None else -1e9):
                return False

        # Step 6: Price rise confirmation (consecutive green bars)
        if p.rise_bars and p.rise_bars > 0:
            look = min(p.rise_bars, i)
            
            for k in range(look):
                # Require consecutive rising closes
                if not (bars[i - k].c >= bars[i - k - 1].c):
                    return False
                
                # Optional: check minimum green body size
                if self.p.green_body_min and self.p.green_body_min > 0.0:
                    cur = bars[i - k]
                    body = abs(cur.c - cur.o)
                    rng  = max(1e-9, cur.h - cur.l)
                    if (body / rng) < self.p.green_body_min:
                        return False

        # Step 7: MACD rising gate (when enabled)
        # Also honor the explicit MACD rising requirement if configured
        if not self._passes_macd_gate(closes, i):
            return False

        # All dip-reclaim conditions met
        return True
