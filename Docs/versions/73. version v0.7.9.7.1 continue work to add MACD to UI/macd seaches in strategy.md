Searches in visual studio for def macd, require_macd_rise and macd_rise_bars

def macd(series: List[float], fast=12, slow=26, signal=9):
    """
    Calculate MACD (Moving Average Convergence Divergence) indicator.
    
    MACD is a trend-following momentum indicator that shows the relationship between
    two moving averages of prices. It consists of:
    - MACD Line: Difference between fast and slow EMAs
    - Signal Line: EMA of the MACD line
    - Histogram: Difference between MACD line and signal line
    
    Args:
        series: List of prices (typically closing prices)
        fast: Period for fast EMA (default 12)
        slow: Period for slow EMA (default 26)
        signal: Period for signal line EMA (default 9)
    
    Returns:
        Tuple of (macd_line, signal_line, histogram) - all lists of Optional[float]
    
    Notes:
        - Positive histogram suggests bullish momentum
        - Rising histogram suggests strengthening momentum
        - MACD line crossing above signal line is a bullish signal
    """
    # Ensure slow > fast
    if slow < fast:
        fast, slow = slow, fast
    
    # Calculate fast and slow EMAs
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    
    # Calculate MACD line (difference between fast and slow EMAs)
    macd_line: List[Optional[float]] = [None] * len(series)
    for i in range(len(series)):
        if ema_fast[i] is None or ema_slow[i] is None:
            macd_line[i] = None
        else:
            macd_line[i] = float(ema_fast[i]) - float(ema_slow[i])
    
    # Calculate signal line (EMA of MACD line)
    signal_line = ema([x if x is not None else 0.0 for x in macd_line], signal)
    
    # Calculate histogram (difference between MACD line and signal line)
    hist: List[Optional[float]] = [None] * len(series)
    for i in range(len(series)):
        if macd_line[i] is None or signal_line[i] is None:
            hist[i] = None
        else:
            hist[i] = float(macd_line[i]) - float(signal_line[i])
    
    return macd_line, signal_line, hist


def _passes_macd_gate(self, closes: List[float], i: int) -> bool:
        """
        Check if MACD histogram shows rising momentum.
        
        When enabled, this requires the MACD histogram to be:
        1. Rising for N consecutive bars
        2. Above zero (positive momentum)
        
        This helps confirm that momentum is not only present but accelerating.
        
        Args:
            closes: List of closing prices
            i: Current bar index
        
        Returns:
            True if MACD requirements are met (or if filter is disabled)
        """
        # If filter is disabled, pass automatically
        if not self.p.require_macd_rise:
            return True
        
        n = int(self.p.macd_rise_bars or 0)
        
        # If no bars required or insufficient data, fail
        if n <= 0 or i < n + 1:
            return False
        
        # Calculate MACD components
        macd_line, signal_line, hist = macd(closes)
        
        # Check that histogram has been rising for N consecutive bars
        # and is currently positive
        for k in range(n):
            h_cur = hist[i - k]       # Current histogram value
            h_prev = hist[i - k - 1]  # Previous histogram value
            
            # Require: rising and positive
            if h_cur is None or h_prev is None or not (h_cur > h_prev and h_cur > 0):
                return False
        
        return True


@dataclass
class StrategyParams:
    """
    Configuration parameters for the breakout trading strategy.
    
    This class encapsulates all tunable parameters that control entry conditions,
    exit levels, and various confirmation filters for the trading strategy.
    """
    
    # Basic entry timing and risk management
    gate_minutes: int = 5  # Minimum number of minutes after market open before allowing entries
    tp_pct: float = 1.2    # Take profit percentage above entry price
    sl_pct: float = 2.7    # Stop loss percentage below entry price
    
    # Confirmation indicators (boolean toggles)
    vwap_confirm: bool = False  # Require VWAP confirmation for entry
    ema_confirm: bool = True    # Require EMA confirmation for entry
    macd_confirm: bool = False  # Legacy boolean MACD confirmation (for dip reclaim mode)
    
    # Price action requirements
    rise_bars: int = 2              # Number of consecutive rising price bars required
    green_body_min: float = 0.0     # Minimum real-body fraction per bar (0 = no filter)
    
    # Pre-market filters (optional)
    min_pm_vol: Optional[int] = None    # Minimum pre-market volume required
    reclaim_pmh: Optional[bool] = None  # Require reclaim of pre-market high
    
    # ========== Dip Reclaim Strategy Parameters ==========
    dip_reclaim: bool = False      # Enable dip-and-reclaim entry mode (alternative to basic breakout)
    reclaim_ref: str = "ema"       # Reference for reclaim check: "ema" or "vwap"
    min_dip_pct: float = 2.0       # Minimum percentage dip from swing high required
    min_reclaim_pct: float = 0.5   # Percentage above reference (EMA/VWAP) required to confirm reclaim
    ema_period: int = 5            # EMA period when using EMA as reclaim reference
    reclaim_buffer_bps: float = 0.0      # Extra buffer above reference in basis points (e.g., 5.0 = +0.05%)
    vwap_slope_bps: Optional[int] = None # Require VWAP slope >= this value in bps (optional filter)
    vwap_period_min: int = 1             # Minimum VWAP period (guard; VWAP is cumulative)
    
    # ========== Opening Relative Volume Filter (v0.3.21) ==========
    min_rvol_open: Optional[float] = None   # Minimum opening RVOL (e.g., 1.5 = 150% of yesterday's pace)
    rvol_open_minutes: int = 15             # Number of minutes to compare for RVOL calculation
    
    # ========== MACD Rising Filter (v0.4.x) ==========
    require_macd_rise: bool = False         # Enable explicit MACD histogram rising requirement
    macd_rise_bars: int = 0                 # Number of consecutive rising MACD histogram bars required




def _passes_macd_gate(self, closes: List[float], i: int) -> bool:
        """
        Check if MACD histogram shows rising momentum.
        
        When enabled, this requires the MACD histogram to be:
        1. Rising for N consecutive bars
        2. Above zero (positive momentum)
        
        This helps confirm that momentum is not only present but accelerating.
        
        Args:
            closes: List of closing prices
            i: Current bar index
        
        Returns:
            True if MACD requirements are met (or if filter is disabled)
        """
        # If filter is disabled, pass automatically
        if not self.p.require_macd_rise:
            return True
        
        n = int(self.p.macd_rise_bars or 0)
        
        # If no bars required or insufficient data, fail
        if n <= 0 or i < n + 1:
            return False
        
        # Calculate MACD components
        macd_line, signal_line, hist = macd(closes)
        
        # Check that histogram has been rising for N consecutive bars
        # and is currently positive
        for k in range(n):
            h_cur = hist[i - k]       # Current histogram value
            h_prev = hist[i - k - 1]  # Previous histogram value
            
            # Require: rising and positive
            if h_cur is None or h_prev is None or not (h_cur > h_prev and h_cur > 0):
                return False
        
        return True


