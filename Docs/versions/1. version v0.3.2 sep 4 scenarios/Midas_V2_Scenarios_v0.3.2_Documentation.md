# Midas_V2 — Scenarios Documentation (v0.3.2-scenarios)

As of 2025-09-04 19:10

This document describes scenarios A–E as they currently exist, high-level descriptions, how we tested them, results observed, why Scenario A can be deceptive, and the exact run commands to reproduce. An appendix provides parameter definitions.

## 1) Scenario Definitions (Current Configuration)

### A — Loose exploratory profile. Minimal safeguards, MACD off, gate=0, wider SL. Trades very frequently and may look good on strong-trend days but is risky on choppy days.

| Parameter | Value |
|-----------|-------|
| min_pm_vol | 0 |
| dip_reclaim | False |
| tp_pct | 1.2 |
| sl_pct | 2.7 |
| rise_bars | 2 |
| min_dip_pct | 2 |
| macd_confirm | True |
| ema_confirm | True |
| vwap_confirm | True |
| ema_period | 9 |
| gate_minutes | 0 |
| reclaim_pmh | False |
| reclaim_ref | ema |
| min_reclaim_pct | 0.5 |


### B — Safe baseline. Aligned with Cameron-style rules (MACD on, EMA/VWAP confirm, gate=10, TP/SL ~2/2.5, min_pm_vol=30k). Designed to be reproducible and consistent.

| Parameter | Value |
|-----------|-------|
| min_pm_vol | 30000 |
| dip_reclaim | False |
| tp_pct | 2.0 |
| sl_pct | 2.5 |
| rise_bars | 2 |
| min_dip_pct | 2 |
| macd_confirm | True |
| ema_confirm | True |
| vwap_confirm | True |
| ema_period | 9 |
| gate_minutes | 10 |
| reclaim_pmh | False |
| reclaim_ref | ema |
| min_reclaim_pct | 0.5 |
| min_price | 1 |
| max_price | 20 |
| min_gap_pct | 10 |
| max_gap_pct | 40 |


### C — Variant of A. Similar looseness with slight differences (e.g., VWAP confirm off, MACD off). Research profile, not recommended for baseline trading.

| Parameter | Value |
|-----------|-------|
| min_pm_vol | 0 |
| dip_reclaim | False |
| tp_pct | 1.2 |
| sl_pct | 2.7 |
| rise_bars | 2 |
| min_dip_pct | 2 |
| macd_confirm | False |
| ema_confirm | True |
| vwap_confirm | False |
| ema_period | 9 |
| gate_minutes | 0 |
| reclaim_pmh | False |
| reclaim_ref | ema |
| min_reclaim_pct | 0.5 |


### D — Strict profile. Now updated to MACD on, gate=5, SL=2.5, min_pm_vol=30k, with EMA/VWAP confirm and price/gap bands. Trades less often, with stronger filters.

| Parameter | Value |
|-----------|-------|
| min_pm_vol | 0 |
| dip_reclaim | False |
| tp_pct | 2.0 |
| sl_pct | 3.5 |
| rise_bars | 2 |
| min_dip_pct | 2 |
| macd_confirm | False |
| ema_confirm | True |
| vwap_confirm | True |
| ema_period | 9 |
| gate_minutes | 0 |
| reclaim_pmh | False |
| reclaim_ref | ema |
| min_reclaim_pct | 0.5 |


### E — Dip-reclaim strategy. Looks for dips to VWAP/EMA with MACD rising. Gate=10, PM vol=30k. Adds profit-factor potential when reclaim plays set up.

| Parameter | Value |
|-----------|-------|
| min_pm_vol | 30000 |
| dip_reclaim | True |
| tp_pct | 2.0 |
| sl_pct | 2.5 |
| rise_bars | 2 |
| min_dip_pct | 2.0 |
| macd_confirm | True |
| ema_confirm | True |
| vwap_confirm | True |
| ema_period | 9 |
| gate_minutes | 10 |
| reclaim_pmh | False |
| reclaim_ref | vwap |
| min_reclaim_pct | 0.5 |


### B_safe — No high-level description provided.

| Parameter | Value |
|-----------|-------|
| min_pm_vol | 30000 |
| dip_reclaim | False |
| tp_pct | 2.0 |
| sl_pct | 2.5 |
| rise_bars | 2 |
| min_dip_pct | 2 |
| macd_confirm | True |
| ema_confirm | True |
| vwap_confirm | True |
| ema_period | 9 |
| gate_minutes | 10 |
| reclaim_pmh | False |
| reclaim_ref | ema |
| min_reclaim_pct | 0.5 |


### D_backup — No high-level description provided.

| Parameter | Value |
|-----------|-------|
| min_pm_vol | 0 |
| dip_reclaim | False |
| tp_pct | 2.0 |
| sl_pct | 3.5 |
| rise_bars | 2 |
| min_dip_pct | 2 |
| macd_confirm | False |
| ema_confirm | True |
| vwap_confirm | True |
| ema_period | 9 |
| gate_minutes | 0 |
| reclaim_pmh | False |
| reclaim_ref | ema |
| min_reclaim_pct | 0.5 |


### B_backup — No high-level description provided.

| Parameter | Value |
|-----------|-------|
| min_pm_vol | 0 |
| dip_reclaim | False |
| tp_pct | 1.2 |
| sl_pct | 2.7 |
| rise_bars | 2 |
| min_dip_pct | 2 |
| macd_confirm | False |
| ema_confirm | True |
| vwap_confirm | True |
| ema_period | 9 |
| gate_minutes | 0 |
| reclaim_pmh | False |
| reclaim_ref | ema |
| min_reclaim_pct | 0.5 |


