# Midas_V2 Developer Guide

This is a living reference for parameters, files, scenarios, directory layout, and one-line commands.

## Key Folders
- config/  (scenarios.json, settings.toml)
- scripts/  (run_backtest.*, run_all_scenarios.*)
- src/midas_v2/  (engine, strategy, cli)
- Docs/  (DEV_GUIDE.md, Refresh-Docs.ps1)
- data/samples/  (CSV with header: time,open,high,low,close,volume)
- out/YYYYMMDD/SCENARIO/  (results_YYYY-MM-DD.csv)


### Run Cheat-Sheet
- All scenarios (PowerShell): .\scripts\run_all_scenarios.ps1 -Date 2025-08-05
- One scenario (PowerShell): .\scripts\run_backtest.ps1 -Date 2025-08-05 -Scenario E
- Python direct: python -m midas_v2.cli backtest --date 2025-08-05 --scenario E --universe data/samples/universe_sample.txt --out out\20250805\E

> **Gotcha:** Compose expects the **full RAW file** for `--raw`, e.g.  `--raw data/raw/universe_topgappers_2025-08-05.txt`.
> Using a prefix may produce `rawTop=0` (news-only).


## Catalyst Hybrid — Single Day (auto)

```powershell
python scripts/run_catalyst_flow.py --date 2025-08-05 --scenario B --news-first --news-min-score 1 --top 12 --enforce-band
```

**What this does**
- Uses **news-first** selection; fills with RAW gappers up to **Top-12** within the enforce-band (price/gap).
- Wrapper passes the **full RAW file path** to compose; compose builds **news + RAW fillers**.
- Runs Scenario **B** on the hybrid universe.

## Catalyst Hybrid — Date Range (auto)

```powershell
python scripts/run_catalyst_flow.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --news-min-score 1 --top 12 --enforce-band
```

**Notes**
- Consider enabling an **opening RVOL gate** in config/scenarios.json (e.g., ≥1.5× first 10–15m vs prior day).
- Optional headline polarity filter in `enrich_universe_catalyst.py` (e.g., `--deny-negative` with `data/catalyst/neg_terms.txt`).

### Strategy presets (summary view)


| Scenario | tp_pct | sl_pct | ema_confirm | vwap_confirm | macd_confirm | dip_reclaim | min_dip_pct | min_reclaim_pct | reclaim_ref | ema_period | gate_minutes | rise_bars | min_pm_vol |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 2.0 | 2.5 |  |  |  | False |  |  | EMA |  | 10 | 3 | 30000 |
| B | 2.0 | 2.5 |  |  |  | False |  |  |  |  | 20 | 3 | 30000 |
| C | 2.0 | 2.5 |  |  |  | False |  |  | EMA |  | 10 | 3 | 30000 |
| D | 2.0 | 2.5 |  |  |  | False |  |  | EMA |  | 5 | 3 | 30000 |
| E | 2.0 | 2.5 |  |  |  | True | 2.0 | 0.0 | vwap | 5 | 15 | 3 | 50000 |


### Strategy presets from config/scenarios.json


