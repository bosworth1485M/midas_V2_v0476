PS C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working> python scripts\run_range_and_summarize.py --start 2025-08-01 --end 2025-08-10 --scenario B

=== Running range: 2025-08-01 -> 2025-08-10 | Scenarios: ['B'] | Mode: OVERWRITE ===

[RUN] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe scripts/run_day_simple.py --date 2025-08-01 --scenario B --session rth
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\scripts\topgappers.py --date 2025-08-01 --scenario B
Open-gap gappers (open vs prev close)  price=[1..20]  min_gap=10%
SYMBOL      GAP%    PRICE
PHLT      111.27   7.5000
MWYN       91.11   1.7200
NAMM       43.94   5.7000
BTAI       26.72   1.6600
BKHAR      25.33   1.8800
[SCAN] gap_map saved -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250801\scanner\gap_map_2025-08-01.json
[UNIVERSE] Trimmed to Top-5 symbols (from 25)
Wrote 5 symbols -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt
[UNIVERSE] C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt has 5 symbols
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\scripts\fetch_minutes_polygon.py --date 2025-08-01 --session rth
Wrote data\samples\sample_2025-08-01_PHLT.csv
Wrote data\samples\sample_2025-08-01_MWYN.csv
Wrote data\samples\sample_2025-08-01_NAMM.csv
Wrote data\samples\sample_2025-08-01_BTAI.csv
Wrote data\samples\sample_2025-08-01_BKHAR.csv
Done. wrote=5 empty=0 failed=0
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe -m midas_v2.cli backtest --date 2025-08-01 --scenario B --universe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt --out C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250801\B
[CFG] scenario= B  gate_minutes= 20  min_rvol_open= 2.0  rvol_open_minutes= 15  green_streak= None  macd_rise_bars= 2  require_macd_rise= True  max_trades_per_symbol= 1  daily_max_loss= 1000.0
2025-12-09 09:13:32,907 [INFO] [WHY] Using StrategyParams: {'dip_reclaim': False, 'gate_minutes': 20, 'green_body_min': 0.22, 'macd_rise_bars': 2, 'min_pm_vol': 30000, 'min_rvol_open': 2.0, 'require_macd_rise': True, 'rise_bars': 3, 'rvol_open_minutes': 15, 'sl_pct': 2.5, 'tp_pct': 2.0}
2025-12-09 09:13:32,909 [INFO] [SIZE] PHLT tier=B risk_usd=35.00 entry=7.6350 sl=7.4441 qty=183
2025-12-09 09:13:32,915 [INFO] [SIZE] MWYN tier=B risk_usd=35.00 entry=1.4000 sl=1.3650 qty=1000

======================================================================
TRADE: MWYN | Side: LONG | Entry: 2025-08-01 10:06 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 91.11%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the stop loss was hit.

RESULTS:
• Profit/Loss: $-35.00
• This trade lost $35.00.
• Number of shares: 1000
• Entry price: $1.40
• Exit price: $1.36
• Profit per share: $-0.03
• Sale time: 2025-08-01 10:09

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $1.36)
• Take profit: 2.0% (price: $1.43)

RISK CALCULATION:
• Risk amount (USD): $35.00
• Risk per share: $0.03
• Approximate shares: 35.00 ÷ 0.03 ≈ 1000
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:13:32,926 [INFO] [SIZE] NAMM tier=B risk_usd=35.00 entry=4.7300 sl=4.6118 qty=295

======================================================================
TRADE: NAMM | Side: LONG | Entry: 2025-08-01 10:03 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 43.94%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the stop loss was hit.

RESULTS:
• Profit/Loss: $-34.88
• This trade lost $34.88.
• Number of shares: 295
• Entry price: $4.73
• Exit price: $4.61
• Profit per share: $-0.12
• Sale time: 2025-08-01 10:05

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $4.61)
• Take profit: 2.0% (price: $4.82)

RISK CALCULATION:
• Risk amount (USD): $34.88
• Risk per share: $0.12
• Approximate shares: 34.88 ÷ 0.12 ≈ 295
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:13:32,935 [INFO] [SIZE] BTAI tier=B risk_usd=35.00 entry=1.7900 sl=1.7452 qty=782

======================================================================
TRADE: BTAI | Side: LONG | Entry: 2025-08-01 10:32 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 26.72%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the stop loss was hit.

