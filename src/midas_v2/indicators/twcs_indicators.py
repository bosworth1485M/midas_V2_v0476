"""
TWCS Phase 2 Part 2 – Indicators Module (v0.8.1.0.2)

This module provides indicator computation helpers for TWCS (Trade Window Capture System).
These are observational/read-only and do not affect trading logic, signals, or PnL.

Current version implements:
- green_streak: consecutive green candles leading up to entry/exit
- vwap: volume-weighted average price up to entry/exit
- vwap_slope_bps: simple VWAP slope approximation (last few minutes)
- macd_hist: MACD histogram at entry/exit
- macd_slope: short-window MACD slope (raw difference)
- rvol_open: relative volume at open (when available from strategy_state)
"""
# v0.8.1.0.2: TWCS indicators module

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List
import sys


def build_twcs_indicators(
    symbol: str,
    date_str: str,
    when: datetime,
    candles_1m: List[Dict[str, Any]],
    strategy_state: Any | None = None,
) -> Dict[str, Any]:
    """
    Build TWCS indicator snapshot for a given moment in time.
    
    This implementation computes green_streak, vwap, vwap_slope_bps, macd_hist,
    macd_slope, and rvol_open (v0.8.1.0.2).
    
    Args:
        symbol: Ticker symbol (e.g. "MWYN")
        date_str: Date in "YYYY-MM-DD" format
        when: The moment in time for which to compute indicators (entry or exit time)
        candles_1m: List of 1-minute candle dicts from TWCS window loader
        strategy_state: Optional strategy state object (for accessing computed indicators)
    
    Returns:
        Dict containing indicator values:
        {
            "green_streak": int,          # consecutive green candles leading up to 'when'
            "vwap": float | None,          # volume-weighted average price up to 'when'
            "vwap_slope_bps": float,       # VWAP slope approximation in basis points
            "macd_hist": float | None,     # MACD histogram at 'when'
            "macd_slope": float,           # short-window MACD slope (raw difference)
            "rvol_open": float | None,     # relative volume at open (if available)
        }
    
    Notes:
        - This is read-only and observational; never affects trading logic
        - Returns minimal indicators on any error (defensive)
        - Version: v0.8.1.0.2
    """
    # v0.8.1.0.2: TWCS indicators (green_streak + vwap + vwap_slope_bps + macd_hist + macd_slope + rvol_open)
    
    indicators: Dict[str, Any] = {}
    
    # Compute green_streak
    try:
        green_streak = _compute_green_streak(candles_1m, when)
        indicators["green_streak"] = green_streak
    except Exception as exc:
        print(
            f"[WARN] v0.8.1.0.2: failed to compute green_streak for {symbol} on {date_str}: {exc}",
            file=sys.stderr
        )
        indicators["green_streak"] = 0
    
    # Compute vwap
    try:
        vwap = _compute_vwap(candles_1m, when)
        indicators["vwap"] = vwap
    except Exception as exc:
        print(
            f"[WARN] v0.8.1.0.2: failed to compute vwap for {symbol} on {date_str}: {exc}",
            file=sys.stderr
        )
        indicators["vwap"] = None
    
    # Compute vwap_slope_bps
    try:
        vwap_slope_bps = _compute_vwap_slope_bps(candles_1m, when)
        indicators["vwap_slope_bps"] = vwap_slope_bps
    except Exception as exc:
        print(
            f"[WARN] v0.8.1.0.2: failed to compute vwap_slope_bps for {symbol} on {date_str}: {exc}",
            file=sys.stderr
        )
        indicators["vwap_slope_bps"] = 0.0
    
    # Compute macd_hist
    try:
        macd_hist = _compute_macd_hist(candles_1m, when)
        indicators["macd_hist"] = macd_hist
    except Exception as exc:
        print(
            f"[WARN] v0.8.1.0.2: failed to compute macd_hist for {symbol} on {date_str}: {exc}",
            file=sys.stderr
        )
        indicators["macd_hist"] = None
    
    # Compute macd_slope
    try:
        macd_slope = _compute_macd_slope(candles_1m, when)
        indicators["macd_slope"] = macd_slope
    except Exception as exc:
        print(
            f"[WARN] v0.8.1.0.2: failed to compute macd_slope for {symbol} on {date_str}: {exc}",
            file=sys.stderr
        )
        indicators["macd_slope"] = 0.0
    
    # Compute rvol_open (if available in strategy_state)
    try:
        rvol_open = _compute_rvol_open(strategy_state)
        indicators["rvol_open"] = rvol_open
    except Exception as exc:
        print(
            f"[WARN] v0.8.1.0.2: failed to compute rvol_open for {symbol} on {date_str}: {exc}",
            file=sys.stderr
        )
        indicators["rvol_open"] = None
    
    return indicators


