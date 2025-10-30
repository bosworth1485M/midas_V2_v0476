from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import math

@dataclass
class StrategyParams:
    gate_minutes: int = 5
    tp_pct: float = 1.2
    sl_pct: float = 2.7
    vwap_confirm: bool = False
    ema_confirm: bool = True
    macd_confirm: bool = False
    rise_bars: int = 2
    min_pm_vol: Optional[int] = None
    reclaim_pmh: Optional[bool] = None

    # Dip reclaim knobs
    dip_reclaim: bool = False
    reclaim_ref: str = "ema"
    min_dip_pct: float = 2.0
    min_reclaim_pct: float = 0.5
    ema_period: int = 5

    # NEW (v0.3.21): Opening RVOL gate
    min_rvol_open: Optional[float] = None   # e.g., 1.5
    rvol_open_minutes: int = 15             # compare first N minutes

class Bar:
    def __init__(self, t, o, h, l, c, v):
        self.t = t; self.o = o; self.h = h; self.l = l; self.c = c; self.v = v

def ema(series: List[float], period: int) -> List[Optional[float]]:
    if period <= 1:
        return [float(x) for x in series]
    out: List[Optional[float]] = [None] * len(series)
    k = 2.0 / (period + 1.0)
    val: Optional[float] = None
    for i, x in enumerate(series):
        if val is None:
            if i + 1 >= period:
                seed = sum(series[i + 1 - period : i + 1]) / float(period)
                val = seed
            else:
                val = x
        else:
            val = (x - val) * k + val
        out[i] = val
    return out

def macd(series: List[float], fast=12, slow=26, signal=9):
    if slow < fast:
        fast, slow = slow, fast
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line: List[Optional[float]] = [None] * len(series)
    for i in range(len(series)):
        if ema_fast[i] is None or ema_slow[i] is None:
            macd_line[i] = None
        else:
            macd_line[i] = float(ema_fast[i]) - float(ema_slow[i])
    signal_line = ema([x if x is not None else 0.0 for x in macd_line], signal)
    hist: List[Optional[float]] = [None] * len(series)
    for i in range(len(series)):
        if macd_line[i] is None or signal_line[i] is None:
            hist[i] = None
        else:
            hist[i] = float(macd_line[i]) - float(signal_line[i])
    return macd_line, signal_line, hist

class SimpleBreakoutStrategy:
    def __init__(self, params: StrategyParams):
        self.p = params
        self._yday_bars: Optional[List[Bar]] = None  # NEW: prior-day bars (optional)

    # NEW: allow engine to provide yesterday’s bars
    def set_yesterday_bars(self, bars: Optional[List[Bar]]) -> None:
        self._yday_bars = bars

    def targets(self, entry: float):
        tp = entry * (1.0 + self.p.tp_pct / 100.0)
        sl = entry * (1.0 - self.p.sl_pct / 100.0)
        return tp, sl

    # NEW: opening RVOL helper
    def _opening_rvol_ok(self, today: List[Bar], yesterday: Optional[List[Bar]], minutes: int, thresh: float) -> bool:
        if yesterday is None or not today:
            return True  # fail-open if no prior-day bars are set
        n = min(minutes, len(today), len(yesterday))
        if n <= 0:
            return True
        vol_today = sum(b.v for b in today[:n]) or 0
        vol_yday  = sum(b.v for b in yesterday[:n]) or 1
        rvol = vol_today / vol_yday
        return rvol >= thresh

    def should_enter(self, bars: List[Bar], i: int) -> bool:
        # Gate by minutes
        if i < max(0, int(self.p.gate_minutes)):
            return False

        # Opening RVOL gate (v0.3.21)
        if self.p.min_rvol_open is not None and self.p.min_rvol_open > 0:
            if not self._opening_rvol_ok(bars, self._yday_bars, int(self.p.rvol_open_minutes), float(self.p.min_rvol_open)):
                return False

        if self.p.dip_reclaim:
            return self._dip_reclaim_should_enter(bars, i)

        # A–D: require rising greens
        if self.p.rise_bars and self.p.rise_bars > 0:
            look = min(self.p.rise_bars, i)
            if look <= 0:
                return False
            for k in range(look):
                if not (bars[i - k].c > bars[i - k - 1].c):
                    return False

        # (Optional EMA/VWAP/MACD checks would live here)
        return True

    def _dip_reclaim_should_enter(self, bars: List[Bar], i: int) -> bool:
        p = self.p
        if i < 3:
            return False

        closes = [b.c for b in bars]
        lookback = min(20, i)
        swing_high = max(closes[i - lookback : i])
        curr_close = closes[i]
        recent_segment = closes[i - lookback : i + 1]
        trough = min(recent_segment)
        if swing_high <= 0:
            return False
        dip_pct = (swing_high - trough) / swing_high * 100.0
        if dip_pct < p.min_dip_pct:
            return False

        if p.reclaim_ref.lower() == "ema":
            ema_vals = ema(closes, max(2, int(p.ema_period)))
            ema_ref = ema_vals[i]
            if ema_ref is None:
                return False
            if curr_close < ema_ref * (1.0 + p.min_reclaim_pct / 100.0):
                return False
        else:
            return False

        if p.macd_confirm:
            macd_line, signal_line, hist = macd(closes)
            if macd_line[i] is None or signal_line[i] is None or hist[i] is None:
                return False
            if not (macd_line[i] > signal_line[i]):
                return False
            if hist[i] <= (hist[i - 1] if hist[i - 1] is not None else -1e9):
                return False

        if p.rise_bars and p.rise_bars > 0:
            look = min(p.rise_bars, i)
            for k in range(look):
                if not (bars[i - k].c >= bars[i - k - 1].c):
                    return False

        return True