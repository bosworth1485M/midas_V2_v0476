# Risk‑Based Position Sizing — Midas_V2 Guide (v0.3.9 draft)

**Purpose.** Explain *how* to size trades from a fixed dollar risk and how to extend it later with a conservative “Kelly‑lite” boost. No code changes now — this is a reference you can shelf and return to when the core is stable.

---

## 1) Why risk‑based sizing?
- Keeps losses consistent (e.g., ~$50 per losing trade) regardless of the ticker’s price.
- Automatically adapts the **share count** to your **stop distance**.
- Easier to budget a **daily max loss** (e.g., $1,000) and a **per‑trade risk** (e.g., $50).

---

## 2) Core definitions
- **Risk per trade (R):** the maximum dollars you’re willing to lose if the stop hits. Example: **R = $50**.
- **Entry price / Stop price:** planned fill and hard stop.
- **Stop distance per share:** `distance = |entry − stop|` (add a small buffer for slippage/fees).
- **Shares:** number of shares to buy so that `shares × distance ≲ R`.

**Base formula (long trades)**
```
distance_per_share = (entry − stop) + slippage_buffer
shares = floor( R / distance_per_share )
```
*(For shorts, use `(stop − entry)` for the distance.)*

**Example**
- Entry **$5.00**, stop **$4.88**, buffer **$0.02** ⇒ distance **$0.14**  
- R = **$50** ⇒ shares = `floor(50 / 0.14) = 357`  
- Notional ≈ **357 × $5.00 = $1,785**

---

## 3) Guardrails (recommended now)
Add these *caps* to avoid oversizing:
- **max_shares** — e.g., 5,000
- **max_notional** — e.g., $30,000
- **buying power cap** — shares must fit within `bp_remaining × leverage`
- **daily_max_loss** — stop trading or size down when remaining daily risk < R
- **min_size / skip rule** — if computed shares < 1, skip the trade (stop too tight for chosen R)
- **volatility sanity** — if ATR is huge vs price, optionally scale R down (ATR‑based factor)
- **hygiene filters** — price band 1–20, exclude illiquid/warrants/leveraged ETFs, spread/halts checks

**Putting it together (conceptual)**
```
shares = floor( R / (|entry − stop| + buffer) )
shares = min(shares, cap_by_max_shares, cap_by_notional, cap_by_buying_power)
if shares < 1: skip
```

---

## 4) Daily risk budgeting
If **daily_max_loss = $1,000** and **R = $50**: budget ≈ 20 full‑risk trades.  
Practical rules:
- Reduce R when drawdown > threshold (e.g., halve R after −$500).
- Stop trading for the day at **−$1,000** realized (or sooner if equity curve deteriorates).

---

## 5) “Kelly‑lite” (optional later)
Use a very small Kelly fraction to **tilt size** when expectancy looks better — but keep it conservative.

**Kelly fraction (simplified)**
```
f* = p − (1 − p) / b
where p = win rate, b = average win / average loss
```
Use **fractional Kelly**, e.g., **0.25×Kelly**, and clamp to `[0.5, 1.5]` around base R.

**Example**
- Suppose `p = 0.60`, `b = 1.0` ⇒ `f* = 0.20` (20% of capital in pure Kelly).
- Use 0.25× ⇒ **5%** equivalent tilt. In practice, just scale **R**:
```
R_effective = clamp( R_base × (1 + 0.05), R_min, R_max )
```
Keep **R_min/R_max** modest (e.g., $25 ≤ R ≤ $75) to avoid big swings.

**When to *not* boost**
- Fresh month / limited sample size
- After a drawdown day
- When spreads are wide or halts are frequent

---

## 6) Integration plan for Midas (later)
No code today. When you’re ready:
- **Config keys** (example)
```
risk: {
  per_trade_risk: 50,
  daily_max_loss: 1000,
  max_notional: 30000,
  max_shares: 5000,
  slippage_buffer: 0.02,
  kelly_fraction: 0.25,        # optional later
  kelly_enabled: false,
  r_min: 25, r_max: 75
}
```
- **Where it plugs in:** the order‑build step right before entry, using entry/stop and the caps.
- **Logging:** write computed shares, distance, effective R, and which caps limited size.
- **Backtests:** run A/B with sizing=“fixed shares” vs “risk‑based” on the same ranges to verify WR/PnL and drawdowns.

---

## 7) Testing checklist
- Unit‑test the sizing math (edge cases: tiny distance, caps binding, zero/negative values)
- Simulate a day with multiple trades to confirm daily_max_loss halts new entries
- Confirm short trades use proper `distance = stop − entry`
- Verify logs show (entry, stop, distance, shares, cap source)
- Regression run: compare Aug & Sep with risk‑based sizing **off** first (baseline), then **on**

---

## 8) Quick reference (cheat‑sheet)
- **shares** = `floor( R / (|entry − stop| + buffer) )`
- Apply **max_shares**, **max_notional**, **buying_power** caps
- **Skip** if shares < 1
- **Daily stop** at −$1,000 (example)
- Optional: **Kelly‑lite** tilt (small, clamped)

---

## 9) Q&A
**Q: Can I use this with multiple scenarios?**  
A: Yes — share a single risk budget and enforce “one position per symbol” across scenarios.

**Q: Does this change the signals/entries?**  
A: No — only the **size** changes.

**Q: Do I need 1‑sec data first?**  
A: No — sizing is independent of bar resolution. Keep the minute‑bar baseline.

**Q: When should I enable it?**  
A: After you finish September regression and tag a stable version.

---

*(Document only. Save under `Docs/versions/6. version v0.3.9 plans/` when convenient.)*