def _compute_green_streak(candles_1m: List[Dict[str, Any]], when: datetime) -> int:
    """
    Compute the number of consecutive green candles leading up to 'when'.
    
    Args:
        candles_1m: List of 1-minute candle dicts (sorted ascending by time)
        when: The moment in time to compute the streak up to
    
    Returns:
        Number of consecutive green candles ending at or before 'when'.
        Returns 0 if no candles, no green candles, or latest candle is red.
    
    Notes:
        - Only considers candles with timestamp <= when
        - Counts backwards from the latest qualifying candle
        - Stops at first non-green candle or missing is_green field
    """
    if not candles_1m:
        return 0
    
    # Filter candles that are at or before 'when'
    qualifying_candles = []
    for candle in candles_1m:
        try:
            candle_time = datetime.fromisoformat(candle["t"].replace("Z", ""))
            if candle_time <= when:
                qualifying_candles.append(candle)
        except Exception:
            # Skip candles with bad timestamps
            continue
    
    if not qualifying_candles:
        return 0
    
    # Count consecutive green candles from the end backwards
    streak = 0
    for candle in reversed(qualifying_candles):
        is_green = candle.get("is_green", False)
        if is_green:
            streak += 1
        else:
            # Hit a non-green candle, stop counting
            break
    
    return streak


def _compute_vwap(candles_1m: List[Dict[str, Any]], when: datetime) -> float | None:
    """
    Compute the volume-weighted average price (VWAP) up to 'when'.
    
    Args:
        candles_1m: List of 1-minute candle dicts (sorted ascending by time)
        when: The moment in time to compute VWAP up to
    
    Returns:
        VWAP as a float, or None if no valid candles found.
        
        VWAP = sum(price * volume) / sum(volume)
        
        where price is the close price ("c") and volume is "v".
    
    Notes:
        - Only considers candles with timestamp <= when
        - Skips candles with missing price/volume or volume <= 0
        - Returns None if no valid (price, volume) pairs exist
    """
    if not candles_1m:
        return None
    
    # Filter candles that are at or before 'when' and collect valid (price, vol) pairs
    price_vol_sum = 0.0
    vol_sum = 0.0
    
    for candle in candles_1m:
        try:
            candle_time = datetime.fromisoformat(candle["t"].replace("Z", ""))
            if candle_time > when:
                continue
            
            price = candle.get("c")
            vol = candle.get("v")
            
            # Skip if price or volume is missing or invalid
            if price is None or vol is None:
                continue
            if vol <= 0:
                continue
            
            price_vol_sum += float(price) * float(vol)
            vol_sum += float(vol)
        except Exception:
            # Skip candles with bad timestamps or data
            continue
    
    if vol_sum <= 0:
        return None
    
    vwap = price_vol_sum / vol_sum
    return vwap


