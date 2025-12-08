"""
TWCS Phase 2: Minute Window Helper (v0.8.1.0.1)

This module provides read-only helpers to load 1-minute candle windows
from CSV files for TWCS (Trade Window Capture System) snapshots.

This is non-invasive and observational only - it does not affect any
trading logic, signals, PnL, or backtest decisions.
"""
# v0.8.1.0.1: TWCS Phase 2 minute window helper

from __future__ import annotations
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
from datetime import datetime
import csv

__all__ = ["load_twcs_minute_window"]


def load_twcs_minute_window(
    symbol: str,
    date_str: str,
    target_time_str: str,
    window_before: int = 10,
    window_after: int = 0,
    csv_root: Path | None = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Load a TWCS minute candle window from CSV files.
    
    Args:
        symbol: Ticker symbol (e.g. "MWYN")
        date_str: Date in "YYYY-MM-DD" format
        target_time_str: Target time as "HH:MM" or "YYYY-MM-DD HH:MM"
        window_before: Number of minutes before target to include (default: 10)
        window_after: Number of minutes after target to include (default: 0)
        csv_root: Optional base directory for CSVs (defaults to data/samples)
    
    Returns:
        Tuple of (candles_1m, window_meta) where:
        - candles_1m: List of candle dicts with OHLCV + geometry fields
        - window_meta: Dict with window size and configuration
    
    Notes:
        - This is read-only and non-invasive; never crashes the backtest
        - Returns empty results on any error (with stderr warnings)
        - Target candle has idx_from_entry = 0
        - Earlier candles have negative indices (-1, -2, ...)
        - Later candles have positive indices (+1, +2, ...)
    """
    # v0.8.1.0.1: default empty return structure
    empty_result = (
        [],
        {
            "window_size_1m": 0,
            "window_before_1m": window_before,
            "window_after_1m": window_after,
        }
    )
    
    try:
        # v0.8.1.0.1: resolve CSV path
        if csv_root is None:
            csv_root = Path("data") / "samples"
        
        filename = f"sample_{date_str}_{symbol}.csv"
        csv_path = csv_root / filename
        
        if not csv_path.exists():
            print(
                f"[WARN] v0.8.1.0.1: Missing TWCS minute CSV for {symbol} "
                f"on {date_str} at {csv_path}",
                file=sys.stderr
            )
            return empty_result
        
        # v0.8.1.0.1: parse target time
        target_dt = _parse_target_time(target_time_str, date_str)
        if target_dt is None:
            print(
                f"[WARN] v0.8.1.0.1: Failed to parse target_time_str='{target_time_str}' "
                f"for {symbol} on {date_str}",
                file=sys.stderr
            )
            return empty_result
        
        # v0.8.1.0.1: load and parse CSV (now with date_str)
        bars = _load_csv_bars(csv_path, date_str=date_str)
        if not bars:
            print(
                f"[WARN] v0.8.1.0.1: No bars loaded from CSV for {symbol} on {date_str}",
                file=sys.stderr
            )
            return empty_result
        
        # v0.8.1.0.1: find target candle index
        idx_target = _find_target_index(bars, target_dt)
        if idx_target is None:
            print(
                f"[WARN] v0.8.1.0.1: No matching minute bar for {symbol} "
                f"at {target_time_str} on {date_str}",
                file=sys.stderr
            )
            return empty_result
        
        # v0.8.1.0.1: compute window slice
        idx_start = max(0, idx_target - window_before)
        idx_end = min(len(bars) - 1, idx_target + window_after)
        
        # v0.8.1.0.1: build candle objects with geometry
        candles_1m = []
        for i in range(idx_start, idx_end + 1):
            bar = bars[i]
            candle_dict = _build_candle_dict(bar, i, idx_target)
            candles_1m.append(candle_dict)
        
        window_meta = {
            "window_size_1m": len(candles_1m),
            "window_before_1m": window_before,
            "window_after_1m": window_after,
        }
        
        return (candles_1m, window_meta)
    
    except Exception as exc:
        print(
            f"[ERR] v0.8.1.0.1: Failed to load TWCS minute window for {symbol} "
            f"on {date_str} at {target_time_str}: {exc}",
            file=sys.stderr
        )
        return empty_result


def _parse_target_time(target_time_str: str, date_str: str) -> datetime | None:
    """Parse target time string to datetime object. v0.8.1.0.1"""
    try:
        # Handle "YYYY-MM-DD HH:MM" format
        if " " in target_time_str and len(target_time_str.split()[0]) == 10:
            return datetime.strptime(target_time_str, "%Y-%m-%d %H:%M")
        
        # Handle "HH:MM" format - combine with date_str
        if ":" in target_time_str and len(target_time_str.split(":")) == 2:
            combined = f"{date_str} {target_time_str}"
            return datetime.strptime(combined, "%Y-%m-%d %H:%M")
        
        return None
    except Exception:
        return None


def _load_csv_bars(csv_path: Path, date_str: str) -> List[Dict[str, Any]]:
    """Load bars from CSV file. v0.8.1.0.1"""
    bars = []
    try:
        with csv_path.open("r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                # Parse timestamp
                ts_str = row.get("timestamp") or row.get("ts") or row.get("time")
                if not ts_str:
                    continue
                
                ts_str = ts_str.strip()  # v0.8.1.0.1: strip whitespace
                
                try:
                    # Try parsing common formats
                    if "T" in ts_str:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    else:
                        parsed = None
                        
                        # v0.8.1.0.1: Support CSV rows with time-only "HH:MM" using date_str.
                        if ":" in ts_str and len(ts_str) == 5 and ts_str.count(":") == 1:
                            combined = f"{date_str} {ts_str}"
                            try:
                                parsed = datetime.strptime(combined, "%Y-%m-%d %H:%M")
                            except ValueError:
                                parsed = None
                        
                        # Fallback to full datetime formats if parsed is still None
                        if parsed is None:
                            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]:
                                try:
                                    parsed = datetime.strptime(ts_str, fmt)
                                    break
                                except ValueError:
                                    continue
                        
                        if parsed is None:
                            continue
                        
                        ts = parsed
                    
                    # v0.8.1.0.1: Normalize to naive datetime for TWCS comparisons.
                    if ts.tzinfo is not None:
                        ts = ts.replace(tzinfo=None)
                
                except Exception:
                    continue
                
                # Parse OHLCV
                try:
                    bar = {
                        "timestamp": ts,
                        "open": float(row.get("open") or row.get("o") or 0),
                        "high": float(row.get("high") or row.get("h") or 0),
                        "low": float(row.get("low") or row.get("l") or 0),
                        "close": float(row.get("close") or row.get("c") or 0),
                        "volume": float(row.get("volume") or row.get("v") or 0),
                    }
                    bars.append(bar)
                except (ValueError, TypeError):
                    continue
    except Exception:
        return []
    
    # v0.8.1.0.1: Ensure bars are sorted by timestamp.
    bars.sort(key=lambda b: b["timestamp"])
    
    return bars


def _find_target_index(bars: List[Dict[str, Any]], target_dt: datetime) -> int | None:
    """Find index of bar matching target datetime. v0.8.1.0.1"""
    # Match by minute precision (ignore seconds)
    target_minute = target_dt.replace(second=0, microsecond=0)
    
    for idx, bar in enumerate(bars):
        bar_minute = bar["timestamp"].replace(second=0, microsecond=0)
        if bar_minute == target_minute:
            return idx
    
    return None


def _build_candle_dict(bar: Dict[str, Any], idx: int, idx_target: int) -> Dict[str, Any]:
    """Build candle dictionary with geometry fields. v0.8.1.0.1"""
    o = bar["open"]
    h = bar["high"]
    l = bar["low"]
    c = bar["close"]
    v = bar["volume"]
    
    # Compute geometry
    price_range = h - l
    body = c - o
    
    if price_range <= 0:
        body_pct = 0.0
        upper_wick_pct = 0.0
        lower_wick_pct = 0.0
        is_doji = False
    else:
        body_pct = body / price_range
        upper_wick_pct = (h - max(o, c)) / price_range
        lower_wick_pct = (min(o, c) - l) / price_range
        
        # Doji detection: body is <= 10% of range
        is_doji = abs(body) <= 0.1 * price_range
    
    is_green = c > o
    
    # Format timestamp as ISO string
    t_str = bar["timestamp"].strftime("%Y-%m-%dT%H:%M:%S")
    
    return {
        "t": t_str,
        "o": o,
        "h": h,
        "l": l,
        "c": c,
        "v": v,
        "body_pct": body_pct,
        "upper_wick_pct": upper_wick_pct,
        "lower_wick_pct": lower_wick_pct,
        "is_green": is_green,
        "is_doji": is_doji,
        "idx_from_entry": idx - idx_target,
    }
