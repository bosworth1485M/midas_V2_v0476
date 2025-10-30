"""
micro_strategy.py  —  minimal, decorator-free micro-confirm + entry check

What this gives you
-------------------
- Tiny Candle dataclass (timestamp, o/h/l/c, volume)
- Lightweight EMA(9) and VWAP helpers
- MACD (12,26,9) with histogram + "rising bars" gate
- Green-candle streak gate (e.g., 3 in a row)
- Optional "opening RVOL" gate (you can pass a precomputed value)
- A single call `find_first_entry(...)` that returns the first index where
  all confirms pass (after a gate in seconds), or -1 if no entry.

How to use
----------
1) Import:
   >>> from micro_strategy import Candle, find_first_entry

2) Prepare 1-second candles as a list[ Candle ] in time order.

3) Call:
   >>> idx = find_first_entry(
           candles,
           gate_seconds=15*60,     # wait e.g. 15 minutes after open
           rise_bars=3,            # require N consecutive green candles
           macd_rise_bars=2,       # require MACD histogram rising N bars
           min_rvol_open=None,     # or e.g. 2.0 if you have it
           reclaim_ref="EMA",      # "EMA" or "VWAP"
           ema_period=9
       )
   >>> if idx != -1:
           entry = candles[idx]
           print("ENTRY @", idx, entry.timestamp, entry.close)

Notes
-----
- Keep this file free of top-level non-Python text (no pasted notes) to avoid SyntaxError.
- If placing under a package (e.g., src/midas_v2/micro/), ensure __init__.py exists in both
  src/midas_v2/ and src/midas_v2/micro/ so imports work.
"""

from dataclasses import dataclass
from typing import List, Optional, Literal

# ----- Data model -------------------------------------------------------------

@dataclass
class Candle:
    timestamp: str   # e.g. "2025-08-05 09:30:01" (string is fine for this micro tool)
    open: float
    high: float
    low: float
    close: float
    volume: float


# ----- Math helpers -----------------------------------------------------------

def ema(values: List[float], period: int) -> List[Optional[float]]:
    """
    Simple EMA with None for seeds until enough data exists.
    """
    if period <= 1:
        return list(values)

    out: List[Optional[float]] = [None] * len(values)
    k = 2.0 / (period + 1.0)

    # seed with SMA of first 'period'
    if len(values) >= period:
        sma = sum(values[:period]) / period
        out[period - 1] = sma
        prev = sma
        for i in range(period, len(values)):
            prev = values[i] * k + prev * (1.0 - k)
            out[i] = prev
    return out


def vwap(candles: List[Candle]) -> List[Optional[float]]:
    """
    Cumulative VWAP from the start. For a rolling VWAP, adapt as needed.
    """
    out: List[Optional[float]] = [None] * len(candles)
    cum_pv = 0.0
    cum_v  = 0.0
    for i, c in enumerate(candles):
        typical = (c.high + c.low + c.close) / 3.0
        cum_pv += typical * c.volume
        cum_v  += c.volume
        out[i] = (cum_pv / cum_v) if cum_v > 0 else None
    return out


