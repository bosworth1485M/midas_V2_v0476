"""
Unit tests for SimpleBreakoutStrategy._passes_macd_gate()

Tests the MACD histogram rising filter which requires:
1. MACD histogram to be STRICTLY rising for N consecutive bars: hist[i] > hist[i-1]
2. MACD histogram to be positive (>0) at current bar
3. Sufficient data for N comparisons: i >= N+1

This filter helps confirm accelerating bullish momentum.
"""

import pytest
from midas_v2.strategy import SimpleBreakoutStrategy, StrategyParams, macd


def last_hist(closes, window=6):
    """
    Helper to extract last N histogram values for debugging test failures.
    
    Returns rounded histogram values for readability in assertions.
    """
    macd_line, signal, hist = macd(closes)
    return [round(h, 6) if h is not None else None for h in hist[-window:]]


class TestMACDGate:
    """Test suite for _passes_macd_gate method with deterministic cases."""

    def test_disabled_gate_always_true(self):
        """
        When require_macd_rise=False, the gate should always pass.
        
        This is a smoke test to ensure the filter can be disabled.
        The actual histogram behavior doesn't matter.
        """
        params = StrategyParams(
            require_macd_rise=False
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Gentle uptrend - histogram behavior doesn't matter since filter is disabled
        closes = [100 + 0.2 * i for i in range(20)]
        
        i = len(closes) - 1
        
        # Should PASS: filter is disabled
        assert strategy._passes_macd_gate(closes, i) is True, (
            "Expected True when require_macd_rise=False (filter disabled)"
        )

    def test_passes_with_two_consecutive_rises(self):
        """
        When histogram rises strictly for 2 consecutive bars and is positive, should PASS.
        
        Pattern:
        - Warm-up with gentle uptrend to establish MACD baseline
        - Strong momentum burst to create unambiguous rising histogram
        
        This represents ideal entry conditions with strengthening momentum.
        """
        params = StrategyParams(
            require_macd_rise=True,
            macd_rise_bars=2
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Warm-up: establish MACD baseline with gentle uptrend
        closes = [100 + 0.2 * i for i in range(30)]
        
        # Strong momentum burst: unambiguous acceleration
        closes.extend([106.0, 108.0, 110.6, 112.0])
        
        i = len(closes) - 1
        
        # Should PASS: histogram rising for last 2 bars and positive
        assert strategy._passes_macd_gate(closes, i) is True, (
            f"Expected PASS with rising histogram. Last hist values: {last_hist(closes)}"
        )
        
        # Verify histogram is actually rising and positive
        _, _, hist = macd(closes)
        assert hist[i] is not None and hist[i] > 0, (
            f"Histogram should be positive: hist[{i}]={hist[i]}"
        )
        assert hist[i - 1] is not None and hist[i - 1] > 0, (
            f"Previous histogram should be positive: hist[{i-1}]={hist[i-1]}"
        )
        assert hist[i] > hist[i - 1], (
            f"Histogram should be strictly rising: "
            f"hist[{i}]={hist[i]:.6f} > hist[{i-1}]={hist[i-1]:.6f}"
        )

    def test_histogram_rises_then_dips_fails(self):
        """
        When histogram rises then dips (momentum weakens), should FAIL.
        
        Pattern:
        - Warm-up with gentle uptrend
        - Acceleration phase
        - STRONG DIP at the end -> histogram definitively declines
        
        The gate requires STRICTLY rising (hist[i] > hist[i-1]), so any dip fails.
        Uses strong explicit price dip to ensure deterministic histogram decline.
        """
        params = StrategyParams(
            require_macd_rise=True,
            macd_rise_bars=2
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Warm-up
        closes = [100 + 0.2 * i for i in range(30)]
        
        # Acceleration
        closes.extend([106.0, 108.0, 110.5])
        
        # Strong DIP: price drops significantly to force histogram decline
        closes.extend([111.0, 110.0])
        
        i = len(closes) - 1
        
        # Should FAIL: histogram is not strictly rising at the end
        assert strategy._passes_macd_gate(closes, i) is False, (
            f"Expected FAIL when histogram dips. Last hist values: {last_hist(closes)}"
        )
        
        # Verify histogram actually declined
        _, _, hist = macd(closes)
        if hist[i] is not None and hist[i - 1] is not None:
            hist_i = round(hist[i], 6)
            hist_i_minus_1 = round(hist[i - 1], 6)
            assert hist_i <= hist_i_minus_1, (
                f"Histogram should decline but still rising: "
                f"hist[{i}]={hist_i} vs hist[{i-1}]={hist_i_minus_1}. "
                f"Last hist: {last_hist(closes)}"
            )

    def test_one_decline_within_three_fails(self):
        """
        When histogram declines at any point in the required sequence, should FAIL.
        
        Pattern:
        - Warm-up with gentle uptrend
        - Mixed pattern with a mid-sequence dip that breaks consecutive rise
        
        With macd_rise_bars=3, need 3 consecutive rises. The dip breaks this.
        """
        params = StrategyParams(
            require_macd_rise=True,
            macd_rise_bars=3
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Warm-up
        closes = [100 + 0.3 * i for i in range(30)]
        
        # Pattern with mid-sequence dip: rise, rise, DIP, rise
        # The dip at 110.2 breaks the consecutive rise requirement
        closes.extend([109.0, 111.0, 110.2, 113.0])
        
        i = len(closes) - 1
        
        # Should FAIL: the dip breaks consecutive rise for 3 bars
        assert strategy._passes_macd_gate(closes, i) is False, (
            f"Expected FAIL when histogram has a decline in sequence. "
            f"Last hist values: {last_hist(closes)}"
        )
        
        # Verify the decline actually occurred
        _, _, hist = macd(closes)
        # The pattern should prevent hist[i] > hist[i-1] > hist[i-2] > 0 all being true
        if all(h is not None for h in [hist[i], hist[i-1], hist[i-2]]):
            is_rising_three = (hist[i] > hist[i-1] > hist[i-2] > 0)
            assert not is_rising_three, (
                f"Expected histogram to have at least one decline in last 3 bars, "
                f"but found continuous rise. Last hist: {last_hist(closes)}"
            )

    def test_insufficient_warmup_fails_by_index(self):
        """
        When i < (macd_rise_bars + 1), there's insufficient data for comparisons.
        
        With macd_rise_bars=3, we need i >= 4 to have indices [i-3, i-2, i-1, i]
        for 3 comparisons. At i=2, we only have 3 points total (indices 0,1,2),
        which is insufficient.
        
        This is an explicit early-index rule check.
        """
        params = StrategyParams(
            require_macd_rise=True,
            macd_rise_bars=3  # N = 3
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Very short closes - not enough for proper MACD + comparisons
        closes = [100.0, 101.0, 102.0, 103.0]
        
        i = 2  # i < N+1 (2 < 4) -> guaranteed False by early-index check
        
        # Should FAIL: insufficient data (i < macd_rise_bars + 1)
        assert strategy._passes_macd_gate(closes, i) is False, (
            f"Expected FAIL when i={i} < macd_rise_bars+1={params.macd_rise_bars+1}"
        )

    def test_long_flat_then_accel_requires_recent_rise_only(self):
        """
        When price is flat initially then accelerates, only recent N bars matter.
        
        Pattern:
        - Long flat consolidation (weak/zero histogram initially)
        - Recent acceleration creates rising positive histogram
        
        This proves the gate only checks the last N bars, not the entire history.
        """
        params = StrategyParams(
            require_macd_rise=True,
            macd_rise_bars=2
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Long flat consolidation followed by strong acceleration
        closes = [100.0] * 35  # Flat
        closes.extend([102.0, 104.0, 106.0])  # Strong acceleration
        
        i = len(closes) - 1
        
        # Should PASS: recent N bars are rising and positive
        assert strategy._passes_macd_gate(closes, i) is True, (
            f"Expected PASS when recent bars show rising histogram after flat period. "
            f"Last hist values: {last_hist(closes)}"
        )

    def test_rising_but_histogram_negative_fails(self):
        """
        When prices rise but MACD histogram is still negative (bearish), should FAIL.
        
        Pattern (Approach A - preferred):
        - Strong initial downtrend creates deeply negative histogram
        - Very small recent rises (tiny upticks) keep histogram at or below zero
        
        The gate requires hist[i] > 0, so negative/zero histogram fails even if rising.
        Uses minimal upticks to ensure histogram stays non-positive.
        """
        params = StrategyParams(
            require_macd_rise=True,
            macd_rise_bars=2
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Strong downtrend to create deeply negative histogram
        closes = [120 - 0.8 * i for i in range(50)]
        
        # Very small upticks - not enough to push histogram positive
        closes.extend([80.0, 80.1])
        
        i = len(closes) - 1
        
        # Should FAIL: histogram must be positive (> 0)
        assert strategy._passes_macd_gate(closes, i) is False, (
            f"Expected FAIL when histogram is negative despite rising prices. "
            f"Last hist values: {last_hist(closes)}"
        )
        
        # Verify histogram is actually non-positive
        _, _, hist = macd(closes)
        if hist[i] is not None:
            assert hist[i] <= 0, (
                f"Expected non-positive histogram but got positive: "
                f"hist[{i}]={hist[i]:.6f}. Last hist: {last_hist(closes)}"
            )

    def test_borderline_noise_requires_strict_increase(self):
        """
        When prices show tiny fluctuations (noise), strict increase must hold.
        
        Pattern:
        - Gentle uptrend to establish baseline
        - Tiny rise followed by tiny dip (noise/consolidation)
        
        The gate requires STRICT inequality (hist[i] > hist[i-1]), so even
        tiny violations fail. This tests sensitivity to small price movements.
        """
        params = StrategyParams(
            require_macd_rise=True,
            macd_rise_bars=2
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Warm-up with gentle uptrend
        closes = [100 + 0.2 * i for i in range(30)]
        
        # Tiny rise then tiny dip (noise)
        closes.extend([106.0, 106.4, 106.39])
        
        i = len(closes) - 1
        
        # Should FAIL: the tiny dip violates strict increase requirement
        assert strategy._passes_macd_gate(closes, i) is False, (
            f"Expected FAIL when tiny price dip breaks strict increase. "
            f"Last hist values: {last_hist(closes)}"
        )
