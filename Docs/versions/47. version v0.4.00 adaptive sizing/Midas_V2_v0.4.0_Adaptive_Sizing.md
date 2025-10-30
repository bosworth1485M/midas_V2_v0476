# Midas_V2 — v0.4.0 “Adaptive Sizing” (Checkpoint)

## 1. Overview
This release introduces adaptive position sizing with configurable tiers, risk caps, and neutral defaults to preserve existing behavior when disabled. All work was verified via controlled backtests (Aug-05→Aug-07, 2025) and validated against the v0.3.47 baseline.

---

## 2. Key Features
- Adaptive position sizing: Risk-per-trade scales based on tier (A/B/C) and context (RVOL, catalyst score).
- Per-scenario toggles: Sizing enabled only for Scenario B; other scenarios inherit config but remain disabled.
- Safety guards: Per-trade risk cap, drawdown throttle (optional, off by default), and tier multipliers.
- Backtester integration: Core engine now applies risk-adjusted share size and updates streak tracking.

---

## 3. New and Updated Files

### New Scripts
| File | Purpose |
|------|----------|
| `src/midas_v2/sizing.py` | AdaptiveSizer class and helper to build from scenario config. |
| `scripts/patch_add_sizing.py` | Adds the sizing block to `scenarios.json`. |
| `scripts/sizing_mode.py` | CLI utility to enable/disable sizing per scenario. |

### Modified Files
| File | Change |
|------|---------|
| `src/midas_v2/engine/backtester.py` | Imports and builds sizer, applies dynamic `qty`, updates on trade exit. |

---

## 4. Scenario B Configuration (Final v0.4.0 Baseline)
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

---

## 5. Commands Used (Chronological Highlights)

### Config Patch and Mode Control
```powershell
python scripts\patch_add_sizing.py --dry-run
python scripts\patch_add_sizing.py           # Apply default block
python scripts\sizing_mode.py on-b            # Enable sizing for Scenario B
python scripts\sizing_mode.py status          # Verify active states
```

### Tuning Parameters via One-Liners
```powershell
# Neutral Tier C + base risk 35
python -c "import json, pathlib; p=pathlib.Path('config/scenarios.json'); j=json.loads(p.read_text()); b=j['B']['params']['sizing']; b['confidence_map'].update({'A':1.8,'B':1.0,'C':1.0}); b['base_risk_usd']=35; p.write_text(json.dumps(j,indent=2))"

# RVOL-only tier rules
python -c "import json, pathlib; p=pathlib.Path('config/scenarios.json'); j=json.loads(p.read_text()); tr=j['B']['params']['sizing']['tier_rules']; tr['A']['news_min_score']=0; tr['B']['news_min_score']=0; p.write_text(json.dumps(j,indent=2))"

# Cap risk per trade
python -c "import json, pathlib; p=pathlib.Path('config/scenarios.json'); j=json.loads(p.read_text()); j['B']['params']['sizing']['max_per_trade_risk_usd']=50; p.write_text(json.dumps(j,indent=2))"

# A-tier multiplier down to 1.4
python -c "import json, pathlib; p=pathlib.Path('config/scenarios.json'); j=json.loads(p.read_text()); j['B']['params']['sizing']['confidence_map']['A']=1.4; p.write_text(json.dumps(j,indent=2))"

# Disable throttle
python -c "import json, pathlib; p=pathlib.Path('config/scenarios.json'); j=json.loads(p.read_text()); s=j['B']['params']['sizing']; s['drawdown_throttle_after_losses']=999; s['throttled_risk_factor']=1.0; p.write_text(json.dumps(j,indent=2))"

# Tighten A-tier RVOL
python -c "import json, pathlib; p=pathlib.Path('config/scenarios.json'); j=json.loads(p.read_text()); j['B']['params']['sizing']['tier_rules']['A']['min_rvol_open']=2.6; p.write_text(json.dumps(j,indent=2))"
```

### Range Testing
```powershell
python scripts\run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B --require-news --news-min-score 3 --top 2 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.4 --gate-minutes 20 --deny-negative --exclude-china --compare --compare-label <LABEL>
python scripts\show_latest_range.py
python scripts\check_comparison_metrics.py
python scripts\scan_run_bundles.py --scenario B --ignore-labels --dedupe-latest --per-day
```

---

## 6. Regression Results (Aug-05 → Aug-07, 2025)
| Variant | Config | Total PnL | Notes |
|----------|---------|------------|-------|
| Baseline (OFF) | No sizing | +40.56 | Reference |
| v1 (C=0.5) | Downscaled | +9.91 | Winners clipped |
| v2 (C=1.0, A=1.8, cap50) | RVOL-only | +24.99 | Upside OK, swings present |
| v3 (A=1.4, cap50) | Tamer A-tier | +19.41 | Stable |
| v4 (Throttle ON) | 50% after loss | −19.98 | Worse |
| v5 (RVOL≥2.6) | Final v0.4.0 | **+13.93** | Balanced |

---

## 7. Recommended Next Steps
### v0.4.1 — *Score-Aware Sizing*
Add line in `backtester.py`:
```python
"news_score": float(norm_params.get("news_min_score", 0.0)),
```
Then re-run Aug-05→07. Expect A-tier triggers only on high-score catalysts.

### v0.4.2 — *Per-Symbol Context*
Pass actual `news_score` and `min_rvol_open` per symbol to `pick_tier()`.

### v0.4.10 — *Support & Resistance Lite*
Introduce dynamic partials and reclaim detection using VWAP/EMA bands.

---

## 8. Git Tag & Push
```powershell
git add -A
git commit -m "v0.4.0: Adaptive sizing baseline (neutral C, A on RVOL>=2.6, cap=50)"
git tag -a v0.4.0 -m "Adaptive sizing baseline verified on Aug-05..07"
git push
git push --tags
```