def macd(values: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
    """
    MACD line, Signal line, Histogram. Returns three lists (with None seeds).
    """
    ema_fast = ema(values, fast)
    ema_slow = ema(values, slow)

    macd_line: List[Optional[float]] = [None] * len(values)
    for i in range(len(values)):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line[i] = ema_fast[i] - ema_slow[i]

    # Signal on MACD line (ignore leading None)
    sig_in: List[float] = []
    sig_map_idx: List[int] = []
    for i, m in enumerate(macd_line):
        if m is not None:
            sig_in.append(m)
            sig_map_idx.append(i)

    signal_line: List[Optional[float]] = [None] * len(values)
    if sig_in:
        sig_vals = ema(sig_in, signal)
        for j, val in enumerate(sig_vals):
            signal_line[sig_map_idx[j]] = val

    hist: List[Optional[float]] = [None] * len(values)
    for i in range(len(values)):
        m = macd_line[i]
        s = signal_line[i]
        if m is not None and s is not None:
            hist[i] = m - s

    return macd_line, signal_line, hist


# ----- Gates / Confirms -------------------------------------------------------

def is_green(c: Candle) -> bool:
    return c.close > c.open


def green_streak_ok(candles: List[Candle], i: int, need: int) -> bool:
    if need <= 0:
        return True
    if i - need + 1 < 0:
        return False
    for k in range(i - need + 1, i + 1):
        if not is_green(candles[k]):
            return False
    return True


def macd_hist_rising_ok(hist: List[Optional[float]], i: int, bars: int) -> bool:
    if bars <= 0:
        return True
    if i - bars + 1 < 0:
        return False
    # require strictly increasing histogram over the last `bars`
    prev = None
    for k in range(i - bars + 1, i + 1):
        hk = hist[k]
        if hk is None:
            return False
        if prev is not None and not (hk > prev):
            return False
        prev = hk
    return True


def reclaim_ok(
    close_prices: List[float],
    ref_line: List[Optional[float]],
    i: int
) -> bool:
    """
    Require close >= reference (EMA or VWAP) at bar i and reference not None.
    """
    return (ref_line[i] is not None) and (close_prices[i] >= ref_line[i])


# ----- Main entry finder ------------------------------------------------------

def find_first_entry(
    candles: List[Candle],
    gate_seconds: int = 15 * 60,
    rise_bars: int = 3,
    macd_rise_bars: int = 2,
    min_rvol_open: Optional[float] = None,
    reclaim_ref: Literal["EMA", "VWAP"] = "EMA",
    ema_period: int = 9,
    market_open_seconds: int = 0
) -> int:
    """
    Returns the index of the first candle where all gates pass, or -1 if none.

    Parameters
    ----------
    candles : list[Candle]
        1-second candles in chronological order.
    gate_seconds : int
        Do not allow entries before this many seconds from market_open_seconds.
    rise_bars : int
        Require this many consecutive green candles ending at the entry bar.
    macd_rise_bars : int
        Require MACD histogram rising for this many bars ending at entry bar.
    min_rvol_open : Optional[float]
        If provided (e.g., 2.0), require opening RVOL >= this value at entry.
        If you don't compute RVOL, pass None to skip this gate.
    reclaim_ref : "EMA" | "VWAP"
        Which reference to reclaim (close >= ref) at entry bar.
    ema_period : int
        EMA period if reclaim_ref == "EMA".
    market_open_seconds : int
        Seconds stamp of the open for gating (0 if your timestamps are relative).
    """

    if len(candles) == 0:
        return -1

    closes = [c.close for c in candles]
    ema_ref = ema(closes, ema_period)
    vwap_ref = vwap(candles)
    macd_line, signal_line, hist = macd(closes, 12, 26, 9)

    # choose reference
    ref = ema_ref if reclaim_ref.upper() == "EMA" else vwap_ref

    # Helper to parse seconds from hh:mm:ss in timestamp if present; fallback monotonic
    def to_seconds(ts: str, idx: int) -> int:
        # Expect "HH:MM:SS" at the end; if parsing fails, assume idx seconds from start
        try:
            h, m, s = ts.strip().split()[-1].split(":")
            return int(h) * 3600 + int(m) * 60 + int(s)
        except Exception:
            return idx  # graceful fallback

    # Simple RVOL placeholder:
    # If you want opening RVOL, compute it externally and pass as min_rvol_open threshold
    # while your strategy stores the *current* RVOL value per bar. For now we skip unless provided.

    for i in range(len(candles)):
        # gate by time
        secs_since_open = to_seconds(candles[i].timestamp, i) - market_open_seconds
        if secs_since_open < gate_seconds:
            continue

        # green streak
        if not green_streak_ok(candles, i, rise_bars):
            continue

        # MACD rising
        if not macd_hist_rising_ok(hist, i, macd_rise_bars):
            continue

        # Reclaim
        if not reclaim_ok(closes, ref, i):
            continue

        # Opening RVOL gate (caller must verify current RVOL >= min_rvol_open)
        if min_rvol_open is not None:
            # In a real system, you'd provide a per-bar RVOL series; here we only
            # check that a threshold was *intended*. Replace with your series check:
            # if rvol_series[i] < min_rvol_open: continue
            pass

        return i

    return -1


# ----- Quick self-test / demo -------------------------------------------------

if __name__ == "__main__":
    # Tiny artificial run just to show it works end-to-end.
    # Creates 40 one-second candles that trend up after 20s.
    demo: List[Candle] = []
    price = 10.0
    for t in range(40):
        # drift flat first 20s, then trend up
        if t >= 20:
            price += 0.04
        o = price - 0.02
        h = price + 0.03
        l = price - 0.05
        c = price
        v = 1000 + (t * 10)
        demo.append(Candle(f"2025-08-05 09:30:{t:02d}", o, h, l, c, v))

    idx = find_first_entry(
        demo,
        gate_seconds=15,      # wait 15 seconds (tiny for demo)
        rise_bars=3,
        macd_rise_bars=2,
        min_rvol_open=None,   # skip in demo
        reclaim_ref="EMA",
        ema_period=9,
        market_open_seconds=9*3600 + 30*60  # 09:30:00
    )

    if idx != -1:
        print(f"ENTRY found at index {idx} @ {demo[idx].timestamp} close={demo[idx].close:.4f}")
    else:
        print("No entry found.")