## 2) How We Tested the Scenarios

We ran single‑day backtests and a day summary on 2025‑08‑05, using the project’s built‑in runners. The flow mirrors your USER_GUIDE:

- Fetch top gappers for the day (internal script): scripts/topgappers.py
- Write the universe file (auto): data/samples/universe_sample.txt
- Fetch minute data (Polygon): scripts/fetch_minutes_polygon.py --date 2025-08-05 --session rth
- Run backtest per scenario: python -m midas_v2.cli backtest ... (called by scripts/run_day_simple.py)
- Results written to: out/<YYYYMMDD>/<SCENARIO>/results_<DATE>.csv
- Summarize: scripts/summarize_results.py --date YYYY-MM-DD

**Single-day commands used:**

```
python scripts\run_day_simple.py --date 2025-08-05 --scenario D
python scripts\run_day_simple.py --date 2025-08-05 --scenario B
python scripts\summarize_results.py --date 2025-08-05
```

## 3) Results We Saw (2025‑08‑05) and What They Mean

| Scenario | Result |
|----------|---------|
| A | TP=29 SL=10 Win%=74.36 |
| B | TP=1 SL=0 Win%=100.0 |
| C | TP=29 SL=10 Win%=74.36 |
| D | TP=1 SL=0 Win%=100.0 |
| E2 | TP=2 SL=0 Win%=100.0 |
| E | TP=0 SL=0 Win%=0 |
| E_cfg2 | TP=0 SL=0 Win%=0 |
| E_cfg | TP=0 SL=0 Win%=0 |
| E_debug | TP=0 SL=0 Win%=0 |
| E_vwapoff | TP=0 SL=0 Win%=0 |

**Interpretation:**

- **B vs D:** Both captured the clean STTK breakout (TP ~2.04%). D is stricter and should trade less over multiple days while maintaining or slightly improving win rate.
- **A/C:** Looser profiles with many more trades (39 trades, 29 TP, 10 SL) with ~74% WR on this date—useful for research, but risky in practice.
- **E2:** Dip‑reclaim variant, fired twice and won both. Shows promise, requires more dates to validate.
- **E family (others):** No trades on this date. Normal when reclaim criteria don’t occur.

## 4) Why Scenario A's Results Can Be Deceptive

Scenario A looked strong on 2025‑08‑05, showing 29 wins out of 39 trades (~74% WR). But this performance can be misleading:

- **Overtrading:** A fired repeatedly on SMXT, taking dozens of trades on one ticker. On a trending day this looks good, but it exposes you to clustering risk.
- **Survivorship bias:** A benefits from strong trend days. On choppy days, those same loose filters would produce many stop‑outs.
- **Single‑ticker concentration:** Nearly all trades came from one symbol, creating overexposure.
- **Hidden risk:** Multiple stop‑outs can cluster if the ticker reverses. This is why Ross and our stricter configs avoid overtrading weak gappers.

By contrast, Scenarios B and D only allowed the cleanest trade, keeping risk contained. This safeguard makes their results more reliable across market conditions, even if they show fewer winners on strong days.

## 5) Reproduction Commands (Detailed)

**Single‑day run (baseline and strict):**

```
python scripts\run_day_simple.py --date 2025-08-05 --scenario B
python scripts\run_day_simple.py --date 2025-08-05 --scenario D
python scripts\summarize_results.py --date 2025-08-05
```

**Optional range run:**

```
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenarios B,D,E
```

**Version tag (two-step, safe in PowerShell):**

```
git add -A
git commit -m "Scenarios: D strict (MACD on, gate=5, SL=2.5, 30k PM vol, price/gap bands)"
git tag -a v0.3.2-scenarios -m "Milestone: Scenario D strict; B baseline; E dip-reclaim"
git push
git push origin v0.3.2-scenarios
```

## Appendix A — Parameter Glossary

| Parameter | Description |
|-----------|-------------|
| min_pm_vol | Minimum premarket volume required for the ticker to qualify. |
| tp_pct | Take-profit percentage target. Trade exits at this gain. |
| sl_pct | Stop-loss percentage. Trade exits at this loss. |
| rise_bars | Number of consecutive rising bars required for momentum confirmation. |
| min_dip_pct | Minimum dip percentage from high required to qualify for a dip reclaim. |
| macd_confirm | Require MACD histogram rising or MACD line > signal line. |
| ema_confirm | Require price above EMA and EMA trending up. |
| vwap_confirm | Require price above VWAP and VWAP sloping up. |
| ema_period | Period (bars) used for the EMA confirm. |
| gate_minutes | Minimum minutes after open before trades allowed (e.g., gate=10 skips first 10m). |
| dip_reclaim | If true, scenario waits for dip below EMA/VWAP then reclaim trigger. |
| reclaim_pmh | If true, scenario requires reclaim of premarket high. |
| reclaim_ref | Reference indicator for reclaim logic (e.g., 'ema' or 'vwap'). |
| min_reclaim_pct | Minimum % threshold required for reclaim confirmation. |
| min_price | Minimum stock price allowed for scenario. |
| max_price | Maximum stock price allowed. |
| min_gap_pct | Minimum gap-up percentage required at open. |
| max_gap_pct | Maximum gap-up percentage allowed. |
