from __future__ import annotations
from datetime import datetime, timezone
from typing import Callable, Iterable, List, Dict, Tuple, Optional
import pandas as pd

# Optional: enforce a minimum version used in other Cameron builds
_MIN_PANDAS = "2.2.0"
if tuple(map(int, pd.__version__.split(".")[:2])) < (2, 2):
    raise RuntimeError(f"pandas>={_MIN_PANDAS} required, found {pd.__version__}")

Bar = Dict[str, float]  # ts (epoch seconds), open, high, low, close, volume
# Cache: (symbol, minute_close_epoch, seconds, resolution) -> list[Bar]
_MICRO_CACHE: Dict[Tuple[str, int, int, str], List[Bar]] = {}

def _to_epoch(ts) -> int:
    if isinstance(ts, (int, float)):
        return int(ts)
    if isinstance(ts, str):
        return int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return int(ts.timestamp())
    raise TypeError(f"Unsupported ts type: {type(ts)}")

def _normalize_rows(rows: Iterable[Dict]) -> pd.DataFrame:
    """Rows must include ts(open/high/low/close/volume). Return a 1s-indexed DataFrame (UTC)."""
    recs: List[Bar] = []
    for r in rows:
        recs.append({
            "ts": _to_epoch(r["ts"]),
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low":  float(r["low"]),
            "close":float(r["close"]),
            "volume": float(r.get("volume", 0)),
        })
    if not recs:
        return pd.DataFrame(columns=["open","high","low","close","volume"]).astype(float)
    df = pd.DataFrame(recs)
    df = df.sort_values("ts")
    df.index = pd.to_datetime(df["ts"], unit="s", utc=True)
    return df.drop(columns=["ts"])

def _df_to_list(df: pd.DataFrame) -> List[Bar]:
    return [
        {
            "ts": int(ts.value // 10**9),
            "open": float(r.open),
            "high": float(r.high),
            "low":  float(r.low),
            "close":float(r.close),
            "volume": float(r.volume),
        }
        for ts, r in df.iterrows()
    ]

def get_micro_slice_cached(
    symbol: str,
    minute_close_ts,
    seconds: int = 60,
    resolution: str = "5s",   # "1s" or "5s"
    loader: Optional[Callable[[str, int, int], Iterable[Dict]]] = None,
) -> List[Bar]:
    """
    Return bars for [minute_close_ts, minute_close_ts+seconds) at the given resolution.
    - loader(symbol, minute_close_epoch, seconds) must yield raw **1-second** rows:
      dict(ts, open, high, low, close, volume)
    - Caches by (symbol, epoch, seconds, resolution)
    """
    if loader is None:
        raise RuntimeError("Provide a loader that wraps your Polygon 1s fetch (e.g., polygon_1s_loader).")

    epoch = _to_epoch(minute_close_ts)
    key = (symbol, epoch, int(seconds), resolution)
    if key in _MICRO_CACHE:
        return _MICRO_CACHE[key]

    # 1) Fetch & normalize raw 1s rows
    df = _normalize_rows(loader(symbol, epoch, int(seconds)))
    if df.empty:
        _MICRO_CACHE[key] = []
        return []

    # 2) Optionally resample to 5s
    if resolution == "1s":
        df_out = df[["open","high","low","close","volume"]]
    elif resolution == "5s":
        agg = {"open":"first","high":"max","low":"min","close":"last","volume":"sum"}
        # ↓↓↓ Only change: '5S' → '5s'
        df_out = df.resample("5s").agg(agg).dropna(subset=["open","high","low","close"])
    else:
        raise ValueError("resolution must be '1s' or '5s'")

    out = _df_to_list(df_out)
    _MICRO_CACHE[key] = out
    return out