RESULTS:
• Profit/Loss: $-34.99
• This trade lost $34.99.
• Number of shares: 782
• Entry price: $1.79
• Exit price: $1.75
• Profit per share: $-0.04
• Sale time: 2025-08-01 10:32

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $1.75)
• Take profit: 2.0% (price: $1.83)

RISK CALCULATION:
• Risk amount (USD): $34.99
• Risk per share: $0.04
• Approximate shares: 34.99 ÷ 0.04 ≈ 782
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

[OK] Backtest complete -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250801\B\results_2025-08-01.csv
[INFO] Running summarize_results.py and streaming output...
B: TP=0 SL=3 Win%=0.00
D: TP=0 SL=0 Win%=0.00
E: TP=0 SL=0 Win%=0.00
[OK] Summary saved -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250801\B\summary_2025-08-01.txt

[OK] Backtest done.
2025-08-01 [B] -> trades=3, wins=0, losses=3, winrate=0.00%, pnl=-104.87
[SKIP] 2025-08-02 (weekend)
[SKIP] 2025-08-03 (weekend)
[RUN] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe scripts/run_day_simple.py --date 2025-08-04 --scenario B --session rth
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\scripts\topgappers.py --date 2025-08-04 --scenario B
Open-gap gappers (open vs prev close)  price=[1..20]  min_gap=10%
SYMBOL      GAP%    PRICE
PBM        92.80   4.5500
COMM       77.54  13.8300
VERB       59.94  15.2100
UNIT       54.18   7.5700
SNGX       52.55   4.1800
[SCAN] gap_map saved -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250804\scanner\gap_map_2025-08-04.json
[UNIVERSE] Trimmed to Top-5 symbols (from 37)
Wrote 5 symbols -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt
[UNIVERSE] C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt has 5 symbols
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\scripts\fetch_minutes_polygon.py --date 2025-08-04 --session rth
Wrote data\samples\sample_2025-08-04_PBM.csv
Wrote data\samples\sample_2025-08-04_COMM.csv
Wrote data\samples\sample_2025-08-04_VERB.csv
Wrote data\samples\sample_2025-08-04_UNIT.csv
Wrote data\samples\sample_2025-08-04_SNGX.csv
Done. wrote=5 empty=0 failed=0
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe -m midas_v2.cli backtest --date 2025-08-04 --scenario B --universe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt --out C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250804\B
[CFG] scenario= B  gate_minutes= 20  min_rvol_open= 2.0  rvol_open_minutes= 15  green_streak= None  macd_rise_bars= 2  require_macd_rise= True  max_trades_per_symbol= 1  daily_max_loss= 1000.0
2025-12-09 09:13:58,844 [INFO] [WHY] Using StrategyParams: {'dip_reclaim': False, 'gate_minutes': 20, 'green_body_min': 0.22, 'macd_rise_bars': 2, 'min_pm_vol': 30000, 'min_rvol_open': 2.0, 'require_macd_rise': True, 'rise_bars': 3, 'rvol_open_minutes': 15, 'sl_pct': 2.5, 'tp_pct': 2.0}
2025-12-09 09:13:58,846 [INFO] [SIZE] PBM tier=B risk_usd=35.00 entry=4.3201 sl=4.2121 qty=324

======================================================================
TRADE: PBM | Side: LONG | Entry: 2025-08-04 10:32 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 92.80%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the stop loss was hit.

RESULTS:
• Profit/Loss: $-34.99
• This trade lost $34.99.
• Number of shares: 324
• Entry price: $4.32
• Exit price: $4.21
• Profit per share: $-0.11
• Sale time: 2025-08-04 10:45

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $4.21)
• Take profit: 2.0% (price: $4.41)

RISK CALCULATION:
• Risk amount (USD): $34.99
• Risk per share: $0.11
• Approximate shares: 34.99 ÷ 0.11 ≈ 324
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:13:58,863 [INFO] [SIZE] COMM tier=B risk_usd=35.00 entry=13.1650 sl=12.8359 qty=106

======================================================================
TRADE: COMM | Side: LONG | Entry: 2025-08-04 10:47 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 77.54%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the take profit was hit.

RESULTS:
• Profit/Loss: $27.91
• This trade made a profit of $27.91.
• Number of shares: 106
• Entry price: $13.16
• Exit price: $13.43
• Profit per share: $0.26
• Sale time: 2025-08-04 11:16

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $12.84)
• Take profit: 2.0% (price: $13.43)

