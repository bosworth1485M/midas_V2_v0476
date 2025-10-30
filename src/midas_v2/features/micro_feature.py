# src/midas_v2/features/micro_feature.py  # v0.4.8
from __future__ import annotations  # v0.4.8
from typing import Any  # v0.4.8

# Safe accessors so this module imports even if registry/sidecar aren’t present.  # v0.4.8
def _is_enabled(feature: str, scenario_id: str) -> bool:  # v0.4.8
    try:
        from midas_v2.features.registry import FeatureRegistry  # v0.4.8
        return FeatureRegistry.is_enabled(feature, scenario_id)  # v0.4.8
    except Exception:
        return False  # v0.4.8

def _get(feature: str, key: str, default=None):  # v0.4.8
    try:
        from midas_v2.features.registry import FeatureRegistry  # v0.4.8
        return FeatureRegistry.get(feature, key, default)  # v0.4.8
    except Exception:
        return default  # v0.4.8

# We reuse your already-smoke-tested gateway.  # v0.4.8
from midas_v2.micro.micro_gateway import check_micro_continuation  # v0.4.8
from midas_v2.utils.epoch_tools import minute_close_epoch_from_bar  # v0.4.8

def should_block_entry(  # v0.4.8
    scenario_id: str,
    symbol: str,
    minute_bar: Any,      # the current minute bar
    strategy: Any,        # to read session_date/symbol/params if needed
) -> bool:
    """
    Return True to BLOCK entry if micro continuation fails; False to ALLOW.
    Safe by design:
      - If feature disabled for this scenario -> False (allow)
      - If timestamp can't be built from the bar -> False (allow)
      - Any error -> False (allow)  # v0.4.8
    """
    if not _is_enabled("micro", scenario_id):  # v0.4.8
        return False  # allow  # v0.4.8

    # Build minute-close epoch safely (handles .ts epoch or .t 'HH:MM[:SS]').  # v0.4.8
    session_date = getattr(strategy, "session_date", "")  # v0.4.8
    ts = minute_close_epoch_from_bar(minute_bar, session_date)  # v0.4.8
    if not isinstance(ts, int):  # v0.4.8
        return False  # allow  # v0.4.8

    # Read sidecar knobs (with defaults).  # v0.4.8
    res   = _get("micro", "resolution", "5s")          # v0.4.8
    win   = int(_get("micro", "window_secs", 60))      # v0.4.8
    ema   = bool(_get("micro", "require_ema_reclaim", True))   # v0.4.8
    vwap  = bool(_get("micro", "require_vwap_hold", False))    # v0.4.8
    ratio = float(_get("micro", "min_green_ratio", 0.60))      # v0.4.8
    pull  = bool(_get("micro", "allow_first_pullback", True))  # v0.4.8

    ok = check_micro_continuation(  # v0.4.8
        symbol=symbol,
        minute_close_epoch=ts,
        resolution=res,
        window_secs=win,
        require_ema=ema,
        require_vwap=vwap,
        min_green_ratio=ratio,
        allow_first_pullback=pull,
    )
    return not ok  # True = BLOCK  # v0.4.8