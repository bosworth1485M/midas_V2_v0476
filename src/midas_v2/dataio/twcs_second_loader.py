"""
TWCS Phase 3 – 1-Second Window Loader (v0.8.1.0.3)

Provides a safe, read-only helper to load 1-second TWCS windows around
entry/exit times from local CSVs under data/samples/.

This helper is defensive and must never raise exceptions; on any error it
returns an empty list and minimal metadata.
"""
# v0.8.1.0.3: TWCS Phase 3 1-second window loader

from __future__ import annotations
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple
import csv
import sys

__all__ = ["load_twcs_second_window"]


def load_twcs_second_window(
    symbol: str,
    date_str: str,
    target_time_str: str,
    window_before_seconds: int = 60,
    window_after_seconds: int = 0,
    csv_root: Path | None = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Load a TWCS 1-second candle window from CSV files.
    
    Args:
        symbol: Ticker symbol (e.g. "PHGE")
        date_str: Date in "YYYY-MM-DD" format
        target_time_str: Target time (ISO-like, e.g. "2025-08-06T09:58:00" or "2025-08-06 09:58:00")
        window_before_seconds: Number of seconds before target to include (default: 60)
        window_after_seconds: Number of seconds after target to include (default: 0)
        csv_root: Optional base directory for CSVs (defaults to data/samples)
    
    Returns:
        Tuple of (candles_1s, window_meta_1s) where:
        - candles_1s: List of candle dicts with OHLCV fields
        - window_meta_1s: Dict with window size and configuration
    
    Notes:
        - This is read-only and non-invasive; never crashes the backtest
        - Returns empty results on any error (with stderr warnings)
        - Target candle has idx_from_entry = 0 (seconds offset)
        - Earlier candles have negative indices (-1, -2, ...)
        - Later candles have positive indices (+1, +2, ...)
        - In v0.8.1.0.3, 1-second CSVs may not exist; this is expected
    """
    # v0.8.1.0.3: default empty return structure
    empty_result = (
        [],
        {
            "window_size_1s": 0,
            "window_before_1s": window_before_seconds,
            "window_after_1s": window_after_seconds,
        }
    )
    
    try:
        # v0.8.1.0.3: resolve CSV path
        if csv_root is None:
            csv_root = Path("data") / "samples"
        
        csv_path = csv_root / f"sample_1s_{date_str}_{symbol}.csv"
        
        if not csv_path.exists():
            print(
                f"[WARN] v0.8.1.0.3: 1s CSV not found for {symbol} {date_str} at {csv_path}",
                file=sys.stderr
            )
            return empty_result
        
        # v0.8.1.0.3: parse target time
        target_dt = _parse_target_time(target_time_str, date_str)
        if target_dt is None:
            print(
                f"[WARN] v0.8.1.0.3: Failed to parse target_time_str='{target_time_str}' "
                f"for {symbol} on {date_str}",
                file=sys.stderr
            )
            return empty_result
        
        # v0.8.1.0.3: compute time window bounds
        start_time = target_dt - timedelta(seconds=window_before_seconds)
        end_time = target_dt + timedelta(seconds=window_after_seconds)
        
        # v0.8.1.0.3: load and parse CSV
        candles = _load_csv_candles(csv_path, start_time, end_time, target_dt)
        
        if not candles:
            print(
                f"[WARN] v0.8.1.0.3: No 1s candles loaded for {symbol} on {date_str}",
                file=sys.stderr
            )
            return empty_result
        
        window_meta_1s = {
            "window_size_1s": len(candles),
            "window_before_1s": window_before_seconds,
            "window_after_1s": window_after_seconds,
        }
        
        return (candles, window_meta_1s)
    
    except Exception as exc:
        print(
            f"[ERR] v0.8.1.0.3: Failed to load TWCS 1s window for {symbol} "
            f"on {date_str} at {target_time_str}: {exc}",
            file=sys.stderr
        )
        return empty_result


def _parse_target_time(target_time_str: str, date_str: str) -> datetime | None:
    """Parse target time string to datetime object. v0.8.1.0.3"""
    try:
        # Strip trailing Z if present
        target_time_str = target_time_str.replace("Z", "")
        
        # Try ISO format with T separator first
        if "T" in target_time_str:
            # Handle both with and without seconds
            for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"]:
                try:
                    return datetime.strptime(target_time_str, fmt)
                except ValueError:
                    continue
        
        # Try space-separated format
        if " " in target_time_str:
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]:
                try:
                    return datetime.strptime(target_time_str, fmt)
                except ValueError:
                    continue
        
        # Try time-only format (HH:MM:SS or HH:MM) - combine with date_str
        if ":" in target_time_str and len(target_time_str) <= 8:
            combined = f"{date_str} {target_time_str}"
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]:
                try:
                    return datetime.strptime(combined, fmt)
                except ValueError:
                    continue
        
        return None
    except Exception:
        return None


def _load_csv_candles(
    csv_path: Path,
    start_time: datetime,
    end_time: datetime,
    target_dt: datetime,
) -> List[Dict[str, Any]]:
    """Load 1-second candles from CSV file within time window. v0.8.1.0.3"""
    candles = []
    
    try:
        with csv_path.open("r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                # Parse timestamp
                ts_str = row.get("t") or row.get("timestamp") or row.get("time")
                if not ts_str:
                    continue
                
                try:
                    # Parse timestamp (strip Z and handle common formats)
                    ts_str_clean = ts_str.replace("Z", "").strip()
                    
                    # Try ISO format first
                    if "T" in ts_str_clean:
                        for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"]:
                            try:
                                ts = datetime.strptime(ts_str_clean, fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            continue
                    else:
                        # Try space-separated format
                        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]:
                            try:
                                ts = datetime.strptime(ts_str_clean, fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            continue
                    
                    # Filter by time window
                    if ts < start_time or ts > end_time:
                        continue
                    
                    # Parse OHLCV
                    o = row.get("o") or row.get("open")
                    h = row.get("h") or row.get("high")
                    l = row.get("l") or row.get("low")
                    c = row.get("c") or row.get("close")
                    v = row.get("v") or row.get("volume")
                    
                    # Convert to float (None if missing or invalid)
                    def safe_float(val):
                        if val is None:
                            return None
                        try:
                            return float(val)
                        except (ValueError, TypeError):
                            return None
                    
                    # Calculate idx_from_entry (seconds offset from target)
                    idx_from_entry = int((ts - target_dt).total_seconds())
                    
                    candle = {
                        "t": ts.strftime("%Y-%m-%dT%H:%M:%S"),  # Normalize to ISO format
                        "o": safe_float(o),
                        "h": safe_float(h),
                        "l": safe_float(l),
                        "c": safe_float(c),
                        "v": safe_float(v),
                        "idx_from_entry": idx_from_entry,
                    }
                    
                    candles.append((ts, candle))
                
                except Exception:
                    # Skip rows with bad data
                    continue
    except Exception:
        return []
    
    # Sort by timestamp ascending and extract candle dicts
    candles.sort(key=lambda x: x[0])
    return [c[1] for c in candles]