RISK CALCULATION:
• Risk amount (USD): $34.89
• Risk per share: $0.33
• Approximate shares: 34.89 ÷ 0.33 ≈ 106
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:13:58,879 [INFO] [SIZE] VERB tier=B risk_usd=35.00 entry=18.1500 sl=17.6962 qty=77

======================================================================
TRADE: VERB | Side: LONG | Entry: 2025-08-04 10:32 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 59.94%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the stop loss was hit.

RESULTS:
• Profit/Loss: $-34.94
• This trade lost $34.94.
• Number of shares: 77
• Entry price: $18.15
• Exit price: $17.70
• Profit per share: $-0.45
• Sale time: 2025-08-04 10:32

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $17.70)
• Take profit: 2.0% (price: $18.51)

RISK CALCULATION:
• Risk amount (USD): $34.94
• Risk per share: $0.45
• Approximate shares: 34.94 ÷ 0.45 ≈ 77
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:13:58,893 [INFO] [SIZE] UNIT tier=B risk_usd=35.00 entry=8.1350 sl=7.9316 qty=172

======================================================================
TRADE: UNIT | Side: LONG | Entry: 2025-08-04 10:40 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 54.18%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the take profit was hit.

RESULTS:
• Profit/Loss: $27.98
• This trade made a profit of $27.98.
• Number of shares: 172
• Entry price: $8.13
• Exit price: $8.30
• Profit per share: $0.16
• Sale time: 2025-08-04 12:39

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $7.93)
• Take profit: 2.0% (price: $8.30)

RISK CALCULATION:
• Risk amount (USD): $34.98
• Risk per share: $0.20
• Approximate shares: 34.98 ÷ 0.20 ≈ 172
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:13:58,909 [INFO] [SIZE] SNGX tier=B risk_usd=35.00 entry=3.7800 sl=3.6855 qty=370

======================================================================
TRADE: SNGX | Side: LONG | Entry: 2025-08-04 10:05 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 52.55%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the stop loss was hit.

RESULTS:
• Profit/Loss: $-34.97
• This trade lost $34.97.
• Number of shares: 370
• Entry price: $3.78
• Exit price: $3.69
• Profit per share: $-0.09
• Sale time: 2025-08-04 10:05

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $3.69)
• Take profit: 2.0% (price: $3.86)

RISK CALCULATION:
• Risk amount (USD): $34.97
• Risk per share: $0.09
• Approximate shares: 34.97 ÷ 0.09 ≈ 370
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

[OK] Backtest complete -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250804\B\results_2025-08-04.csv
[INFO] Running summarize_results.py and streaming output...
B: TP=2 SL=3 Win%=40.00
D: TP=0 SL=0 Win%=0.00
E: TP=0 SL=0 Win%=0.00
[OK] Summary saved -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250804\B\summary_2025-08-04.txt

[OK] Backtest done.
2025-08-04 [B] -> trades=5, wins=2, losses=3, winrate=40.00%, pnl=-49.01
[RUN] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe scripts/run_day_simple.py --date 2025-08-05 --scenario B --session rth
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\scripts\topgappers.py --date 2025-08-05 --scenario B
Open-gap gappers (open vs prev close)  price=[1..20]  min_gap=10%
SYMBOL      GAP%    PRICE
YMAB      103.70   8.5350
SMXT       72.04   1.6000
AIP        51.11  14.2800
LOBO       40.40   1.0300
TCMD       35.39  13.3900
[SCAN] gap_map saved -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250805\scanner\gap_map_2025-08-05.json
[UNIVERSE] Trimmed to Top-5 symbols (from 35)
Wrote 5 symbols -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt
[UNIVERSE] C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt has 5 symbols
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\scripts\fetch_minutes_polygon.py --date 2025-08-05 --session rth
Wrote data\samples\sample_2025-08-05_YMAB.csv
Wrote data\samples\sample_2025-08-05_SMXT.csv
Wrote data\samples\sample_2025-08-05_AIP.csv
Wrote data\samples\sample_2025-08-05_LOBO.csv
Wrote data\samples\sample_2025-08-05_TCMD.csv
Done. wrote=5 empty=0 failed=0
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe -m midas_v2.cli backtest --date 2025-08-05 --scenario B --universe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt --out C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250805\B
[CFG] scenario= B  gate_minutes= 20  min_rvol_open= 2.0  rvol_open_minutes= 15  green_streak= None  macd_rise_bars= 2  require_macd_rise= True  max_trades_per_symbol= 1  daily_max_loss= 1000.0
2025-12-09 09:14:17,449 [INFO] [WHY] Using StrategyParams: {'dip_reclaim': False, 'gate_minutes': 20, 'green_body_min': 0.22, 'macd_rise_bars': 2, 'min_pm_vol': 30000, 'min_rvol_open': 2.0, 'require_macd_rise': True, 'rise_bars': 3, 'rvol_open_minutes': 15, 'sl_pct': 2.5, 'tp_pct': 2.0}
2025-12-09 09:14:17,452 [INFO] [SIZE] YMAB tier=B risk_usd=35.00 entry=8.5250 sl=8.3119 qty=164
2025-12-09 09:14:17,462 [INFO] [SIZE] SMXT tier=B risk_usd=35.00 entry=1.9988 sl=1.9488 qty=700

