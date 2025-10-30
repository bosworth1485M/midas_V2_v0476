# Profitability Playbook — Cameron + Add‑ons (v0.3.9 draft)
**Date:** 2025-09-07  
**Goal:** Raise realized profitability while preserving (or improving) baseline win‑rate and keeping drawdowns small.

---

## 0) TL;DR (what actually helps most)
1. **Universe hygiene + opening RVOL gate** → fewer low‑quality trades, better PnL stability.  
2. **D_strict + E_dip together** → D is the safety anchor; E adds selective high‑R:R wins.  
3. **Selective 1‑second confirmation** at the trigger (break/reclaim) → fewer false breaks on choppy opens.  
4. **Risk‑based position sizing** (fixed $R per trade, strict caps) → smoother equity, shallower drawdowns.  
5. Optional add‑on scenarios (ORB, VWAP reclaim fade, BOPB, Parabolic reversal, MDBO, News scalps) — gated by RVOL/trend.

---

## 1) Cameron baselines you’re using
### 1.1 Scenario D_strict (anchor)
- **Intent:** conservative momentum breakout with confirmations.  
- **Typical guardrails:** gate=5 min, min_pm_vol≥30k, price $1–20, gap 10–40%, EMA+VWAP confirm, MACD rising (rise_bars≈2), TP=2.0%, SL=2.5%.  
- **Observed (Aug):** ≈63.29% WR, +167.57 PnL over 2025‑08‑05→2025‑08‑31 (79 trades, 50/29 W/L).

### 1.2 Scenario E_dip (complement to D)
- **Intent:** micro pullback / dip to EMA or VWAP, then **reclaim** with MACD rising.  
- **Typical guardrails:** gate=15, rise_bars=3, min_pm_vol≥50k, TP=2.0%, SL=2.5%, reclaim_ref=EMA.  
- **Observed (Aug):** ≈52.07% WR, +145.03 PnL (lower WR than D, but strong winners).

### 1.3 Hygiene & RVOL
- **Hygiene filters:** exclude warrants/units/leveraged ETFs (e.g., symbols ending .WS, .U, UVXY/UVIX/VIXI/SOXS/SSG/FNGD), avoid China ADRs if desired.  
- **Opening RVOL gate:** ratio of first 10–15 min volume vs prior day ≥ 1.5 (tunable). Improves quality; keep off by default until after regression.

---

## 2) Add‑on strategies (outside Cameron) that can lift PnL
Below: **Preconditions → Entry → Exit/Risk → Knobs → Wiring**

### 2.1 Opening Range Breakout (ORB) — add only with RVOL/trend
- **Pre:** price $1–20, gap≥5–10%, RVOL_open≥1.5, EMA slope up, (opt) MACD line>signal.  
- **Entry:** break/close above 1–5 min opening range; optional 1‑sec hold above level.  
- **Exit/Risk:** SL at OR mid/low or ATR fraction; TP 1.5–2.5% or EMA trail.  
- **Knobs:** OR minutes {{1,3,5}}, RVOL gate {{off,1.2,1.5,2.0}}, TP/SL grid.  
- **Wiring later:** scenario F_orb with orb_minutes, min_rvol_open, ema_slope_up, macd_confirm.

### 2.2 VWAP reclaim “fade” (counter‑trend, conservative)
- **Pre:** extension from VWAP (e.g., +0.2–0.5%), mid‑day, no fresh spike.  
- **Entry:** wait for tag + reclaim of VWAP; MACD upturn on entry bar.  
- **Exit/Risk:** tight SL just beyond reclaim; TP 1.0–1.5% or VWAP trail.  
- **Knobs:** reclaim tolerance bps, time‑of‑day gate.  
- **Wiring:** G_vwap_fade with vwap_reclaim=True, fade_mode=True, gate_minutes≥15.

### 2.3 Parabolic reversal (exhaustion → reclaim)  
- **Pre:** 3+ stacked wide greens / far above EMA/VWAP; volume climax/wicks.  
- **Entry:** pullback to EMA/VWAP, then reclaim with MACD histogram turning up.  
- **Exit/Risk:** SL a few ticks below reclaim low; TP 1.5–2.5% or EMA trail.  
- **Knobs:** extension multiple, reclaim_ref, MACD rise bars.  
- **Wiring:** H_parabolic_rev with extension_mult, reclaim_ref, rise_bars.

