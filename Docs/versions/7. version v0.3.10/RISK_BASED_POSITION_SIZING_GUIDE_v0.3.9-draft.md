# Risk-Based Position Sizing (v0.3.9 draft)
- shares = floor( R / (|entry - stop| + buffer) ); caps: max_shares, max_notional, buying power.
- Daily max loss; skip if shares < 1; optional fractional Kelly tilt later (clamped).