======================================================================
TRADE: SMXT | Side: LONG | Entry: 2025-08-05 10:35 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 72.04%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the stop loss was hit.

RESULTS:
• Profit/Loss: $-34.98
• This trade lost $34.98.
• Number of shares: 700
• Entry price: $2.00
• Exit price: $1.95
• Profit per share: $-0.05
• Sale time: 2025-08-05 10:36

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $1.95)
• Take profit: 2.0% (price: $2.04)

RISK CALCULATION:
• Risk amount (USD): $34.98
• Risk per share: $0.05
• Approximate shares: 34.98 ÷ 0.05 ≈ 700
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:14:17,483 [INFO] [SIZE] AIP tier=B risk_usd=35.00 entry=13.7000 sl=13.3575 qty=102

======================================================================
TRADE: AIP | Side: LONG | Entry: 2025-08-05 10:04 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 51.11%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the stop loss was hit.

RESULTS:
• Profit/Loss: $-34.94
• This trade lost $34.94.
• Number of shares: 102
• Entry price: $13.70
• Exit price: $13.36
• Profit per share: $-0.34
• Sale time: 2025-08-05 10:12

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $13.36)
• Take profit: 2.0% (price: $13.97)

RISK CALCULATION:
• Risk amount (USD): $34.94
• Risk per share: $0.34
• Approximate shares: 34.94 ÷ 0.34 ≈ 102
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:14:17,498 [INFO] [SIZE] LOBO tier=B risk_usd=35.00 entry=0.8640 sl=0.8424 qty=1620

======================================================================
TRADE: LOBO | Side: LONG | Entry: 2025-08-05 10:29 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 40.40%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the stop loss was hit.

RESULTS:
• Profit/Loss: $-34.99
• This trade lost $34.99.
• Number of shares: 1620
• Entry price: $0.86
• Exit price: $0.84
• Profit per share: $-0.02
• Sale time: 2025-08-05 10:31

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $0.84)
• Take profit: 2.0% (price: $0.88)

RISK CALCULATION:
• Risk amount (USD): $34.99
• Risk per share: $0.02
• Approximate shares: 34.99 ÷ 0.02 ≈ 1620
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

[OK] Backtest complete -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250805\B\results_2025-08-05.csv
[INFO] Running summarize_results.py and streaming output...
B: TP=0 SL=3 Win%=0.00
D: TP=0 SL=0 Win%=0.00
E: TP=0 SL=0 Win%=0.00
[OK] Summary saved -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250805\B\summary_2025-08-05.txt

