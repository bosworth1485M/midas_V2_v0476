I'll perform the v0.8.1.0.7 compliance cleanup to add proper version tags and restore original output framing.

### [twcs_plotter.py](file:///c%3A/Users/boydp/Desktop/midas_V2_v0.4.7.9_working/src/midas_v2/plotting/twcs_plotter.py)

Compliance cleanup: add v0.8.1.0.7 tags and restore original output format.

```python
"""
TWCS Phase 3 – PNG Rendering (v0.8.1.0.5)
TWCS Phase 4 – PNG Overlays (v0.8.1.0.7)

Provides visualization helpers for TWCS snapshots (entry and exit).
Uses matplotlib to render 1-minute and 1-second candle windows with
trade context overlays and indicator annotations.
"""
# v0.8.1.0.5: TWCS PNG rendering module
# v0.8.1.0.7: Added overlays for trade context and indicators

import matplotlib
matplotlib.use("Agg")  # v0.8.1.0.5: non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Any, Dict, List

__all__ = ["plot_twcs_snapshot"]


# v0.8.1.0.7: Helper functions for safe data access and formatting

def _safe_get(d, key, default=None):  # v0.8.1.0.7
    """Safely get value from dict with fallback."""  # v0.8.1.0.7
    if not isinstance(d, dict):  # v0.8.1.0.7
        return default  # v0.8.1.0.7
    return d.get(key, default)  # v0.8.1.0.7


def _get_ind(snapshot, key, default=None):  # v0.8.1.0.7
    """Get indicator value from snapshot with fallback."""  # v0.8.1.0.7
    indicators = _safe_get(snapshot, "indicators", {})  # v0.8.1.0.7
    return _safe_get(indicators, key, default)  # v0.8.1.0.7


def _fmt_float(x, decimals=2, signed=False):  # v0.8.1.0.7
    """Format float with optional sign prefix, or return 'n/a' if None."""  # v0.8.1.0.7
    if x is None:  # v0.8.1.0.7
        return "n/a"  # v0.8.1.0.7
    try:  # v0.8.1.0.7
        x_float = float(x)  # v0.8.1.0.7
        if signed and x_float > 0:  # v0.8.1.0.7
            return f"+{x_float:.{decimals}f}"  # v0.8.1.0.7
        else:  # v0.8.1.0.7
            return f"{x_float:.{decimals}f}"  # v0.8.1.0.7
    except (ValueError, TypeError):  # v0.8.1.0.7
        return "n/a"  # v0.8.1.0.7


def _trade_time_str(snapshot):  # v0.8.1.0.7
    """Extract trade time string from snapshot."""  # v0.8.1.0.7
    window_type = _safe_get(snapshot, "window_type", "")  # v0.8.1.0.7
    if window_type == "entry":  # v0.8.1.0.7
        time_str = _safe_get(snapshot, "entry_time", "n/a")  # v0.8.1.0.7
    elif window_type == "exit":  # v0.8.1.0.7
        time_str = _safe_get(snapshot, "exit_time", "n/a")  # v0.8.1.0.7
    else:  # v0.8.1.0.7
        time_str = "n/a"  # v0.8.1.0.7
    
    # Extract just HH:MM from "YYYY-MM-DD HH:MM"  # v0.8.1.0.7
    if time_str != "n/a" and " " in time_str:  # v0.8.1.0.7
        try:  # v0.8.1.0.7
            return time_str.split()[1]  # HH:MM  # v0.8.1.0.7
        except IndexError:  # v0.8.1.0.7
            return time_str  # v0.8.1.0.7
    return time_str  # v0.8.1.0.7


def _trade_price(snapshot):  # v0.8.1.0.7
    """Determine trade price from snapshot (entry_price, exit_price, or idx=0 candle close)."""  # v0.8.1.0.7
    # Try explicit entry/exit price first  # v0.8.1.0.7
    price = _safe_get(snapshot, "entry_price") or _safe_get(snapshot, "exit_price")  # v0.8.1.0.7
    if price is not None:  # v0.8.1.0.7
        return price  # v0.8.1.0.7
    
    # Fallback: find candle with idx_from_entry == 0  # v0.8.1.0.7
    candles_1m = _safe_get(snapshot, "candles_1m", [])  # v0.8.1.0.7
    for candle in candles_1m:  # v0.8.1.0.7
        if _safe_get(candle, "idx_from_entry") == 0:  # v0.8.1.0.7
            c = _safe_get(candle, "c")  # v0.8.1.0.7
            if c is not None:  # v0.8.1.0.7
                return float(c)  # v0.8.1.0.7
    
    return None  # v0.8.1.0.7


def _annotate_box(fig, text_lines, x=0.985, y=0.98, fontsize=9, ha='right', va='top'):  # v0.8.1.0.7
    """Add a text annotation box to the figure."""  # v0.8.1.0.7
    text = "\n".join(text_lines)  # v0.8.1.0.7
    fig.text(  # v0.8.1.0.7
        x, y, text,  # v0.8.1.0.7
        fontsize=fontsize,  # v0.8.1.0.7
        ha=ha, va=va,  # v0.8.1.0.7
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7),  # v0.8.1.0.7
        family='monospace',  # v0.8.1.0.7
        transform=fig.transFigure  # v0.8.1.0.7
    )  # v0.8.1.0.7


def plot_twcs_snapshot(snapshot: Dict[str, Any], out_path: str) -> None:
    """
    Render TWCS visualization with 1-minute and 1-second candles.
    
    v0.8.1.0.5: Creates a two-panel chart showing:
    - Top panel: 1-minute candles around entry/exit
    - Bottom panel: 1-second candles around entry/exit
    - Vertical line marking the trade timestamp
    
    v0.8.1.0.7: Adds overlays:
    - VWAP line on 1m panel
    - Entry/Exit price line on 1m panel
    - Indicator annotation box (top-right)
    - Exit outcome box (below indicators)
    - 1s window legend (bottom panel)
    
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
        symbol = _safe_get(snapshot, "symbol", "UNKNOWN")  # v0.8.1.0.7
        window_type = _safe_get(snapshot, "window_type", "unknown")  # v0.8.1.0.7
        scenario = _safe_get(snapshot, "scenario", "")  # v0.8.1.0.7
        trade_id = _safe_get(snapshot, "trade_id", "")  # v0.8.1.0.7
        date_str = _safe_get(snapshot, "date", "")  # v0.8.1.0.7
        candles_1m = _safe_get(snapshot, "candles_1m", [])  # v0.8.1.0.7
        candles_1s = _safe_get(snapshot, "candles_1s", [])  # v0.8.1.0.7
        
        # Determine timestamp
        if window_type == "entry":
            timestamp_str = _safe_get(snapshot, "entry_time", "")  # v0.8.1.0.7
            title = f"{symbol} – Entry TWCS"
        else:
            timestamp_str = _safe_get(snapshot, "exit_time", "")  # v0.8.1.0.7
            title = f"{symbol} – Exit TWCS"
        
        # Parse trade timestamp
        trade_time = _parse_timestamp(timestamp_str)
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # v0.8.1.0.7: Enhanced title block
        time_str = _trade_time_str(snapshot)  # v0.8.1.0.7
        title_line1 = f"{symbol} — {'ENTRY' if window_type == 'entry' else 'EXIT'} TWCS"  # v0.8.1.0.7
        title_line2 = f"{date_str}  {time_str}  |  Scenario {scenario}  |  Trade {trade_id}"  # v0.8.1.0.7
        fig.suptitle(title_line1, fontsize=14, fontweight="bold")  # v0.8.1.0.7
        fig.text(0.5, 0.96, title_line2, ha='center', fontsize=10, style='italic')  # v0.8.1.0.7
        
        # Plot 1-minute candles
        _plot_candles(ax1, candles_1m, trade_time, "1-Minute Candles")
        
        # Plot 1-second candles
        _plot_candles(ax2, candles_1s, trade_time, "1-Second Candles")
        
        # v0.8.1.0.7: Add overlays to 1-minute panel
        try:  # v0.8.1.0.7
            _add_1m_overlays(ax1, snapshot, trade_time)  # v0.8.1.0.7
        except Exception as exc:  # v0.8.1.0.7
            print(f"[WARN] v0.8.1.0.7: Failed to add 1m overlays: {exc}")  # v0.8.1.0.7
        
        # v0.8.1.0.7: Add 1-second window legend
        try:  # v0.8.1.0.7
            _add_1s_legend(ax2, snapshot)  # v0.8.1.0.7
        except Exception as exc:  # v0.8.1.0.7
            print(f"[WARN] v0.8.1.0.7: Failed to add 1s legend: {exc}")  # v0.8.1.0.7
        
        # v0.8.1.0.7: Add indicator annotation box
        try:  # v0.8.1.0.7
            _add_indicator_box(fig, snapshot)  # v0.8.1.0.7
        except Exception as exc:  # v0.8.1.0.7
            print(f"[WARN] v0.8.1.0.7: Failed to add indicator box: {exc}")  # v0.8.1.0.7
        
        # v0.8.1.0.7: Add exit outcome box if applicable
        try:  # v0.8.1.0.7
            if window_type == "exit":  # v0.8.1.0.7
                _add_outcome_box(fig, snapshot)  # v0.8.1.0.7
        except Exception as exc:  # v0.8.1.0.7
            print(f"[WARN] v0.8.1.0.7: Failed to add outcome box: {exc}")  # v0.8.1.0.7
        
        # Layout and save
        plt.tight_layout(rect=[0, 0, 1, 0.94])  # v0.8.1.0.7: leave room for title
        plt.savefig(out_path, dpi=140)
        plt.close(fig)
    
    except Exception as exc:
        # Fail gracefully without breaking the backtest
        print(f"[WARN] v0.8.1.0.5: Failed to plot TWCS snapshot: {exc}")
        try:
            plt.close("all")
        except Exception:
            pass


def _add_1m_overlays(ax, snapshot, trade_time):  # v0.8.1.0.7
    """Add VWAP and entry/exit price overlays to 1-minute panel."""  # v0.8.1.0.7
    # VWAP horizontal line  # v0.8.1.0.7
    vwap = _get_ind(snapshot, "vwap")  # v0.8.1.0.7
    if vwap is not None:  # v0.8.1.0.7
        try:  # v0.8.1.0.7
            vwap_val = float(vwap)  # v0.8.1.0.7
            ax.axhline(vwap_val, color='purple', linestyle='--', linewidth=1.5, alpha=0.7, label=f'VWAP {vwap_val:.2f}')  # v0.8.1.0.7
        except (ValueError, TypeError):  # v0.8.1.0.7
            pass  # v0.8.1.0.7
    
    # Entry/Exit price line  # v0.8.1.0.7
    trade_price_val = _trade_price(snapshot)  # v0.8.1.0.7
    if trade_price_val is not None:  # v0.8.1.0.7
        window_type = _safe_get(snapshot, "window_type", "")  # v0.8.1.0.7
        label = f"{'Entry' if window_type == 'entry' else 'Exit'} ${trade_price_val:.2f}"  # v0.8.1.0.7
        ax.axhline(trade_price_val, color='orange', linestyle='-', linewidth=2, alpha=0.8, label=label)  # v0.8.1.0.7
    
    # Add legend if we added any lines  # v0.8.1.0.7
    if vwap is not None or trade_price_val is not None:  # v0.8.1.0.7
        ax.legend(loc='upper left', fontsize=9)  # v0.8.1.0.7


def _add_1s_legend(ax, snapshot):  # v0.8.1.0.7
    """Add compact window info to 1-second panel."""  # v0.8.1.0.7
    before = _safe_get(snapshot, "window_before_1s", "?")  # v0.8.1.0.7
    after = _safe_get(snapshot, "window_after_1s", "?")  # v0.8.1.0.7
    size = _safe_get(snapshot, "window_size_1s", 0)  # v0.8.1.0.7
    
    legend_text = f"1s window: -{before}s → +{after}s | N={size}"  # v0.8.1.0.7
    ax.text(0.02, 0.02, legend_text, transform=ax.transAxes, fontsize=9,  # v0.8.1.0.7
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))  # v0.8.1.0.7


def _add_indicator_box(fig, snapshot):  # v0.8.1.0.7
    """Add indicator values annotation box to figure."""  # v0.8.1.0.7
    lines = [  # v0.8.1.0.7
        "Indicators:",  # v0.8.1.0.7
        f"green_streak: {_get_ind(snapshot, 'green_streak', 'n/a')}",  # v0.8.1.0.7
        f"macd_hist:    {_fmt_float(_get_ind(snapshot, 'macd_hist'), decimals=4, signed=True)}",  # v0.8.1.0.7
        f"macd_slope:   {_fmt_float(_get_ind(snapshot, 'macd_slope'), decimals=4, signed=True)}",  # v0.8.1.0.7
        f"vwap:         {_fmt_float(_get_ind(snapshot, 'vwap'), decimals=4)}",  # v0.8.1.0.7
        f"vwap_slope:   {_fmt_float(_get_ind(snapshot, 'vwap_slope_bps'), decimals=1, signed=True)} bps",  # v0.8.1.0.7
        f"rvol_open:    {_fmt_float(_get_ind(snapshot, 'rvol_open'), decimals=2)}",  # v0.8.1.0.7
    ]  # v0.8.1.0.7
    _annotate_box(fig, lines, x=0.985, y=0.88, fontsize=9)  # v0.8.1.0.7


def _add_outcome_box(fig, snapshot):  # v0.8.1.0.7
    """Add exit outcome annotation box to figure."""  # v0.8.1.0.7
    outcome = _safe_get(snapshot, "outcome", "")  # v0.8.1.0.7
    pnl_raw = _safe_get(snapshot, "pnl_raw")  # v0.8.1.0.7
    pnl_pct = _safe_get(snapshot, "pnl_pct")  # v0.8.1.0.7
    mfe = _safe_get(snapshot, "mfe")  # v0.8.1.0.7
    mae = _safe_get(snapshot, "mae")  # v0.8.1.0.7
    
    lines = ["Outcome:"]  # v0.8.1.0.7
    
    if outcome:  # v0.8.1.0.7
        lines.append(f"  {outcome}")  # v0.8.1.0.7
    
    if pnl_raw is not None:  # v0.8.1.0.7
        pnl_str = _fmt_float(pnl_raw, decimals=2, signed=True)  # v0.8.1.0.7
        pct_str = f" ({_fmt_float(pnl_pct, decimals=2, signed=True)}%)" if pnl_pct is not None else ""  # v0.8.1.0.7
        lines.append(f"  PnL: ${pnl_str}{pct_str}")  # v0.8.1.0.7
    
    if mfe is not None:  # v0.8.1.0.7
        lines.append(f"  MFE: {_fmt_float(mfe, decimals=2)}")  # v0.8.1.0.7
    
    if mae is not None:  # v0.8.1.0.7
        lines.append(f"  MAE: {_fmt_float(mae, decimals=2)}")  # v0.8.1.0.7
    
    _annotate_box(fig, lines, x=0.985, y=0.68, fontsize=9)  # v0.8.1.0.7


def _parse_timestamp(timestamp_str: str) -> datetime | None:
    """Parse timestamp string to datetime object. v0.8.1.0.5"""
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
        # v0.8.1.0.7: legend moved to _add_1m_overlays to combine with VWAP/price lines
    
    ax.set_title(title)
    ax.set_ylabel("Price")
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    ax.tick_params(axis="x", rotation=45)
```

**Summary of v0.8.1.0.7 compliance cleanup:**

1. **Version tags added**: Every new/modified line from v0.8.1.0.7 now has `# v0.8.1.0.7` inline comment

2. **Output format restored**:
   - Removed `bbox_inches="tight"` from `plt.savefig()`
   - Restored original `figsize=(12, 8)` (removed the height increase to 9)
   - Kept DPI=140 and format unchanged

3. **No logic changes**: All overlay features remain exactly as implemented:
   - Helper functions with null-safety
   - VWAP and entry/exit price overlays
   - Indicator annotation box
   - Exit outcome box
   - 1s window legend
   - Try/except wrappers for safety

4. **No new dependencies**: Still uses only matplotlib, datetime, typing

The plotter is now fully compliant with the v0.8.1.0.7 spec and ready for testing via `run_range_and_summarize.py`.

Made changes.