### 2.4 Breakout‑Pullback / Retest (BOPB)
- **Pre:** clear pivot (≥3 touches), EMA(9) > VWAP, trend up.  
- **Entry:** break → pullback → tag level → small reversal close above level.  
- **Exit/Risk:** SL under retest low; TP 2–3% or next shelf.  
- **Knobs:** min touches, buffer bps, time cap.  
- **Wiring:** I_bopb with pivot_retest=True, buffer_bps, time_cap_min.

### 2.5 Multi‑Day Breakout (MDBO) — intraday trigger at daily level
- **Pre:** daily resistance within 1–2% above open; RVOL≥1.2; clean tape.  
- **Entry:** intraday break + hold above PDH/range‑high; EMA slope up.  
- **Exit/Risk:** SL back inside level; TP 2–3% or partial + trail.  
- **Knobs:** daily buffer bps, intraday hold seconds.  
- **Wiring:** J_mdbo with daily_breakout_ref, buffer_bps, hold_seconds.

### 2.6 News/PR momentum scalps (NPR)
- **Pre:** headline/spike proxy via volume/range σ.  
- **Entry:** first reclaim after spike with EMA cross up + MACD line>signal; 1‑sec confirm helpful.  
- **Exit/Risk:** tight SL; TP 0.8–1.5%; flat by EOD.  
- **Knobs:** spike thresholds, confirm seconds, TP/SL.  
- **Wiring:** K_news with spike_filter=True, confirm_seconds=3–5.

---

## 3) Cross‑cutting boosters
### 3.1 1‑second confirmation (selective)
Use seconds only at the trigger (break/reclaim hold for 3–5s). Lowers false breaks, slightly fewer fills.

### 3.2 Risk‑based position sizing (documented; implement later)
- Keeps losses consistent (e.g., $50/trade). Improves equity smoothness and often expectancy.  
- See RISK_BASED_POSITION_SIZING_GUIDE_v0.3.9-draft.pdf for math, caps, and rollout plan.

### 3.3 Scenario router (D→E precedence; one position per symbol)
Avoids double‑dipping capital on the same symbol; improves risk use without changing signals.

---

## 4) Rollout plan (safe sequence)
1) September regression — D_strict using your classic run_range_and_summarize.py.  
2) Run E_dip on the same range; compare WR/PnL/expectancy.  
3) Turn on hygiene filter + RVOL gate (off → on) and rerun; expect fewer losers.  
4) Optional: add 1‑second confirm on the trigger only; rerun.  
5) When stable, adopt risk‑based sizing (fixed $R; strict caps).  
6) Trial one add‑on scenario (most often ORB with RVOL gate) as F_orb gated by trend/RVOL.

Tag every stable checkpoint so you can always restore in one command.

---

## 5) Metrics to monitor
- WR, Expectancy, Total PnL, Max DD, Avg hold time, Max favorable/adverse excursion.  
- Per‑symbol overlap between scenarios; router “skips” (if/when enabled).  
- Trade count vs WR after hygiene/RVOL/seconds changes.

---

## 6) Commands (pure Python; no chaining)
Single day
```
python scripts\run_day_simple.py --date 2025-08-05 --scenario D
python scripts\summarize_results.py --date 2025-08-05
```

Range (August/September examples)
```
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario D
python scripts\run_range_and_summarize.py --start 2025-09-01 --end 2025-09-30 --scenario D
python scripts\show_latest_range.py --root out\auto --scenario D
```

Viewer
```
python scripts\view_results.py --date 2025-09-02 --scenario D --preview 20 --top 5
```

---

## 7) Risks & gotchas
- ORB and counter‑trend fades can underperform in chop; keep RVOL/trend gates.  
- Seconds data adds slippage risk; use only at the trigger.  
- Don’t turn on multiple new features at once; A/B each change.

---

## 8) Where to file this
Docs\versions\5. version v0.3.8-2025-09-07-envfix\ or  
Docs\versions\6. version v0.3.9 plans\ (your choice).
