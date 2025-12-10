"""
TWCS Phase 3 – PNG Rendering (v0.8.1.0.5)

Provides visualization helpers for TWCS snapshots (entry and exit).
Uses matplotlib to render 1-minute and 1-second candle windows.
"""
# v0.8.1.0.5: TWCS PNG rendering module

import matplotlib
matplotlib.use("Agg")  # v0.8.1.0.5: non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Any, Dict, List

__all__ = ["plot_twcs_snapshot"]


def plot_twcs_snapshot(snapshot: Dict[str, Any], out_path: str) -> None:
    """
    Render TWCS visualization with 1-minute and 1-second candles.
    
    v0.8.1.0.5: Creates a two-panel chart showing:
    - Top panel: 1-minute candles around entry/exit
    - Bottom panel: 1-second candles around entry/exit
    - Vertical line marking the trade timestamp
    
    Args:
        snapshot: TWCS snapshot dict containing candles_1m, candles_1s, and metadata
        out_path: Output PNG file path
    
    Notes:
        - Uses green bars for bullish candles (close >= open)
        - Uses red bars for bearish candles (close < open)
        - Saves with 140 DPI for good detail
        - Calls plt.close() to avoid memory leaks
    """
    try:
        # Extract data from snapshot
        symbol = snapshot.get("symbol", "UNKNOWN")
        window_type = snapshot.get("window_type", "unknown")
        candles_1m = snapshot.get("candles_1m", [])
        candles_1s = snapshot.get("candles_1s", [])
        
        # Determine timestamp
        if window_type == "entry":
            timestamp_str = snapshot.get("entry_time", "")
            title = f"{symbol} – Entry TWCS"
        else:
            timestamp_str = snapshot.get("exit_time", "")
            title = f"{symbol} – Exit TWCS"
        
        # Parse trade timestamp
        trade_time = _parse_timestamp(timestamp_str)
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=False)
        fig.suptitle(title, fontsize=14, fontweight="bold")
        
        # Plot 1-minute candles
        _plot_candles(ax1, candles_1m, trade_time, "1-Minute Candles")
        
        # Plot 1-second candles
        _plot_candles(ax2, candles_1s, trade_time, "1-Second Candles")
        
        # Layout and save
        plt.tight_layout()
        plt.savefig(out_path, dpi=140, bbox_inches="tight")
        plt.close(fig)
    
    except Exception as exc:
        # Fail gracefully without breaking the backtest
        print(f"[WARN] v0.8.1.0.5: Failed to plot TWCS snapshot: {exc}")
        try:
            plt.close("all")
        except Exception:
            pass


def _parse_timestamp(timestamp_str: str) -> datetime | None:
    """Parse timestamp string to datetime. v0.8.1.0.5"""
    if not timestamp_str:
        return None
    
    try:
        # Try common formats
        for fmt in [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
        ]:
            try:
                return datetime.strptime(timestamp_str.replace("Z", ""), fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None


def _plot_candles(
    ax: Any,
    candles: List[Dict[str, Any]],
    trade_time: datetime | None,
    title: str,
) -> None:
    """Plot OHLC candles on given axes. v0.8.1.0.5"""
    if not candles:
        ax.text(0.5, 0.5, "No candle data", ha="center", va="center", transform=ax.transAxes)
        ax.set_title(title)
        return
    
    # Parse candles
    timestamps = []
    opens = []
    highs = []
    lows = []
    closes = []
    colors = []
    
    for candle in candles:
        try:
            # Parse timestamp
            t_str = candle.get("t", "")
            t = _parse_timestamp(t_str)
            if t is None:
                continue
            
            # Parse OHLC
            o = candle.get("o")
            h = candle.get("h")
            l = candle.get("l")
            c = candle.get("c")
            
            if None in (o, h, l, c):
                continue
            
            timestamps.append(t)
            opens.append(float(o))
            highs.append(float(h))
            lows.append(float(l))
            closes.append(float(c))
            
            # Color: green if close >= open, red otherwise
            colors.append("green" if float(c) >= float(o) else "red")
        
        except Exception:
            continue
    
    if not timestamps:
        ax.text(0.5, 0.5, "No valid candle data", ha="center", va="center", transform=ax.transAxes)
        ax.set_title(title)
        return
    
    # Plot candles as OHLC bars
    for i, (t, o, h, l, c, color) in enumerate(zip(timestamps, opens, highs, lows, closes, colors)):
        # Candle body (open to close)
        body_height = abs(c - o)
        body_bottom = min(o, c)
        ax.bar(t, body_height, bottom=body_bottom, width=0.0006, color=color, alpha=0.8, edgecolor=color)
        
        # Upper wick (high to max(open, close))
        ax.plot([t, t], [max(o, c), h], color=color, linewidth=0.8)
        
        # Lower wick (low to min(open, close))
        ax.plot([t, t], [l, min(o, c)], color=color, linewidth=0.8)
    
    # Draw vertical line at trade time
    if trade_time is not None:
        ax.axvline(trade_time, color="blue", linestyle="--", linewidth=1.5, alpha=0.7, label="Trade Time")
        ax.legend(loc="upper left")
    
    ax.set_title(title)
    ax.set_ylabel("Price")
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    ax.tick_params(axis="x", rotation=45)
