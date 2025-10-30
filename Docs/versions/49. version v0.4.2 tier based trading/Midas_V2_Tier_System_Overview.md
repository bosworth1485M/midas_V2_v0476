# Midas_V2 — Tier System Overview (A / B / C)

## ⚙️ Overview
The **tier system** in Midas_V2 dynamically adjusts trade size based on the **confidence level** of each setup.  
Each trade is assigned to a **Tier (A, B, or C)** by the Risk Manager depending on catalyst quality, RVOL strength, and other confirmations.

---

## 🔸 Base Risk
**`base_risk_usd = 35`**

Every trade starts here — $35 risk (amount you are willing to lose if stop-loss hits).

---

## 🔹 Tier Multipliers (Confidence Map)

| Tier | Meaning | Confidence | Risk Multiplier | Effective Risk (Base × Multiplier) |
|------|----------|-------------|-----------------|------------------------------------|
| **A** | High confidence | “A-grade setup” — strong catalyst + high RVOL | 1.4 | $49 (capped by `max_per_trade_risk_usd = 50`) |
| **B** | Normal confidence | Default / most trades | 1.0 | $35 |
| **C** | Low confidence | Weak setups, low RVOL, marginal catalysts | 1.0 (neutralized for safety) | $35 |

---

## 🔸 How the Software Chooses a Tier

Internally, the backtester builds a `tier_ctx` dictionary for each trade:

```python
tier_ctx = {
    "news_score": 3.0,
    "min_rvol_open": 2.4,
    "symbol": "MD",
}
```

Then it evaluates `tier_rules` from your configuration:

```json
"tier_rules": {
  "A": {"news_min_score": 3, "min_rvol_open": 2.6},
  "B": {"news_min_score": 3, "min_rvol_open": 2.0},
  "C": {"news_min_score": 1, "min_rvol_open": 1.5}
}
```

The system picks the **highest** tier whose rules are satisfied.

**Example:**  
- If `score=3`, `RVOL=2.7` → **Tier A**  
- If `score=3`, `RVOL=2.2` → **Tier B**  
- If `score=1.5` → **Tier C**

---

## 🔸 Trade Sizing After Tier Selection

Once a tier is chosen, the software calculates risk per trade:

```python
risk_usd = min(base_risk_usd * confidence_map[tier], max_per_trade_risk_usd)
```

**Examples:**
- Tier A → `min(35 * 1.4, 50)` = **$49**
- Tier B → `35 * 1.0` = **$35**
- Tier C → `35 * 1.0` = **$35** (neutral)

---

## 🔸 Why the Tier System Matters

It allows controlled, logic-based position sizing:
- **Bet more** when setup odds are higher (A-tier).
- **Keep risk normal** when confidence is moderate (B-tier).
- **Limit exposure** or skip weak setups (C-tier).

---

## 🔒 Current State (v0.4.1 — Stable)
- Tiers A/B/C logic exists in `sizing.py` and `backtester.py`.
- Currently, only **RVOL ≥ 2.6** qualifies for Tier A.
- All recent trades (Aug-05→07) classified as **Tier B** ($35 risk).
- Profit baseline: **+13.93 USD total** — stable and safe.
