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
    macd_confirm: bool = False  # legacy boolean confirm
    rise_bars: int = 2
    green_body_min: float = 0.0  # optional min real-body fraction per bar (0 keeps old behavior)
    min_pm_vol: Optional[int] = None
    reclaim_pmh: Optional[bool] = None

    # Dip reclaim knobs
    dip_reclaim: bool = False
    reclaim_ref: str = "ema"     # "ema" or "vwap"
    min_dip_pct: float = 2.0
    min_reclaim_pct: float = 0.5 # % above reference (EMA/VWAP) required to count as reclaim
    ema_period: int = 5
    reclaim_buffer_bps: float = 0.0      # extra buffer above ref in basis points (e.g., 5.0 = +5 bps)
    vwap_slope_bps: Optional[int] = None # require VWAP slope >= this bps over last few bars (optional)
    vwap_period_min: int = 1             # guard; VWAP is cumulative anyway

    # NEW (v0.3.21): Opening RVOL gate
    min_rvol_open: Optional[float] = None   # e.g., 1.5
    rvol_open_minutes: int = 15             # compare first N minutes

    # NEW (v0.4.x): Explicit MACD rising gate
    require_macd_rise: bool = False         # enable/disable MACD rising requirement
    macd_rise_bars: int = 0                 # number of consecutive rising MACD histogram bars required

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

    # NEW: VWAP utilities
    def _vwap_series(self, bars: List[Bar]) -> List[Optional[float]]:
        """Cumulative VWAP = cum(price*vol)/cum(vol). Returns per-bar VWAP."""
        vwap: List[Optional[float]] = [None] * len(bars)
        pv_cum = 0.0
        v_cum = 0.0
        for i, b in enumerate(bars):
            price = (b.h + b.l + b.c) / 3.0  # typical price
            pv_cum += price * (b.v or 0.0)
            v_cum  += (b.v or 0.0)
            vwap[i] = (pv_cum / v_cum) if v_cum > 0 else None
        return vwap

    def _vwap_slope_bps(self, vwap: List[Optional[float]], i: int, lookback: int = 3) -> Optional[float]:
        """Return approximate slope in basis points over last `lookback` bars."""
        if i < lookback or lookback <= 0:
            return None
        a = vwap[i - lookback]
        b = vwap[i]
        if a is None or b is None or a <= 0:
            return None
        return ((b - a) / a) * 1e4  # basis points

    def _required_price_above_ref(self, ref_val: Optional[float], pct: float, bps: float) -> Optional[float]:
        """Return required price given a reference, pct (e.g., 0.5%) and bps buffer."""
        if ref_val is None or ref_val <= 0:
            return None
        req = ref_val * (1.0 + (pct / 100.0 if pct else 0.0))
        if bps and bps != 0.0:
            req *= (1.0 + bps / 1e4)
        return req

    def _passes_price_rise_gate(self, bars: List[Bar], i: int) -> bool:
        if self.p.rise_bars and self.p.rise_bars > 0:
            look = min(self.p.rise_bars, i)
            if look <= 0:
                return False
            for k in range(look):
                cur = bars[i - k]
                prv = bars[i - k - 1]
                if not (cur.c > prv.c):
                    return False
                # Optional body-size filter
                if self.p.green_body_min and self.p.green_body_min > 0.0:
                    body = abs(cur.c - cur.o)
                    rng  = max(1e-9, cur.h - cur.l)
                    if (body / rng) < self.p.green_body_min:
                        return False
        return True

    def _passes_macd_gate(self, closes: List[float], i: int) -> bool:
        """Require MACD histogram to rise for N bars and be >0 when enabled."""
        if not self.p.require_macd_rise:
            return True
        n = int(self.p.macd_rise_bars or 0)
        if n <= 0 or i < n + 1:
            return False
        macd_line, signal_line, hist = macd(closes)
        # need n+1 points to compare last n deltas
        for k in range(n):
            h_cur = hist[i - k]
            h_prev = hist[i - k - 1]
            if h_cur is None or h_prev is None or not (h_cur > h_prev and h_cur > 0):
                return False
        return True

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

        # A–D: require rising greens (price candles)
        if not self._passes_price_rise_gate(bars, i):
            return False

        # NEW: MACD rising gate (only when enabled)
        closes = [b.c for b in bars]
        if not self._passes_macd_gate(closes, i):
            return False

        # (Optional EMA/VWAP/MACD boolean confirms would live here; kept as-is)
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

        # Choose reference (EMA or VWAP) and check reclaim with pct + optional bps buffer
        ref_kind = p.reclaim_ref.lower().strip()
        ref_val: Optional[float] = None
        if ref_kind == "ema":
            ema_vals = ema(closes, max(2, int(p.ema_period)))
            ref_val = ema_vals[i]
        elif ref_kind == "vwap":
            vwap_vals = self._vwap_series(bars)
            ref_val = vwap_vals[i]
            # Optional VWAP slope filter (in bps) if requested
            if p.vwap_slope_bps is not None:
                slope = self._vwap_slope_bps(vwap_vals, i, lookback=3)
                if slope is None or slope < float(p.vwap_slope_bps):
                    return False
        else:
            return False

        req_price = self._required_price_above_ref(ref_val, p.min_reclaim_pct, p.reclaim_buffer_bps)
        if req_price is None or curr_close < req_price:
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
                if self.p.green_body_min and self.p.green_body_min > 0.0:
                    cur = bars[i - k]
                    body = abs(cur.c - cur.o)
                    rng  = max(1e-9, cur.h - cur.l)
                    if (body / rng) < self.p.green_body_min:
                        return False

        # Also honor MACD rising gate here when enabled
        if not self._passes_macd_gate(closes, i):
            return False

        return True