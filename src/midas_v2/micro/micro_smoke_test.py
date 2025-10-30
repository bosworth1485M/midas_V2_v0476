# src/midas_v2/micro/micro_smoke_test.py
"""
Standalone logic smoke tests for micro_strategy.py (import-based)
Run from project root:
  set PYTHONPATH=src & python src/midas_v2/micro/micro_smoke_test.py
"""
from midas_v2.micro.micro_strategy import Candle, find_first_entry

def make_uptrend(n=90, ramp_start=30, base=10.0, uptick=0.04):
    """Clean uptrend after ramp_start (many greens)."""
    cs = []
    price = base
    for t in range(n):
        if t >= ramp_start:
            price += uptick
        o = price - 0.02
        h = price + 0.03
        l = price - 0.05
        c = price
        v = 1000 + t * 10
        cs.append(Candle(f"2025-08-05 09:30:{t:02d}", o, h, l, c, v))
    return cs

def make_mixed_uptrend(n=90, ramp_start=30, base=10.0, uptick=0.04, red_every=3):
    """Uptrend but inject a red candle every `red_every` bars to break long green streaks."""
    cs = []
    price = base
    for t in range(n):
        if t >= ramp_start:
            price += uptick
        # make every `red_every`-th bar red (close < open)
        if t % red_every == 0:
            c = price
            o = price + 0.01   # open slightly above close -> red
        else:
            o = price - 0.02   # green bias
            c = price
        h = max(o, c) + 0.03
        l = min(o, c) - 0.05
        v = 1000 + t * 10
        cs.append(Candle(f"2025-08-05 09:30:{t:02d}", o, h, l, c, v))
    return cs

def make_sideways(n=90, base=10.0, jitter=0.002):
    """Mostly flat series—MACD histogram won’t be strictly rising for long."""
    cs = []
    price = base
    for t in range(n):
        # tiny oscillation
        delta = ((t % 4) - 1.5) * jitter
        price = base + delta
        o = price - 0.001
        c = price + 0.001 if (t % 2) else price - 0.001  # alternate green/red
        h = max(o, c) + 0.003
        l = min(o, c) - 0.003
        v = 1000 + (t % 5) * 5
        cs.append(Candle(f"2025-08-05 09:30:{t:02d}", o, h, l, c, v))
    return cs

def run_case(label, candles, expect_allow: bool, **params):
    idx = find_first_entry(candles, **params)
    got_allow = (idx != -1)
    status = "PASS" if got_allow == expect_allow else "FAIL"
    detail = f"idx={idx if got_allow else -1}"
    print(f"[{status}] {label:<60} -> {detail}")
    return status == "PASS"

def main():
    mopen = 9*3600 + 30*60

    # datasets tailored for expectations
    clean = make_uptrend()
    mixed = make_mixed_uptrend()
    flat  = make_sideways()

    total = 0; passed = 0

    # 1) ALLOW on clean uptrend past small time gate
    total += 1
    passed += run_case(
        "Time gate 15s allows entries (clean uptrend, EMA reclaim)",
        clean, True,
        gate_seconds=15, rise_bars=3, macd_rise_bars=2,
        reclaim_ref="EMA", ema_period=9, market_open_seconds=mopen
    )

    # 2) BLOCK with oversized time gate
    total += 1
    passed += run_case(
        "Time gate 600s blocks (dataset ~90s long)",
        clean, False,
        gate_seconds=600, rise_bars=3, macd_rise_bars=2,
        reclaim_ref="EMA", ema_period=9, market_open_seconds=mopen
    )

    # 3) BLOCK with overly strict green streak on mixed series
    total += 1
    passed += run_case(
        "Green streak too strict (rise_bars=8) blocks on mixed uptrend",
        mixed, False,
        gate_seconds=15, rise_bars=8, macd_rise_bars=2,
        reclaim_ref="EMA", ema_period=9, market_open_seconds=mopen
    )

    # 4) BLOCK with MACD rising 10 bars on sideways data
    total += 1
    passed += run_case(
        "MACD rising too strict (10 bars) blocks on sideways data",
        flat, False,
        gate_seconds=15, rise_bars=3, macd_rise_bars=10,
        reclaim_ref="EMA", ema_period=9, market_open_seconds=mopen
    )

    # 5) ALLOW on VWAP reclaim with mild gates (clean uptrend)
    total += 1
    passed += run_case(
        "VWAP reclaim mild gates allows (clean uptrend)",
        clean, True,
        gate_seconds=15, rise_bars=2, macd_rise_bars=1,
        reclaim_ref="VWAP", ema_period=9, market_open_seconds=mopen
    )

    print(f"\nSummary: {passed}/{total} checks matched expectations.")

if __name__ == "__main__":
    main()