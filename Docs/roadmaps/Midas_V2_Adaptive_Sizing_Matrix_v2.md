# 📌 Adaptive Sizing Matrix (Draft for Midas_V2)

**Generated: 2025-09-20 22:15**

## Catalyst Score (backbone)
- **A-grade catalyst (score ≥2):** eligible for larger sizing.
- **B-grade catalyst (score = 1):** smaller sizing; only included if Top-N needs filling.
- **No catalyst:** skip.

## Confirm Alignment
- **Strong alignment:** EMA slope up, VWAP reclaim, MACD line > signal, 2–3 rising histogram bars, ≥3 rising green candles.
- **Medium alignment:** EMA+VWAP align, MACD line > signal but histogram flat.
- **Weak alignment:** only partial confirms; no size boost.

## Example Risk Buckets (assuming $50k account, base risk = $5k per trade)

| Catalyst | Confirms              | Risk Size | Notes |
|---|---|---:|---|
| A-grade | Strong (all aligns)   | **$8–10k** | “A+ setup” — larger bet, but never >2% equity. |
| A-grade | Medium                | **$5–6k**  | Standard size. |
| B-grade | Strong                | **$3–4k**  | Smaller bet, still worth taking. |
| B-grade | Medium                | **$2–3k**  | Only if Top-N needs filling. |
| None    | Any                   | **Skip**   | No catalyst, no trade. |

## Guardrails
- **Per-trade cap:** never risk >2% of equity on a single trade.
- **Daily stop:** stop trading after $–1,000 PnL.
- **Drawdown throttle:** if 3 consecutive losses, cut risk size by 50% for rest of day.

## Implementation Path
1. **Baseline config:** keep fixed size (e.g. $5k/trade) while you stabilize WR with Top-N + catalysts + confirms.
2. **Phase 1 adaptive:** add *2 buckets* only → Normal ($5k) vs. Large ($8k) for A+ setups.
3. **Phase 2 adaptive:** expand to full matrix above once stable.
4. **Future:** connect expectancy calculations (PnL per setup type) to auto-tune the buckets.