[OK] Backtest done.
2025-08-05 [B] -> trades=3, wins=0, losses=3, winrate=0.00%, pnl=-104.91
[RUN] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe scripts/run_day_simple.py --date 2025-08-06 --scenario B --session rth
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\scripts\topgappers.py --date 2025-08-06 --scenario B
Open-gap gappers (open vs prev close)  price=[1..20]  min_gap=10%
SYMBOL      GAP%    PRICE
OPFI.WS    49.71   2.6200
PHGE       36.78  11.3050
MYGN       33.98   5.1850
AIMD       31.55   3.0650
CYRX       27.60   8.6000
[SCAN] gap_map saved -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250806\scanner\gap_map_2025-08-06.json
[UNIVERSE] Trimmed to Top-5 symbols (from 29)
Wrote 5 symbols -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt
[UNIVERSE] C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt has 5 symbols
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\scripts\fetch_minutes_polygon.py --date 2025-08-06 --session rth
Wrote data\samples\sample_2025-08-06_OPFI.WS.csv
Wrote data\samples\sample_2025-08-06_PHGE.csv
Wrote data\samples\sample_2025-08-06_MYGN.csv
Wrote data\samples\sample_2025-08-06_AIMD.csv
Wrote data\samples\sample_2025-08-06_CYRX.csv
Done. wrote=5 empty=0 failed=0
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe -m midas_v2.cli backtest --date 2025-08-06 --scenario B --universe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt --out C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250806\B
[CFG] scenario= B  gate_minutes= 20  min_rvol_open= 2.0  rvol_open_minutes= 15  green_streak= None  macd_rise_bars= 2  require_macd_rise= True  max_trades_per_symbol= 1  daily_max_loss= 1000.0
2025-12-09 09:14:36,507 [INFO] [WHY] Using StrategyParams: {'dip_reclaim': False, 'gate_minutes': 20, 'green_body_min': 0.22, 'macd_rise_bars': 2, 'min_pm_vol': 30000, 'min_rvol_open': 2.0, 'require_macd_rise': True, 'rise_bars': 3, 'rvol_open_minutes': 15, 'sl_pct': 2.5, 'tp_pct': 2.0}
2025-12-09 09:14:36,511 [INFO] [SIZE] PHGE tier=B risk_usd=35.00 entry=9.8002 sl=9.5552 qty=142

======================================================================
TRADE: PHGE | Side: LONG | Entry: 2025-08-06 09:58 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 36.78%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the take profit was hit.

RESULTS:
• Profit/Loss: $27.83
• This trade made a profit of $27.83.
• Number of shares: 142
• Entry price: $9.80
• Exit price: $10.00
• Profit per share: $0.20
• Sale time: 2025-08-06 10:00

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $9.56)
• Take profit: 2.0% (price: $10.00)

RISK CALCULATION:
• Risk amount (USD): $34.79
• Risk per share: $0.25
• Approximate shares: 34.79 ÷ 0.25 ≈ 142
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:14:36,534 [INFO] [SIZE] MYGN tier=B risk_usd=35.00 entry=5.4450 sl=5.3089 qty=257

======================================================================
TRADE: MYGN | Side: LONG | Entry: 2025-08-06 10:11 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 33.98%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the stop loss was hit.

RESULTS:
• Profit/Loss: $-34.98
• This trade lost $34.98.
• Number of shares: 257
• Entry price: $5.45
• Exit price: $5.31
• Profit per share: $-0.14
• Sale time: 2025-08-06 10:14

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $5.31)
• Take profit: 2.0% (price: $5.55)

RISK CALCULATION:
• Risk amount (USD): $34.98
• Risk per share: $0.14
• Approximate shares: 34.98 ÷ 0.14 ≈ 257
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:14:36,549 [INFO] [SIZE] AIMD tier=B risk_usd=35.00 entry=3.6699 sl=3.5782 qty=381

======================================================================
TRADE: AIMD | Side: LONG | Entry: 2025-08-06 10:52 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 31.55%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the stop loss was hit.

RESULTS:
• Profit/Loss: $-34.96
• This trade lost $34.96.
• Number of shares: 381
• Entry price: $3.67
• Exit price: $3.58
• Profit per share: $-0.09
• Sale time: 2025-08-06 10:53

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $3.58)
• Take profit: 2.0% (price: $3.74)

RISK CALCULATION:
• Risk amount (USD): $34.96
• Risk per share: $0.09
• Approximate shares: 34.96 ÷ 0.09 ≈ 381
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:14:36,565 [INFO] [SIZE] CYRX tier=B risk_usd=35.00 entry=8.9300 sl=8.7067 qty=156

======================================================================
TRADE: CYRX | Side: LONG | Entry: 2025-08-06 10:14 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 27.60%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the stop loss was hit.

RESULTS:
• Profit/Loss: $-34.83
• This trade lost $34.83.
• Number of shares: 156
• Entry price: $8.93
• Exit price: $8.71
• Profit per share: $-0.22
• Sale time: 2025-08-06 10:21

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $8.71)
• Take profit: 2.0% (price: $9.11)

RISK CALCULATION:
• Risk amount (USD): $34.83
• Risk per share: $0.22
• Approximate shares: 34.83 ÷ 0.22 ≈ 156
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

