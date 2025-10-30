# Complete Catalyst Logic and Next Steps (v0.3.17)
*Updated with Definition of Wired Scenarios*

## Header & Version Tagging
**v0.3.17**: Catalyst + Opening RVOL integration plan, with denylist, active-universe workflow, catalyst scoring system, and clarification on “wired scenarios.”  
**v0.3.16** is already tagged and pushed to GitHub.

---

## 1) Where We Stand (v0.3.16 Recap)
- **Anchor Scenarios**
  - Scenario **D_strict**: EMA+VWAP+MACD, gate=5, TP=2.0 / SL=2.5, min_pm_vol=30k.  
    → In **August 2025 multi-day tests**: ~63% WR, +167.57 PnL.  
    → In **replay & September validation tests**: much lower WR, sometimes 30–40%.  
    ⚠️ D is therefore the **reference anchor**, not a guaranteed high-WR system.  
  - Scenario **E_dip**: dip reclaim + EMA+VWAP+MACD, gate=15, TP=2.0 / SL=2.5, min_pm_vol=50k.  
    → August 2025: ~52% WR, +145.03 PnL.  
- **Catalyst Module Added**
  - `scripts/enrich_universe_catalyst.py` (Polygon news scoring, A–C scale).
  - Raw top-gappers retained separately; catalyst universes built under `data/catalyst/` with audits.  
- **Baseline Policy**
  - A-grade (score ≥2) forms the backbone; B-grade (score=1) only as filler if needed.
  - Always confirm with EMA/VWAP/MACD.

---

## 2) Fourteen Phases – Chronological Order (Focus → Later)

**Active / Immediate (v0.3.17)**  
1. Catalyst scoring rules (A backbone, B filler).  
2. Apply denylist (`data/denylist.txt`).  
3. Catalyst Top-N workflow (tight 3–5).  
4. Active universe file (`data/universe_active.txt`).  
5. Opening RVOL gate (≥1.5 first 10–15 min).  
6. Run D, then B, then E across Aug → Sep.  

**Next Tier (after v0.3.17)**  
7. Router logic (D>E precedence).  
8. Advanced trade logic (multi-trade, 1s bars).  
9. Adaptive sizing (expectancy/Kelly-lite).  
10. Broker adapter layer (Alpaca/Lightspeed/IBKR).  

**Already Completed Foundations**  
11. Core backtester implemented (scenarios A–E wired).  
12. Scenarios tuning (D strict, E dip).  
13. Risk management (per-trade, daily cap, EOD flatten).  
14. Documentation & Git discipline.  

Legend: ✅ Done | 🟡 In progress | 🔲 Not started

---

## 3) Continuation Sequence for v0.3.17
(Top-N → Denylist → Active Universe → RVOL → Run D/B/E across Aug & Sep).  
*See previous doc versions for detailed steps.*  

---

## 4) Checklist for v0.3.17
- [ ] Finalize catalyst scoring policy (A backbone, B filler only).  
- [ ] Implement opening RVOL gate (≥1.5 for 10–15 min).  
- [ ] Apply daily Top-N (3–5) catalyst tickers.  
- [ ] Apply denylist (`data/denylist.txt`) during universe build.  
- [ ] Write active universe (`data/universe_active.txt`) each day.  
- [ ] Run validation tests for D, then B, then E (Aug → Sep).  
- [ ] Refresh `Docs/DEV_GUIDE.md` and commit.  
- [ ] Tag & push: `v0.3.17-catalyst-rvol`.  

---

## 5) Commands (One-Liners)
*(same as before; omitted here for brevity in this summary)*  

---

## 6) Reminder on Testing Scale
⚠️ To truthfully claim a win rate >60%, we must validate over **hundreds of trading days**. Results from August or September alone are not enough; they only provide directional hints.  

---

## 7) Catalyst Scoring System
- **Score 3 (A-grade)**: Strong catalyst (earnings, FDA approval, high-impact PR). Clean gapper, $1–20, high RVOL. → Preferred backbone.  
- **Score 2 (B-grade)**: Moderate catalyst (analyst coverage, partnership). Some volume/price action. → Used as filler if Top-N is too short.  
- **Score 1 (C-grade)**: Weak/unclear catalyst, hype-only, or irrelevant. → Normally excluded.  
- **Score 0 / Denylist**: Excluded outright — Chinese ADRs, OTC, garbage tickers, or anything not Cameron-style.  

---

## 8) Definition of “Wired Scenarios”  
When this document says scenarios A–E are “wired,” it does **not** mean they are validated or profitable. It means:  
- The scenarios are **implemented in code** and can be run end-to-end.  
- Each scenario has a parameter set (EMA/VWAP, MACD, dip reclaim, TP/SL, etc.).  
- They exist as a **test harness** — allowing us to measure WR and PnL as we add filters (catalysts, RVOL, denylist, router).  

⚠️ Low win rates do **not** invalidate the wiring — they show us that wiring alone is not enough. The purpose of v0.3.17 and beyond is to add the selective layers (catalysts, denylist, RVOL, etc.) that can lift WR toward the ~60% target.  

---

## 9) Forward Reminders
- Keep raw gappers separate from catalyst universes for A/B testing.  
- Anchor with D_strict; test B and E alongside.  
- Future phases (router, 1s candles, adaptive sizing) come only **after** v0.3.17 validation.  
