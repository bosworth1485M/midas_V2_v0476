# src/midas_v2/micro/micro_adapter.py
from __future__ import annotations
from typing import List, Dict
import pandas as pd

# Import your existing micro check (per your codebase/traceback)
from .micro_confirm import one_sec_continuation_ok  # keep this name if that's what your file defines

def to_seconds_df(seconds_bars: List[Dict]) -> pd.DataFrame:
    """
    Convert list of 1s/5s bars -> pandas.DataFrame with UTC-millisecond 't' column
    and columns ['o','h','l','c','v'] as expected by micro_confirm.
    seconds_bars must contain at least: ts (epoch seconds), open/high/low/close; may include volume.
    """
    df = pd.DataFrame(seconds_bars)
    if df.empty:
        # return empty with expected schema to satisfy df.empty, column lookups
        return pd.DataFrame(columns=["t","o","h","l","c","v"])

    # Normalize timestamp field: 'ts' (sec) → 't' (ms). Some 1s loaders use 'ts'; some use 't' (ms).
    if "ts" in df.columns:
        df["t"] = (df["ts"].astype("int64") * 1000)
    elif "t" in df.columns:
        # assume already ms
        df["t"] = df["t"].astype("int64")
    else:
        raise ValueError("to_seconds_df: expected a 'ts' (sec) or 't' (ms) field in seconds_bars")

    # Normalize OHLCV column names to o/h/l/c/v
    colmap = {}
    if "open" in df.columns:   colmap["open"] = "o"
    if "high" in df.columns:   colmap["high"] = "h"
    if "low" in df.columns:    colmap["l"] = "l"
    if "low" in df.columns:    colmap["low"] = "l"
    if "close" in df.columns:  colmap["close"] = "c"
    if "volume" in df.columns: colmap["volume"] = "v"
    df = df.rename(columns=colmap)

    # Ensure required columns exist
    required = ["t","o","h","l","c","v"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"to_seconds_df: missing required columns: {missing}")

    # Keep only the expected columns in the expected order
    df = df[["t","o","h","l","c","v"]].copy()

    # Also set a UTC datetime index for convenience (micro_confirm may not need it, but it's harmless)
    df["ts"] = (df["t"].astype("int64") // 1000)
    df.index = pd.to_datetime(df["ts"], unit="s", utc=True)
    df.drop(columns=["ts"], inplace=True)

    return df

def run_micro_continuation(
    seconds_bars: List[Dict],
    minute_close_epoch: int,            # (UTC epoch seconds for the minute close)
    seconds_window: int,                # e.g., 60
    require_ema: bool,
    require_vwap: bool,
    min_green_ratio: float,
    allow_first_pullback: bool,
) -> bool:
    """
    Adapter: converts list-of-dicts ➜ DataFrame with 't' (ms) + o/h/l/c/v,
    then calls one_sec_continuation_ok(df, minute_close_ms, seconds_window, require_ema, require_vwap, min_green_ratio, allow_first_pullback).
    Returns True (pass) / False (block).
    """
    df_seconds = to_seconds_df(seconds_bars)
    minute_close_ms = int(minute_close_epoch) * 1000

    # Call with POSITIONAL args to match micro_confirm signature
    return bool(
        one_sec_continuation_ok(
            df_seconds,
            int(minute_close_ms),
            int(seconds_window),
            bool(require_ema),
            bool(require_vwap),
            float(min_green_ratio),
            bool(allow_first_pullback),
        )
    )