[OK] Backtest complete -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250806\B\results_2025-08-06.csv
[INFO] Running summarize_results.py and streaming output...
B: TP=1 SL=3 Win%=25.00
D: TP=0 SL=0 Win%=0.00
E: TP=0 SL=0 Win%=0.00
[OK] Summary saved -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250806\B\summary_2025-08-06.txt

[OK] Backtest done.
2025-08-06 [B] -> trades=4, wins=1, losses=3, winrate=25.00%, pnl=-76.94
[RUN] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe scripts/run_day_simple.py --date 2025-08-07 --scenario B --session rth
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\scripts\topgappers.py --date 2025-08-07 --scenario B
Open-gap gappers (open vs prev close)  price=[1..20]  min_gap=10%
SYMBOL      GAP%    PRICE
IMG       143.35   9.7340
CNCKW      58.70   1.0000
PALI       49.00   1.4900
YHC        47.50   1.7700
AVAH       36.76   5.3200
[SCAN] gap_map saved -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250807\scanner\gap_map_2025-08-07.json
[UNIVERSE] Trimmed to Top-5 symbols (from 44)
Wrote 5 symbols -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt
[UNIVERSE] C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt has 5 symbols
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\scripts\fetch_minutes_polygon.py --date 2025-08-07 --session rth
Wrote data\samples\sample_2025-08-07_IMG.csv
Wrote data\samples\sample_2025-08-07_CNCKW.csv
Wrote data\samples\sample_2025-08-07_PALI.csv
Wrote data\samples\sample_2025-08-07_YHC.csv
Wrote data\samples\sample_2025-08-07_AVAH.csv
Done. wrote=5 empty=0 failed=0
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe -m midas_v2.cli backtest --date 2025-08-07 --scenario B --universe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt --out C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250807\B
[CFG] scenario= B  gate_minutes= 20  min_rvol_open= 2.0  rvol_open_minutes= 15  green_streak= None  macd_rise_bars= 2  require_macd_rise= True  max_trades_per_symbol= 1  daily_max_loss= 1000.0
2025-12-09 09:15:01,920 [INFO] [WHY] Using StrategyParams: {'dip_reclaim': False, 'gate_minutes': 20, 'green_body_min': 0.22, 'macd_rise_bars': 2, 'min_pm_vol': 30000, 'min_rvol_open': 2.0, 'require_macd_rise': True, 'rise_bars': 3, 'rvol_open_minutes': 15, 'sl_pct': 2.5, 'tp_pct': 2.0}
2025-12-09 09:15:01,924 [INFO] [SIZE] IMG tier=B risk_usd=35.00 entry=9.0980 sl=8.8705 qty=153

======================================================================
TRADE: IMG | Side: LONG | Entry: 2025-08-07 10:56 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 143.35%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the stop loss was hit.

RESULTS:
• Profit/Loss: $-34.80
• This trade lost $34.80.
• Number of shares: 153
• Entry price: $9.10
• Exit price: $8.87
• Profit per share: $-0.23
• Sale time: 2025-08-07 10:56

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $8.87)
• Take profit: 2.0% (price: $9.28)

RISK CALCULATION:
• Risk amount (USD): $34.80
• Risk per share: $0.23
• Approximate shares: 34.80 ÷ 0.23 ≈ 153
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:15:01,940 [INFO] [SIZE] PALI tier=B risk_usd=35.00 entry=1.0800 sl=1.0530 qty=1296

======================================================================
TRADE: PALI | Side: LONG | Entry: 2025-08-07 10:27 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 49.00%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the take profit was hit.

RESULTS:
• Profit/Loss: $27.99
• This trade made a profit of $27.99.
• Number of shares: 1296
• Entry price: $1.08
• Exit price: $1.10
• Profit per share: $0.02
• Sale time: 2025-08-07 10:30

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $1.05)
• Take profit: 2.0% (price: $1.10)

RISK CALCULATION:
• Risk amount (USD): $34.99
• Risk per share: $0.03
• Approximate shares: 34.99 ÷ 0.03 ≈ 1296
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:15:01,956 [INFO] [SIZE] YHC tier=B risk_usd=35.00 entry=1.2800 sl=1.2480 qty=1093

======================================================================
TRADE: YHC | Side: LONG | Entry: 2025-08-07 11:17 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 47.50%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the stop loss was hit.

