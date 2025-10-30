# Midas_V2 — v0.4.1 “Score‑Aware Prep (Stable)”

## Summary (What we did today)
- **Kept priority: maximum stability** (no extra risk today).
- Applied a **one‑line backtester patch** so the sizer becomes **score‑aware** (reads `news_min_score` from scenario).
- **Did not** loosen A‑tier RVOL. We **kept A‑tier at RVOL ≥ 2.6**, cap `$50`, `A=1.4`, `B=1.0`, `C=1.0`.
- Re‑ran **Aug‑05 → Aug‑07** multi‑day range to confirm behavior and totals.
- Current behavior: with RVOL ≥ 2.6 for A‑tier and scenario‑level RVOL in context, trades qualify as **Tier B** (risk `$35`) on these days — consistent and safe.
- Deferred the “see A‑tier more often” tweak (A RVOL 2.6 → 2.4) for a later session.

## Exact code change (backtester)
**File:** `src/midas_v2/engine/backtester.py`  
Find the `tier_ctx` dict and set:
```python
"news_score": float(norm_params.get("news_min_score", 0.0)),
"min_rvol_open": float(norm_params.get("min_rvol_open", 0.0)),
```

> This is **prep only**. Signals/caps unchanged. No keys. Fully reversible.

## Current Scenario B sizing config (unchanged from v0.4.0 end state)
```json
"sizing": {
  "enabled": true,
  "base_risk_usd": 35,
  "max_per_trade_risk_usd": 50,
  "confidence_map": {"A": 1.4, "B": 1.0, "C": 1.0},
  "tier_rules": {
    "A": {"news_min_score": 0, "min_rvol_open": 2.6},
    "B": {"news_min_score": 0, "min_rvol_open": 2.0},
    "C": {"news_min_score": 1, "min_rvol_open": 1.5}
  },
  "drawdown_throttle_after_losses": 999,
  "throttled_risk_factor": 1.0
}
```

## Commands we ran

### Multi‑day range (stability profile — same as before)
```powershell
python scripts\run_catalyst_range_and_summarize.py ^
  --start 2025-08-05 --end 2025-08-07 --scenario B ^
  --require-news --news-min-score 3 --top 2 ^
  --enforce-band --band-min 10 --band-max 40 ^
  --min-rvol-open 2.4 --gate-minutes 20 ^
  --deny-negative --exclude-china ^
  --compare --compare-label B_sizingON_Aug05_07_A14_cap50_rvol26
```

### View results
```powershell
python scripts\show_latest_range.py
python scripts\check_comparison_metrics.py
python scripts\scan_run_bundles.py --scenario B --ignore-labels --dedupe-latest --per-day
```

## Why Tier = B on these days?
- We passed `news_score = 3` into the sizer (prep done), **but** your current A-tier rule needs **RVOL ≥ 2.6**.
- Sizer uses scenario‑level RVOL for now; per‑symbol features are a later step.
- Result: Tier **B** (risk `$35`) — consistent, safe.

## Today’s analysis (business impact)
- **Stability preserved**: Totals remained **+13.93** for Aug‑05→07 with no oversizing of losers.
- **Prepped for upside**: With score‑aware prep in place, when we later require score in tiers and/or pass per‑symbol features, **A‑tier will only trigger on true A‑grade + strong RVOL**.

---

# Next steps (when you’re ready)

## A. Tag & backup (your simple 5 + USB)
**Git (basic, no complexity):**
```powershell
git add -A
git commit -m "v0.4.1: Score-aware sizing prep (news_min_score passthrough); keep A RVOL>=2.6, cap=50"
git tag -a v0.4.1 -m "Score-aware prep; stable gates"
git push
git push --tags
```

**USB snapshot (Explorer)**
- Copy the whole project folder to your memory stick.
- Rename the folder to `Midas_V2_v0.4.1`.

## B. Optional (later) profit push — pick **one** at a time
1) **Enable catalyst‑aware tiering** (immediate effect, no new code):  
   Require **score ≥ 3** in A/B tiers as well as RVOL.  
   ```powershell
   python -c "import json, pathlib; p=pathlib.Path(r'config/scenarios.json'); j=json.loads(p.read_text()); tr=j['B']['params']['sizing']['tier_rules']; tr['A']={'news_min_score':3,'min_rvol_open':2.6}; tr['B']={'news_min_score':3,'min_rvol_open':2.0}; p.write_text(json.dumps(j,indent=2)+'\n'); print('[OK] A/B now require score>=3 + RVOL')"
   ```

2) **Per‑symbol context (small code later):** pass actual per‑symbol `news_score` and opening RVOL to `pick_tier()` for precise A/B classification.

3) **S/R Lite** (low risk, improves expectancy): VWAP/EMA/PMH reclaim entries + band‑aware targets for tighter losers and smarter partials.

---

## Appendix: What we kept unchanged (for stability)
- Signals and entry logic.
- Risk cap `$50`.
- A‑tier multiplier `1.4`, B `1.0`, C `1.0`.
- A‑tier RVOL gate `2.6`.
- Drawdown throttle **off**.
