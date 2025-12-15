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
| A | config\scenarios.json | {"dip_reclaim":false,"gate_minutes":10,"macd_rise_bars":2,"max_gap_pct":40,"max_price":20,"min_gap_pct":10,"min_pm_vol":30000,"min_price":1,"reclaim_ref":"EMA","rise_bars":3,"sizing":{"base_risk_usd":50,"confidence_map":{"A":1.8,"B":1.0,"C":0.5},"drawdown_throttle_after_losses":3,"enabled":false,"max_daily_risk_usd":300,"max_per_trade_risk_usd":120,"throttled_risk_factor":0.5,"tier_rules":{"A":{"min_rvol_open":2.4,"news_min_score":3},"B":{"min_rvol_open":2.0,"news_min_score":2},"C":{"min_rvol_open":1.5,"news_min_score":1}}},"sl_pct":2.5,"tp_pct":2.0} |
| B | config\scenarios.json | {"dip_reclaim":false,"gate_minutes":20,"green_body_min":0.22,"macd_rise_bars":2,"max_gap_pct":40,"max_price":20,"min_gap_pct":10,"min_pm_vol":30000,"min_price":1,"min_rvol_open":2.0,"require_macd_rise":true,"rise_bars":3,"rvol_open_minutes":15,"sizing":{"base_risk_usd":35,"confidence_map":{"A":1.4,"B":1.0,"C":1.0},"drawdown_throttle_after_losses":999,"enabled":true,"max_daily_risk_usd":300,"max_per_trade_risk_usd":50,"throttled_risk_factor":1.0,"tier_rules":{"A":{"min_rvol_open":2.6,"news_min_score":0},"B":{"min_rvol_open":2.0,"news_min_score":0},"C":{"min_rvol_open":1.5,"news_min_score":1}}},"sl_pct":2.5,"top":5,"tp_pct":2.0,"twcs_enabled":true,"plot_twcs":true,"max_trades_per_symbol":1,"daily_max_loss":1000.0} |
| C | config\scenarios.json | {"dip_reclaim":false,"gate_minutes":10,"macd_rise_bars":2,"max_gap_pct":40,"max_price":20,"min_gap_pct":10,"min_pm_vol":30000,"min_price":1,"reclaim_ref":"EMA","rise_bars":3,"sizing":{"base_risk_usd":50,"confidence_map":{"A":1.8,"B":1.0,"C":0.5},"drawdown_throttle_after_losses":3,"enabled":false,"max_daily_risk_usd":300,"max_per_trade_risk_usd":120,"throttled_risk_factor":0.5,"tier_rules":{"A":{"min_rvol_open":2.4,"news_min_score":3},"B":{"min_rvol_open":2.0,"news_min_score":2},"C":{"min_rvol_open":1.5,"news_min_score":1}}},"sl_pct":2.5,"tp_pct":2.0} |
| D | config\scenarios.json | {"dip_reclaim":false,"gate_minutes":5,"green_body_min":0.22,"macd_rise_bars":2,"max_gap_pct":40,"max_price":20,"min_gap_pct":10,"min_pm_vol":30000,"min_price":1,"reclaim_ref":"EMA","rise_bars":3,"sizing":{"base_risk_usd":50,"confidence_map":{"A":1.8,"B":1.0,"C":0.5},"drawdown_throttle_after_losses":3,"enabled":false,"max_daily_risk_usd":300,"max_per_trade_risk_usd":120,"throttled_risk_factor":0.5,"tier_rules":{"A":{"min_rvol_open":2.4,"news_min_score":3},"B":{"min_rvol_open":2.0,"news_min_score":2},"C":{"min_rvol_open":1.5,"news_min_score":1}}},"sl_pct":2.5,"tp_pct":2.0} |
| E | config\scenarios.json | {"dip_reclaim":true,"ema_period":5,"gate_minutes":15,"green_body_min":0.22,"macd_rise_bars":2,"max_gap_pct":40,"max_price":20,"min_dip_pct":2.0,"min_gap_pct":10,"min_pm_vol":50000,"min_price":1,"min_reclaim_pct":0.0,"min_rvol_open":2.0,"reclaim_buffer_bps":5,"reclaim_ref":"vwap","require_macd_rise":true,"rise_bars":3,"rvol_open_minutes":15,"sizing":{"base_risk_usd":50,"confidence_map":{"A":1.8,"B":1.0,"C":0.5},"drawdown_throttle_after_losses":3,"enabled":false,"max_daily_risk_usd":300,"max_per_trade_risk_usd":120,"throttled_risk_factor":0.5,"tier_rules":{"A":{"min_rvol_open":2.4,"news_min_score":3},"B":{"min_rvol_open":2.0,"news_min_score":2},"C":{"min_rvol_open":1.5,"news_min_score":1}}},"sl_pct":2.5,"tp_pct":2.0,"vwap_slope_bps":2} |


### Catalyst Hybrid Notes (auto)


- Compose expects **full RAW path** for `--raw`, e.g. `data/raw/universe_topgappers_<DATE>.txt`.
- Using a prefix may produce `rawTop=0` (news-only).