def _compute_vwap_slope_bps(
    candles_1m: List[Dict[str, Any]],
    when: datetime,
    window_size: int = 3,
) -> float:
    """
    Compute a simple VWAP slope approximation in basis points.
    
    This is a practical local approximation based on the last N minutes of price
    action at or before 'when'. Uses close prices as a proxy for VWAP behavior.
    
    Args:
        candles_1m: List of 1-minute candle dicts (sorted ascending by time)
        when: The moment in time to compute slope up to
        window_size: Number of recent candles to use for slope calculation (default: 3)
    
    Returns:
        Slope in basis points (bps). Positive = rising, negative = falling.
        Returns 0.0 if not enough candles or invalid data.
        
        slope_bps = ((last_price - first_price) / first_price) * 10_000
    
    Notes:
        - v0.8.1.0.2: simple VWAP slope approximation in basis points (last few minutes)
        - Only considers candles with timestamp <= when
        - Uses close prices ("c") as a practical approximation
        - Returns 0.0 when fewer than 2 qualifying candles exist
        - Future versions may compute true VWAP at multiple points for more accuracy
    """
    if not candles_1m:
        return 0.0
    
    # Filter candles that are at or before 'when'
    qualifying_candles = []
    for candle in candles_1m:
        try:
            candle_time = datetime.fromisoformat(candle["t"].replace("Z", ""))
            if candle_time <= when:
                qualifying_candles.append(candle)
        except Exception:
            # Skip candles with bad timestamps
            continue
    
    if len(qualifying_candles) < 2:
        return 0.0
    
    # Take the last N candles (window_size)
    window_candles = qualifying_candles[-window_size:]
    
    if len(window_candles) < 2:
        return 0.0
    
    # Get first and last close prices from the window
    first_price = window_candles[0].get("c")
    last_price = window_candles[-1].get("c")
    
    # Validate prices
    if first_price is None or last_price is None:
        return 0.0
    
    try:
        first_price = float(first_price)
        last_price = float(last_price)
    except (ValueError, TypeError):
        return 0.0
    
    # Avoid division by zero
    if first_price == 0:
        return 0.0
    
    # Calculate slope in basis points
    slope_bps = ((last_price - first_price) / first_price) * 10_000.0
    
    return slope_bps


