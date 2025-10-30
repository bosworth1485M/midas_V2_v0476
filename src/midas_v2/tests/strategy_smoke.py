from __future__ import annotations
from typing import List, Optional

# Import from your package
from midas_v2.strategy import SimpleBreakoutStrategy, StrategyParams, Bar

def make_bars(n: int, start=10.0, step=0.10, vol=1000) -> List[Bar]:
    """Create a simple rising series of n bars."""
    bars = []
    px = start
    for i in range(n):
        o = px
        h = px + step * 0.6
        l = px - step * 0.4
        c = px + step * 0.5
        v = vol + i * 100
        bars.append(Bar(t=i, o=o, h=h, l=l, c=c, v=v))
        px = c
    return bars

def make_yesterday_like(today: List[Bar], scale: float = 0.5) -> List[Bar]:
    """Yesterday with lower volumes so RVOL_open > 1 if scale < 1."""
    y = []
    for b in today:
        y.append(Bar(t=b.t, o=b.o, h=b.h, l=b.l, c=b.c, v=max(1, int(b.v * scale))))
    return y

def run_case(name: str, bars: List[Bar], yday: Optional[List[Bar]], params: StrategyParams, idx: int, expect: bool):
    strat = SimpleBreakoutStrategy(params)
    strat.set_yesterday_bars(yday)
    got = strat.should_enter(bars, idx)
    print(f"[{name}] should_enter(i={idx}) -> {got} (expected {expect})")
    assert got == expect, f"{name}: expected {expect} but got {got}"

def main():
    # Common base: 40 bars, gently rising. Use bar 20+ so gates have history.
    bars = make_bars(40, start=10.0, step=0.20, vol=2_000)
    yday = make_yesterday_like(bars, scale=0.4)  # today vol > yday vol → RVOL_open > 2.0 in first window
    i = 20

    # --- Case 1: EMA dip-reclaim passes (MACD-rise OFF to isolate reclaim path) ---
    p1 = StrategyParams(
        gate_minutes=5,
        rise_bars=3,
        green_body_min=0.0,
        require_macd_rise=False,   # disabled for pass case
        macd_rise_bars=2,
        min_rvol_open=2.0,
        rvol_open_minutes=15,
        dip_reclaim=True,
        reclaim_ref="ema",
        ema_period=5,
        min_dip_pct=0.5,           # easy dip threshold
        min_reclaim_pct=0.0,       # just reclaim the EMA (no extra %)
        reclaim_buffer_bps=0.0
    )
    run_case("EMA_reclaim_pass", bars, yday, p1, i, expect=True)

    # --- Case 2: EMA dip-reclaim fails due to RVOL gate ---
    p2 = p1.__class__(**{**p1.__dict__, "min_rvol_open": 10.0})  # unrealistic high RVOL → should fail
    run_case("EMA_reclaim_fail_rvol", bars, yday, p2, i, expect=False)

    # --- Case 3: VWAP dip-reclaim passes (MACD-rise OFF to isolate reclaim path) ---
    p3 = StrategyParams(
        gate_minutes=5,
        rise_bars=3,
        green_body_min=0.0,
        require_macd_rise=False,   # disabled for pass case
        macd_rise_bars=2,
        min_rvol_open=2.0,
        rvol_open_minutes=15,
        dip_reclaim=True,
        reclaim_ref="vwap",
        min_dip_pct=0.5,
        min_reclaim_pct=0.0,       # accept price >= VWAP
        reclaim_buffer_bps=0.0,
        vwap_slope_bps=None        # no slope filter
    )
    run_case("VWAP_reclaim_pass", bars, yday, p3, i, expect=True)

    # --- Case 4: VWAP dip-reclaim fails due to slope filter ---
    p4 = p3.__class__(**{**p3.__dict__, "vwap_slope_bps": 9999})  # absurd slope → should fail
    run_case("VWAP_reclaim_fail_slope", bars, yday, p4, i, expect=False)

    # --- Case 5: Green body min filter blocks entry even if reclaim would pass ---
    p5 = p3.__class__(**{**p3.__dict__, "green_body_min": 0.9})   # require body≈range → too strict
    run_case("VWAP_reclaim_fail_green_body", bars, yday, p5, i, expect=False)

    # --- Case 6: Explicit MACD-rising gate passes with easier criterion on an accelerated tail ---
    # Build a separate series with stronger acceleration in the last few bars so MACD hist is clearly rising at i.
    bars_accel = make_bars(40, start=10.0, step=0.20, vol=2_000)
    # Force acceleration on last three bars before/at i
    for j, bump in [(i-2, 0.6), (i-1, 0.8), (i, 1.2)]:
        prev_c = bars_accel[j-1].c
        bars_accel[j].o = prev_c
        bars_accel[j].c = prev_c + bump
        bars_accel[j].h = max(bars_accel[j].o, bars_accel[j].c) + 0.05
        bars_accel[j].l = min(bars_accel[j].o, bars_accel[j].c) - 0.05
        bars_accel[j].v = int(bars_accel[j].v * 1.5)
    yday_accel = make_yesterday_like(bars_accel, scale=0.4)

    p6 = StrategyParams(
        gate_minutes=5,
        rise_bars=3,
        green_body_min=0.0,
        require_macd_rise=True,
        macd_rise_bars=1,          # 1-bar rise to prove gate wiring; real runs can use 2+
        min_rvol_open=2.0,
        rvol_open_minutes=15,
        dip_reclaim=True,
        reclaim_ref="ema",
        ema_period=5,
        min_dip_pct=0.5,
        min_reclaim_pct=0.0,
        reclaim_buffer_bps=0.0
    )
    run_case("EMA_reclaim_macdRise_pass", bars_accel, yday_accel, p6, i, expect=True)

    print("\nAll smoke tests passed.")

if __name__ == "__main__":
    main()