RESULTS:
• Profit/Loss: $-34.98
• This trade lost $34.98.
• Number of shares: 1093
• Entry price: $1.28
• Exit price: $1.25
• Profit per share: $-0.03
• Sale time: 2025-08-07 11:29

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $1.25)
• Take profit: 2.0% (price: $1.31)

RISK CALCULATION:
• Risk amount (USD): $34.98
• Risk per share: $0.03
• Approximate shares: 34.98 ÷ 0.03 ≈ 1093
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:15:01,977 [INFO] [SIZE] AVAH tier=B risk_usd=35.00 entry=5.9008 sl=5.7533 qty=237

======================================================================
TRADE: AVAH | Side: LONG | Entry: 2025-08-07 09:59 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 36.76%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the take profit was hit.

RESULTS:
• Profit/Loss: $27.97
• This trade made a profit of $27.97.
• Number of shares: 237
• Entry price: $5.90
• Exit price: $6.02
• Profit per share: $0.12
• Sale time: 2025-08-07 10:00

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $5.75)
• Take profit: 2.0% (price: $6.02)

RISK CALCULATION:
• Risk amount (USD): $34.96
• Risk per share: $0.15
• Approximate shares: 34.96 ÷ 0.15 ≈ 237
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

[OK] Backtest complete -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250807\B\results_2025-08-07.csv
[INFO] Running summarize_results.py and streaming output...
B: TP=2 SL=2 Win%=50.00
D: TP=0 SL=0 Win%=0.00
E: TP=0 SL=0 Win%=0.00
[OK] Summary saved -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250807\B\summary_2025-08-07.txt

[OK] Backtest done.
2025-08-07 [B] -> trades=4, wins=2, losses=2, winrate=50.00%, pnl=-13.82
[RUN] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe scripts/run_day_simple.py --date 2025-08-08 --scenario B --session rth
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\scripts\topgappers.py --date 2025-08-08 --scenario B
Open-gap gappers (open vs prev close)  price=[1..20]  min_gap=10%
SYMBOL      GAP%    PRICE
MRM        69.17   2.0300
GCMGW      46.38   1.0100
SPRU       39.32   1.6300
CNCKW      31.58   1.0000
LZ         28.43  10.7500
[SCAN] gap_map saved -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250808\scanner\gap_map_2025-08-08.json
[UNIVERSE] Trimmed to Top-5 symbols (from 52)
Wrote 5 symbols -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt
[UNIVERSE] C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt has 5 symbols
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\scripts\fetch_minutes_polygon.py --date 2025-08-08 --session rth
Wrote data\samples\sample_2025-08-08_MRM.csv
Wrote data\samples\sample_2025-08-08_GCMGW.csv
Wrote data\samples\sample_2025-08-08_SPRU.csv
Wrote data\samples\sample_2025-08-08_CNCKW.csv
Wrote data\samples\sample_2025-08-08_LZ.csv
Done. wrote=5 empty=0 failed=0
[CMD] C:\Users\boydp\AppData\Local\Programs\Python\Python313\python.exe -m midas_v2.cli backtest --date 2025-08-08 --scenario B --universe C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\data\samples\universe_sample.txt --out C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250808\B
[CFG] scenario= B  gate_minutes= 20  min_rvol_open= 2.0  rvol_open_minutes= 15  green_streak= None  macd_rise_bars= 2  require_macd_rise= True  max_trades_per_symbol= 1  daily_max_loss= 1000.0
2025-12-09 09:15:19,823 [INFO] [WHY] Using StrategyParams: {'dip_reclaim': False, 'gate_minutes': 20, 'green_body_min': 0.22, 'macd_rise_bars': 2, 'min_pm_vol': 30000, 'min_rvol_open': 2.0, 'require_macd_rise': True, 'rise_bars': 3, 'rvol_open_minutes': 15, 'sl_pct': 2.5, 'tp_pct': 2.0}
2025-12-09 09:15:19,826 [INFO] [SIZE] MRM tier=B risk_usd=35.00 entry=1.7350 sl=1.6916 qty=806

======================================================================
TRADE: MRM | Side: LONG | Entry: 2025-08-08 11:39 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 69.17%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the take profit was hit.