def _compute_macd_hist(
    candles_1m: List[Dict[str, Any]],
    when: datetime,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> float | None:
    """
    Compute the MACD histogram at 'when' using all available closes.
    
    This is a short-window MACD approximation for TWCS. Uses standard MACD
    parameters (12, 26, 9) but works on whatever history we have at or before
    'when', rather than requiring a full slow_period + signal_period warmup.
    
    Uses standard MACD calculation based on close prices:
    - MACD line = EMA(close, 12) - EMA(close, 26)
    - Signal line = EMA(MACD line, 9)
    - MACD histogram = MACD line - Signal line
    
    Args:
        candles_1m: List of 1-minute candle dicts (sorted ascending by time)
        when: The moment in time to compute MACD histogram up to
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal EMA period (default: 9)
    
    Returns:
        MACD histogram as a float, or None if insufficient data (< 3 closes).
        
    Notes:
        - v0.8.1.0.2: short-window MACD histogram based on available closes
        - Only considers candles with timestamp <= when
        - Works with limited history (e.g. TWCS 11-bar window)
        - Returns None only when fewer than 3 closes available
        - EMA computation adapts to short series without requiring full warmup
    """
    if not candles_1m:
        return None
    
    # Filter candles that are at or before 'when' and extract closes
    closes = []
    for candle in candles_1m:
        try:
            candle_time = datetime.fromisoformat(candle["t"].replace("Z", ""))
            if candle_time > when:
                continue
            
            close = candle.get("c")
            if close is None:
                continue
            
            closes.append(float(close))
        except Exception:
            # Skip candles with bad timestamps or data
            continue
    
    # Need at least 3 closes for any meaningful MACD
    if len(closes) < 3:
        return None
    
    # Helper function to compute EMA that works on short series
    def _ema(values: List[float], period: int) -> List[float]:
        """Compute EMA series with given period, works on short series."""
        if not values:
            return []
        
        k = 2.0 / (period + 1.0)
        ema_values = []
        
        # Seed with first value
        ema = values[0]
        ema_values.append(ema)
        
        # Compute EMA for remaining values
        for price in values[1:]:
            ema = ema + k * (price - ema)
            ema_values.append(ema)
        
        return ema_values
    
    # Compute fast and slow EMAs
    fast_ema_series = _ema(closes, fast_period)
    slow_ema_series = _ema(closes, slow_period)
    
    # Compute MACD line
    macd_line_series = [fast - slow for fast, slow in zip(fast_ema_series, slow_ema_series)]
    
    # Compute signal line
    signal_series = _ema(macd_line_series, signal_period)
    
    # Get last values
    macd_line_last = macd_line_series[-1]
    signal_last = signal_series[-1]
    
    # Compute histogram
    macd_hist = macd_line_last - signal_last
    
    return macd_hist


def _compute_macd_slope(
    candles_1m: List[Dict[str, Any]],
    when: datetime,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    window_size: int = 3,
) -> float:
    """
    Compute the MACD slope (raw difference) over a short window.
    
    This is a short-window MACD slope approximation for TWCS. Computes the MACD
    histogram series up to 'when', then measures the change over the last N bars.
    
    Positive slope = MACD histogram increasing (momentum strengthening).
    Negative slope = MACD histogram decreasing (momentum weakening).
    
    Args:
        candles_1m: List of 1-minute candle dicts (sorted ascending by time)
        when: The moment in time to compute MACD slope up to
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal EMA period (default: 9)
        window_size: Number of recent MACD values to use for slope (default: 3)
    
    Returns:
        MACD slope as a float (raw difference, not percentage).
        Returns 0.0 if insufficient data (< 3 closes).
        
    Notes:
        - v0.8.1.0.2: short-window MACD slope (raw difference) for TWCS
        - Only considers candles with timestamp <= when
        - Works with limited history (e.g. TWCS 11-bar window)
        - Returns 0.0 when fewer than 2 MACD histogram values available
        - Purely observational for TWCS analysis
    """
    if not candles_1m:
        return 0.0
    
    # Filter candles that are at or before 'when' and extract closes
    closes = []
    for candle in candles_1m:
        try:
            candle_time = datetime.fromisoformat(candle["t"].replace("Z", ""))
            if candle_time > when:
                continue
            
            close = candle.get("c")
            if close is None:
                continue
            
            closes.append(float(close))
        except Exception:
            # Skip candles with bad timestamps or data
            continue
    
    # Need at least 3 closes for MACD computation
    if len(closes) < 3:
        return 0.0
    
    # Helper function to compute EMA that works on short series
    def _ema(values: List[float], period: int) -> List[float]:
        """Compute EMA series with given period, works on short series."""
        if not values:
            return []
        
        k = 2.0 / (period + 1.0)
        ema_values = []
        
        # Seed with first value
        ema = values[0]
        ema_values.append(ema)
        
        # Compute EMA for remaining values
        for price in values[1:]:
            ema = ema + k * (price - ema)
            ema_values.append(ema)
        
        return ema_values
    
    # Compute fast and slow EMAs
    fast_ema_series = _ema(closes, fast_period)
    slow_ema_series = _ema(closes, slow_period)
    
    # Compute MACD line
    macd_line_series = [fast - slow for fast, slow in zip(fast_ema_series, slow_ema_series)]
    
    # Compute signal line
    signal_series = _ema(macd_line_series, signal_period)
    
    # Compute MACD histogram series
    macd_hist_series = [m - s for m, s in zip(macd_line_series, signal_series)]
    
    # Need at least 2 histogram values for slope
    if len(macd_hist_series) < 2:
        return 0.0
    
    # Take the last N values
    window = macd_hist_series[-window_size:] if len(macd_hist_series) >= window_size else macd_hist_series
    
    # Compute slope as raw difference
    first_val = window[0]
    last_val = window[-1]
    slope = last_val - first_val
    
    return slope


# v0.8.1.0.2: rvol_open passthrough from strategy_state (if available)
def _compute_rvol_open(strategy_state: Any | None) -> float | None:
    """
    Extract precomputed rvol_open from strategy_state if available.
    
    This helper looks for a field called "rvol_open" in strategy_state, which
    represents the relative volume at market open (e.g., ratio vs previous day).
    
    In v0.8.1.0.2, strategy_state is usually not yet wired, so this will return
    None. This prepares TWCS for future versions where the strategy passes opening
    RVOL into TWCS snapshots.
    
    Args:
        strategy_state: Optional strategy state object (dict-like or object with attributes)
    
    Returns:
        rvol_open as a float if available, otherwise None.
    
    Notes:
        - Tries dict-like access first, then attribute access
        - Returns None if strategy_state is None or field is missing
        - Purely observational for TWCS; does not affect trading logic
    """
    if strategy_state is None:
        return None
    
    # Try dict-like access
    if isinstance(strategy_state, dict):
        rvol_val = strategy_state.get("rvol_open")
        if rvol_val is not None:
            try:
                return float(rvol_val)
            except (ValueError, TypeError):
                return None
    
    # Try attribute access
    try:
        rvol_val = getattr(strategy_state, "rvol_open", None)
        if rvol_val is not None:
            try:
                return float(rvol_val)
            except (ValueError, TypeError):
                return None
    except Exception:
        pass
    
    return None
