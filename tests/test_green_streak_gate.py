"""
Unit tests for SimpleBreakoutStrategy._passes_price_rise_gate()

Tests the price rise gate which requires:
1. Consecutive bars with STRICTLY rising closes: bars[i-k].c > bars[i-k-1].c
2. Optional minimum green body filter: (abs(c-o) / (h-l)) >= green_body_min

This gate ensures we only enter during clear upward price momentum.
"""

import pytest
from midas_v2.strategy import SimpleBreakoutStrategy, StrategyParams, Bar


def mk_bar(t, o, c, rng=1.0, vol=1000):
    """
    Build a Bar with exact range = rng, centered around midpoint of o and c.
    Requires rng >= abs(c - o). Then body_pct = abs(c - o) / rng exactly.
    """
    assert rng >= abs(c - o), f"rng={rng} must be >= abs(c-o)={abs(c-o)}"
    mid = (o + c) / 2.0
    h = mid + rng / 2.0
    l = mid - rng / 2.0
    return Bar(t, o, h, l, c, vol)


class TestGreenStreakGate:
    """Test suite for _passes_price_rise_gate method with deterministic cases."""

    def test_disabled_gate_always_true(self):
        """
        When rise_bars=0, the gate is effectively disabled and should always pass.
        
        Even with green_body_min set, if rise_bars=0, no checks are performed.
        """
        params = StrategyParams(
            rise_bars=0,
            green_body_min=0.22
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Mixed sequence with red bars and dojis - doesn't matter
        bars = [
            mk_bar(0, 100, 101, rng=1.0),   # Green
            mk_bar(1, 101, 100, rng=1.0),   # Red
            mk_bar(2, 100, 100, rng=1.0),   # Doji
            mk_bar(3, 100, 99, rng=1.0),    # Red
        ]
        
        i = len(bars) - 1
        
        # Should PASS: gate is disabled
        assert strategy._passes_price_rise_gate(bars, i) is True, (
            "Expected True when rise_bars=0 (gate disabled), regardless of bar pattern"
        )

    def test_three_strict_rising_greens_pass(self):
        """
        When last 3 bars have strictly rising closes (c[i] > c[i-1]), should PASS.
        
        Pattern: Each bar closes higher than the previous bar.
        Gate requires STRICT inequality (>), not (>=).
        """
        params = StrategyParams(
            rise_bars=3,
            green_body_min=0.0
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Build sequence with strictly rising closes on last 3 bars
        bars = [
            mk_bar(0, 100, 100.5, rng=1.0),  # Setup bar
            mk_bar(1, 100, 101, rng=1.0),    # Close: 101
            mk_bar(2, 101, 102, rng=1.0),    # Close: 102 (> 101) ✓
            mk_bar(3, 102, 103, rng=1.0),    # Close: 103 (> 102) ✓
            mk_bar(4, 103, 104, rng=1.0),    # Close: 104 (> 103) ✓
        ]
        
        i = len(bars) - 1  # i=4, checking last 3 bars (indices 2,3,4)
        
        # Should PASS: 3 consecutive strictly rising closes
        assert strategy._passes_price_rise_gate(bars, i) is True, (
            "Expected True for 3 rising greens with strictly rising closes: 102 < 103 < 104"
        )

    def test_one_red_bar_in_last_three_fails(self):
        """
        When one bar in the last 3 has close <= previous close, should FAIL.
        
        Pattern: Two rising greens, then one red (or flat) bar.
        Gate requires ALL bars in the window to have strictly rising closes.
        """
        params = StrategyParams(
            rise_bars=3,
            green_body_min=0.0
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Last 3 bars: one is red (close < previous close)
        bars = [
            mk_bar(0, 100, 100.5, rng=1.0),  # Setup bar
            mk_bar(1, 100, 101, rng=1.0),    # Close: 101
            mk_bar(2, 101, 102, rng=1.0),    # Close: 102 (> 101) ✓
            mk_bar(3, 102, 103, rng=1.0),    # Close: 103 (> 102) ✓
            mk_bar(4, 103, 102.5, rng=1.0),  # Close: 102.5 (< 103) ✗ RED BAR
        ]
        
        i = len(bars) - 1  # i=4, checking last 3 bars (indices 2,3,4)
        
        # Should FAIL: bar at index 4 has close < previous close
        assert strategy._passes_price_rise_gate(bars, i) is False, (
            "Expected False when one bar in last 3 has close <= previous close (red bar)"
        )

    def test_doji_like_bodies_fail_when_body_min_enforced(self):
        """
        When closes are strictly rising but body_pct < green_body_min, should FAIL.
        
        Pattern: Strictly rising closes, but one bar has a very small body
        (doji-like), failing the green_body_min filter.
        
        This tests the body size filter which rejects bars with small real bodies
        relative to their full range.
        """
        params = StrategyParams(
            rise_bars=3,
            green_body_min=0.22  # Require at least 22% body
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Last 3 bars with strictly rising closes BUT one has tiny body
        bars = [
            mk_bar(0, 100, 100.5, rng=1.0),    # Setup bar
            mk_bar(1, 100, 101, rng=1.0),      # Close: 101, body_pct = 1.0 (100%) ✓
            mk_bar(2, 101, 102, rng=1.0),      # Close: 102, body_pct = 1.0 (100%) ✓
            mk_bar(3, 102, 103, rng=1.0),      # Close: 103, body_pct = 1.0 (100%) ✓
            mk_bar(4, 103, 104, rng=5.0),      # Close: 104, body_pct = 1.0/5.0 = 0.20 (20%) ✗
        ]
        
        i = len(bars) - 1  # i=4, checking last 3 bars (indices 2,3,4)
        
        # Should FAIL: last bar has body_pct = 0.20 < 0.22 (green_body_min)
        assert strategy._passes_price_rise_gate(bars, i) is False, (
            "Expected False due to doji body < green_body_min: "
            "bar at i=4 has body_pct=0.20 < 0.22"
        )

    def test_rising_with_body_threshold_plus_epsilon_passes(self):
        """
        When body_pct is slightly above green_body_min, should PASS.
        
        This tests float-safety: we use body_pct = threshold + epsilon (0.0001)
        to avoid floating-point precision issues that could cause false failures.
        
        The filter uses >= comparison, so threshold + epsilon should safely pass.
        """
        params = StrategyParams(
            rise_bars=2,
            green_body_min=0.22  # Require at least 22% body
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Last 2 bars with body_pct = 0.2201 (slightly above 0.22)
        # Use epsilon = 0.0001 to ensure safe clearance above threshold
        # body_pct = abs(c-o)/rng, so for body_pct=0.2201, set abs(c-o)=0.2201 and rng=1.0
        bars = [
            mk_bar(0, 100, 100.5, rng=1.0),          # Setup bar
            mk_bar(1, 100, 101, rng=1.0),            # Close: 101, body_pct = 1.0 ✓
            mk_bar(2, 101, 101.2201, rng=1.0),       # Close: 101.2201, body_pct = 0.2201 ✓
            mk_bar(3, 101.2201, 101.4402, rng=1.0),  # Close: 101.4402, body_pct = 0.2201 ✓
        ]
        
        i = len(bars) - 1  # i=3, checking last 2 bars (indices 2,3)
        
        # Should PASS: both bars have body_pct = 0.2201 >= 0.22 (with epsilon safety margin)
        assert strategy._passes_price_rise_gate(bars, i) is True, (
            "Expected True when body_pct is threshold + epsilon (0.2201 >= 0.22)"
        )

    def test_boundary_index_too_early_fails(self):
        """
        When index is too early (not enough bars to check), should FAIL.
        
        With rise_bars=3 and only 2 bars total, look = min(3, 1) = 1.
        Even with look=1, we need to compare bars[1].c > bars[0].c.
        If they're equal (flat), the strict inequality fails.
        """
        params = StrategyParams(
            rise_bars=3,
            green_body_min=0.0
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Only 2 bars with equal closes (flat)
        bars = [
            mk_bar(0, 100, 100.5, rng=1.0),   # Close: 100.5
            mk_bar(1, 100.5, 100.5, rng=1.0), # Close: 100.5 (NOT > 100.5) ✗
        ]
        
        i = 1  # i=1, look=min(3,1)=1, checks bars[1].c > bars[0].c
        
        # Should FAIL: bars[1].c == bars[0].c, not strictly rising
        assert strategy._passes_price_rise_gate(bars, i) is False, (
            "Expected False when close is flat (not strictly rising): 100.5 == 100.5"
        )
        
        # Also test i=0 where look=min(3,0)=0 → look <= 0 → returns False
        i = 0
        assert strategy._passes_price_rise_gate(bars, i) is False, (
            "Expected False when i=0 and look=min(3,0)=0"
        )

    def test_longer_sequence_only_last_three_checked(self):
        """
        When rise_bars=3, only the last 3 bars are checked.
        
        Earlier bars can be red/doji/mixed - they don't affect the result.
        This proves the gate only examines the required window.
        """
        params = StrategyParams(
            rise_bars=3,
            green_body_min=0.0
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Long sequence with early noise, but last 3 bars are perfect
        bars = [
            # Early noise (should be ignored)
            mk_bar(0, 100, 99, rng=1.0),     # Red
            mk_bar(1, 99, 98, rng=1.0),      # Red
            mk_bar(2, 98, 98, rng=1.0),      # Doji
            mk_bar(3, 98, 97, rng=1.0),      # Red
            mk_bar(4, 97, 96, rng=1.0),      # Red
            # Last 3 bars: strictly rising greens
            mk_bar(5, 96, 101, rng=5.0),     # Close: 101
            mk_bar(6, 101, 102, rng=1.0),    # Close: 102 (> 101) ✓
            mk_bar(7, 102, 103, rng=1.0),    # Close: 103 (> 102) ✓
            mk_bar(8, 103, 104, rng=1.0),    # Close: 104 (> 103) ✓
        ]
        
        i = len(bars) - 1  # i=8, checking last 3 bars (indices 6,7,8)
        
        # Should PASS: only the last 3 bars matter, and they're all strictly rising
        assert strategy._passes_price_rise_gate(bars, i) is True, (
            "Expected True for 3 rising greens when last 3 bars are strictly rising, "
            "regardless of earlier bars (102 < 103 < 104)"
        )

    def test_mixed_body_sizes_all_pass_min(self):
        """
        When all bars meet green_body_min but have different body sizes, should PASS.
        
        This tests that the filter correctly handles varying body percentages
        as long as all meet the minimum threshold.
        
        Uses epsilon = 0.0001 for the threshold bar to ensure float-safe comparison.
        """
        params = StrategyParams(
            rise_bars=3,
            green_body_min=0.25  # Require at least 25% body
        )
        strategy = SimpleBreakoutStrategy(params)
        
        # Last 3 bars with different body sizes, all >= 0.25
        # body_pct = abs(c-o)/rng
        # For threshold bar (0.25), use 0.2501 for float safety
        bars = [
            mk_bar(0, 100, 100.5, rng=1.0),       # Setup
            mk_bar(1, 100, 101, rng=1.0),         # Close: 101, body_pct = 1.0 (100%) ✓
            mk_bar(2, 101, 102, rng=2.0),         # Close: 102, body_pct = 1.0/2.0 = 0.50 ✓
            mk_bar(3, 102, 103, rng=3.0),         # Close: 103, body_pct = 1.0/3.0 = 0.333 ✓
            mk_bar(4, 103, 104.0040, rng=4.0),    # Close: 104.0040, body_pct = 1.0040/4.0 = 0.2510 ✓
        ]
        
        i = len(bars) - 1  # i=4, checking last 3 bars (indices 2,3,4)
        
        # Should PASS: all bars have body_pct >= 0.25 and strictly rising closes
        assert strategy._passes_price_rise_gate(bars, i) is True, (
            "Expected True when all bars meet green_body_min with varying body sizes: "
            "0.50, 0.333, 0.2510 all >= 0.25"
        )