| Scenario | Source | Params (JSON) |
|---|---|---|
| A | config\scenarios.json | {"min_pm_vol":30000,"dip_reclaim":false,"tp_pct":2.0,"rise_bars":3,"macd_rise_bars":2,"gate_minutes":10,"sl_pct":2.5,"reclaim_ref":"EMA","min_price":1,"max_price":20,"min_gap_pct":10,"max_gap_pct":40,"sizing":{"enabled":false,"base_risk_usd":50,"max_per_trade_risk_usd":120,"max_daily_risk_usd":300,"drawdown_throttle_after_losses":3,"throttled_risk_factor":0.5,"confidence_map":{"A":1.8,"B":1.0,"C":0.5},"tier_rules":{"A":{"news_min_score":3,"min_rvol_open":2.4},"B":{"news_min_score":2,"min_rvol_open":2.0},"C":{"news_min_score":1,"min_rvol_open":1.5}}}} |
| B | config\scenarios.json | {"min_pm_vol":30000,"dip_reclaim":false,"tp_pct":2.0,"rise_bars":3,"green_body_min":0.22,"macd_rise_bars":2,"require_macd_rise":true,"gate_minutes":20,"sl_pct":2.5,"min_rvol_open":2.0,"rvol_open_minutes":15,"min_price":1,"max_price":20,"min_gap_pct":10,"max_gap_pct":40,"sizing":{"enabled":true,"base_risk_usd":35,"max_per_trade_risk_usd":50,"max_daily_risk_usd":300,"drawdown_throttle_after_losses":999,"throttled_risk_factor":1.0,"confidence_map":{"A":1.4,"B":1.0,"C":1.0},"tier_rules":{"A":{"news_min_score":0,"min_rvol_open":2.6},"B":{"news_min_score":0,"min_rvol_open":2.0},"C":{"news_min_score":1,"min_rvol_open":1.5}}}} |
| C | config\scenarios.json | {"min_pm_vol":30000,"dip_reclaim":false,"tp_pct":2.0,"rise_bars":3,"macd_rise_bars":2,"gate_minutes":10,"sl_pct":2.5,"reclaim_ref":"EMA","min_price":1,"max_price":20,"min_gap_pct":10,"max_gap_pct":40,"sizing":{"enabled":false,"base_risk_usd":50,"max_per_trade_risk_usd":120,"max_daily_risk_usd":300,"drawdown_throttle_after_losses":3,"throttled_risk_factor":0.5,"confidence_map":{"A":1.8,"B":1.0,"C":0.5},"tier_rules":{"A":{"news_min_score":3,"min_rvol_open":2.4},"B":{"news_min_score":2,"min_rvol_open":2.0},"C":{"news_min_score":1,"min_rvol_open":1.5}}}} |
| D | config\scenarios.json | {"min_pm_vol":30000,"dip_reclaim":false,"tp_pct":2.0,"rise_bars":3,"green_body_min":0.22,"macd_rise_bars":2,"gate_minutes":5,"sl_pct":2.5,"reclaim_ref":"EMA","min_price":1,"max_price":20,"min_gap_pct":10,"max_gap_pct":40,"sizing":{"enabled":false,"base_risk_usd":50,"max_per_trade_risk_usd":120,"max_daily_risk_usd":300,"drawdown_throttle_after_losses":3,"throttled_risk_factor":0.5,"confidence_map":{"A":1.8,"B":1.0,"C":0.5},"tier_rules":{"A":{"news_min_score":3,"min_rvol_open":2.4},"B":{"news_min_score":2,"min_rvol_open":2.0},"C":{"news_min_score":1,"min_rvol_open":1.5}}}} |
| E | config\scenarios.json | {"min_pm_vol":50000,"dip_reclaim":true,"reclaim_ref":"vwap","min_dip_pct":2.0,"min_reclaim_pct":0.0,"reclaim_buffer_bps":5,"vwap_slope_bps":2,"ema_period":5,"tp_pct":2.0,"rise_bars":3,"green_body_min":0.22,"macd_rise_bars":2,"require_macd_rise":true,"gate_minutes":15,"sl_pct":2.5,"min_rvol_open":2.0,"rvol_open_minutes":15,"min_price":1,"max_price":20,"min_gap_pct":10,"max_gap_pct":40,"sizing":{"enabled":false,"base_risk_usd":50,"max_per_trade_risk_usd":120,"max_daily_risk_usd":300,"drawdown_throttle_after_losses":3,"throttled_risk_factor":0.5,"confidence_map":{"A":1.8,"B":1.0,"C":0.5},"tier_rules":{"A":{"news_min_score":3,"min_rvol_open":2.4},"B":{"news_min_score":2,"min_rvol_open":2.0},"C":{"news_min_score":1,"min_rvol_open":1.5}}}} |


### Catalyst Hybrid Notes (auto)


- Compose expects **full RAW path** for `--raw`, e.g. `data/raw/universe_topgappers_<DATE>.txt`.
- Using a prefix may produce `rawTop=0` (news-only).