RESULTS:
• Profit/Loss: $27.97
• This trade made a profit of $27.97.
• Number of shares: 806
• Entry price: $1.74
• Exit price: $1.77
• Profit per share: $0.03
• Sale time: 2025-08-08 11:50

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $1.69)
• Take profit: 2.0% (price: $1.77)

RISK CALCULATION:
• Risk amount (USD): $34.96
• Risk per share: $0.04
• Approximate shares: 34.96 ÷ 0.04 ≈ 806
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:15:19,840 [INFO] [SIZE] SPRU tier=B risk_usd=35.00 entry=1.4049 sl=1.3698 qty=996

======================================================================
TRADE: SPRU | Side: LONG | Entry: 2025-08-08 11:14 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 39.32%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the stop loss was hit.

RESULTS:
• Profit/Loss: $-34.98
• This trade lost $34.98.
• Number of shares: 996
• Entry price: $1.40
• Exit price: $1.37
• Profit per share: $-0.04
• Sale time: 2025-08-08 11:45

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $1.37)
• Take profit: 2.0% (price: $1.43)

RISK CALCULATION:
• Risk amount (USD): $34.98
• Risk per share: $0.04
• Approximate shares: 34.98 ÷ 0.04 ≈ 996
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

2025-12-09 09:15:19,858 [INFO] [SIZE] LZ tier=B risk_usd=35.00 entry=11.6208 sl=11.3303 qty=120

======================================================================
TRADE: LZ | Side: LONG | Entry: 2025-08-08 10:14 | Scenario: B
======================================================================

SCENARIO B – Gap-and-Go:
Buys small cheap stocks that gap up strongly before the market opens
and keep going up after the open, using simple trend and momentum rules.

CONTEXT BEFORE TRADE:
• Gap % at open: 28.43%

RULES WE USED BEFORE TAKING THIS TRADE:
• We waited 20 minutes after the open before entering any trades.
• Before the market opened, the stock needed at least 30,000 shares of activity.
• In the first 15 minutes, today's volume needed to be at least 2.00× yesterday's volume.
• We required 3 recent green candles in a row, each with a strong body (≥ 0.22 of the bar).
• The MACD histogram had to be above zero and rising for 2 bars.
• Take-profit was set at +2.0% and stop-loss was set at –2.5%.
• We only take 1 trade per symbol.

WHY WE TRADED:
• We bought because the stock looked strong according to the rules.
• We sold because the take profit was hit.

RESULTS:
• Profit/Loss: $27.89
• This trade made a profit of $27.89.
• Number of shares: 120
• Entry price: $11.62
• Exit price: $11.85
• Profit per share: $0.23
• Sale time: 2025-08-08 10:46

TRADING PARAMETERS:
• Stop loss: 2.5% (price: $11.33)
• Take profit: 2.0% (price: $11.85)

RISK CALCULATION:
• Risk amount (USD): $34.86
• Risk per share: $0.29
• Approximate shares: 34.86 ÷ 0.29 ≈ 120
• Daily loss limit: we stop trading for the day if total losses reach $1,000.

EXACT SETTINGS FOR REFERENCE:
• Strategy settings: {"dip_reclaim": false, "gate_minutes": 20, "green_body_min": 0.22, "macd_rise_bars": 2, "min_pm_vol": 30000, "min_rvol_open": 2.0, "require_macd_rise": true, "rise_bars": 3, "rvol_open_minutes": 15, "sl_pct": 2.5, "tp_pct": 2.0}
• Risk configuration: {"daily_max_loss": 1000.0, "max_trades_per_symbol": 1}

======================================================================

[OK] Backtest complete -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250808\B\results_2025-08-08.csv
[INFO] Running summarize_results.py and streaming output...
B: TP=2 SL=1 Win%=66.67
D: TP=0 SL=0 Win%=0.00
E: TP=0 SL=0 Win%=0.00
[OK] Summary saved -> C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working\out\20250808\B\summary_2025-08-08.txt

[OK] Backtest done.
2025-08-08 [B] -> trades=3, wins=2, losses=1, winrate=66.67%, pnl=+20.88
[SKIP] 2025-08-09 (weekend)
[SKIP] 2025-08-10 (weekend)

=== TOTALS ===
[B] trades=22, wins=7, losses=15, winrate=31.82%, totalPnL=-328.67

[OK] Range summary CSV -> out\auto\range_summary_20250801_20250810_B.csv
PS C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working>
PS C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working>
PS C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working>
PS C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working>
PS C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working>