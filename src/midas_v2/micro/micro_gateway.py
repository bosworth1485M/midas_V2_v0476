# src/midas_v2/micro/micro_gateway.py
from __future__ import annotations
from typing import Optional
from midas_v2.data.one_sec_loader import get_micro_slice_cached
from midas_v2.data.polygon_micro_loader import polygon_1s_loader
from midas_v2.micro.micro_adapter import run_micro_continuation

def check_micro_continuation(
    symbol: str,
    minute_close_epoch: int,                 # UTC epoch seconds for the minute close
    resolution: str = "5s",
    window_secs: int = 60,
    require_ema: bool = True,
    require_vwap: bool = False,
    min_green_ratio: float = 0.60,
    allow_first_pullback: bool = True,
) -> bool:
    """
    Single entry point for strategy:
      - builds the 1s/5s window after `minute_close_epoch`
      - adapts to DataFrame
      - calls your existing one_sec_continuation_ok(...)
    Returns True if continuation passes; False otherwise.
    """
    secs = get_micro_slice_cached(
        symbol=symbol,
        minute_close_ts=int(minute_close_epoch),
        seconds=int(window_secs),
        resolution=str(resolution).lower().strip(),
        loader=polygon_1s_loader,
    )
    return run_micro_continuation(
        secs,
        minute_close_epoch,
        window_secs,
        require_ema,
        require_vwap,
        min_green_ratio,
        allow_first_pullback,
    )