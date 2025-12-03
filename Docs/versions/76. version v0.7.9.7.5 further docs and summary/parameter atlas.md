Here’s the Atlas as a self-contained Markdown document you can drop straight into your repo, e.g.:

Docs/PARAMETER_ATLAS_ScenarioB_v0.7.9.7.5.md

You don’t need to change anything—just save this text into a .md file.

# Parameter Atlas – Scenario B (v0.7.9.7.5)
## Use this to understand exactly what we are trading right now.

This document describes **all known knobs** used by Scenario B in the
`midas_V2_v0.4.7.9_working` branch, and **where they currently live**.

It is the “single page of truth” for this version, even though the
implementation is still spread across scanner scripts, strategy code,
and risk settings.

---

## 1. Scanner / Universe (topgappers)

These settings decide **which symbols even reach the strategy**.

From logs (2025-08-01) and scanner behavior:

- **Price band**  
  - `price_min`: **1.0**  
  - `price_max`: **20.0**  
  - Meaning: only stocks with price between **$1 and $20** at the open
    are considered.

- **Gap filter**  
  - `min_gap_pct`: **10.0**  
  - Meaning: only stocks that **open at least 10% above** the previous
    day’s close are considered gappers.
  - (There is no explicit max gap in this branch’s log, but there may be
    one in newer branches.)

- **Top-N by gap**  
  - `top`: **5**  
  - Meaning: after filtering by price and gap, we keep only the **top 5
    symbols ranked by gap %**. These are written to `universe_sample.txt`.

**Where these live today:**
- Implemented in `scripts/topgappers.py` and related scanner logic.
- Visible in logs like:
  - `price=[1.0..20.0]  min_gap=10.0%`
  - `[UNIVERSE] Trimmed to Top-5 symbols (from 24)`

**Effect:**  
Scenario B trades **small-cap gappers** in the $1–$20 range with at
least a 10% gap, using only the **top 5 gappers** each day.

---

## 2. Strategy – SimpleBreakoutStrategy (Scenario B)

These settings control **when and how we are allowed to enter a trade**
and what must be true about the stock and its price action.

They come from `StrategyParams` in `strategy.py` and are confirmed in:

- `[WHY] Using StrategyParams: { ... }` log line, and  
- The “RULES WE USED BEFORE TAKING THIS TRADE” block in the summary.

### 2.1 Timing and volume gates

- **gate_minutes**: **20**  
  - We **wait 20 minutes after the open** before any entries.
  - Purpose: avoid early open chaos.

- **min_pm_vol**: **30,000**  
  - Before the market opens, the stock must have traded at least
    **30,000 shares** premarket.
  - Purpose: avoid completely sleepy symbols.

- **min_rvol_open**: **2.0**  
- **rvol_open_minutes**: **15**  
  - In the **first 15 minutes**, today’s volume must be at least
    **2.0× yesterday’s** volume over the same number of minutes.
  - Purpose: ensure the stock is **unusually active today**, not just
    a quiet name with a random gap.

### 2.2 Green candle (“green streak”) rule

This is implemented via `_passes_price_rise_gate` in `strategy.py`.

- **rise_bars**: **3**  
- **green_body_min**: **0.22**

**Exact meaning:**

> We **require 3 recent green candles in a row.**  
> For each of those candles:
> - The close must be **higher than the previous candle’s close**, and  
> - The candle’s body must be **at least 22% of the full bar range**  
>   (no tiny doji candles).

If any one of those 3 bars fails (not green, not strong enough body),
**no entry**.

This is your **implemented green streak** rule.

### 2.3 MACD histogram rule

Implemented via `_passes_macd_gate` in `strategy.py`.

- **require_macd_rise**: **True**  
- **macd_rise_bars**: **2**

**Exact meaning:**

> The **MACD histogram** must be:
> - **Above zero** (bullish momentum), and  
> - **Rising for 2 bars in a row** (current histogram > previous histogram, twice).

If this condition fails, **no entry**, even if green candles and volume
conditions are satisfied.

### 2.4 Take profit and stop loss

- **tp_pct**: **2.0**  
  - Take profit at **+2.0%** above entry price.

- **sl_pct**: **2.5**  
  - Stop loss at **–2.5%** below entry price.

These define the **reward/risk** of each trade in this version.

### 2.5 Dip reclaim mode (OFF here)

- **dip_reclaim**: **False**

Dip-reclaim logic is present in `strategy.py` but is **disabled**
(`dip_reclaim=False`) for Scenario B in this branch. Basic breakout
mode is used.

**Where these live today:**

- `strategy.py` → `StrategyParams` dataclass.  
- Normalized into `norm_params` in backtester.  
- Values confirmed per trade in the summary block:
  > RULES WE USED BEFORE TAKING THIS TRADE

---

## 3. Risk / Safety

These settings control **how much money we are allowed to risk** per
trade and per day.

### 3.1 Per-trade risk (effective)

From the actual trades (MWYN, NAMM, BTAI):

- Risk amount per trade is around **$35**:
  - e.g., `Risk amount (USD): $34.99`

This is the **actual risk used** in this profile. Internally it comes
from the sizer and risk config (not yet fully inspected in this branch).

### 3.2 Max trades per symbol

- **max_trades_per_symbol**: **1**  
  - We allow only **one trade per symbol per day**.

### 3.3 Daily loss cap

- **daily_max_loss**: **1000.0**  
  - If total losses in a day reach **$1,000**, the system should stop
    trading for that day.

**Where these live today:**

- Passed into the backtester as part of settings / risk config.  
- Captured in `risk_snapshot` in `backtester.py`.  
- Shown in the summary under **RISK CALCULATION** and **Exact settings**.

---

## 4. Summary – What Scenario B is Trading (v0.7.9.7.5, this branch)

Putting everything together, this is the **current live profile** for
Scenario B in `midas_V2_v0.4.7.9_working`:

1. **Universe:**
   - Stocks priced between **$1 and $20**  
   - With an **opening gap ≥ 10%**  
   - We keep only the **Top-5 gappers** by percentage gap.

2. **Volume & timing filters:**
   - Wait **20 minutes** after the open before any entries.  
   - Require at least **30,000 shares** traded premarket.  
   - In the first **15 minutes**, today’s volume must be at least
     **2× yesterday’s** volume (RVOL ≥ 2.0).

3. **Price action (green streak):**
   - Require **3 consecutive green candles**:
     - Each one closes **higher than the previous close**.  
     - Each has a **strong body** (≥ 22% of the full bar range).

4. **MACD momentum:**
   - Require the **MACD histogram** to be:
     - **Above zero**, and  
     - **Rising for 2 histogram bars in a row**.

5. **Exits:**
   - Take profit at **+2.0%**, stop loss at **–2.5%**.

6. **Risk controls:**
   - Risk per trade is around **$35** in this profile.  
   - At most **1 trade per symbol per day**.  
   - Stop trading for the day if total losses reach **$1,000**.

---

## 5. How to use this atlas when testing

- Whenever you run:

  ```bash
  python scripts\run_range_and_summarize.py --start YYYY-MM-DD --end YYYY-MM-DD --scenario B


you can compare the per-trade summaries against this Atlas to confirm
nothing has silently changed.

If any future change adjusts a parameter (e.g. risk per trade, gap
rules, MACD bars, TP/SL), update this document and the config.

When designing the relational database and candle snapshot tooling:

Use this Atlas to define your schema (columns for these knobs).

Use per-trade snapshots to store the effective values used on
each trade.

This way, every trade, DB row, and candle snapshot can be traced back to
this single, human-readable description of Scenario B’s behavior.