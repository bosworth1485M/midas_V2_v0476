Midas_V2 — Scenario B Baseline Checkpoint

Date: 2025-09-02

🔑 What We Did Today

Added guardrails to the engine & CLI

--max-trades-per-symbol (default 1)

--daily-max-loss (default 1000)

Enforced in cli.py and backtester.py.

Now Scenario B only takes one trade per ticker and stops trading after -$1000 cumulative loss.

Updated Scenario B config (config/scenarios.json)

Price filter: $1–$20

Gap filter: min_gap_pct=10, max_gap_pct=40

EMA + VWAP + MACD confirmations enabled

TP = 2.0%, SL = 2.5%, gate = 10 minutes, min_pm_vol = 30k

Refreshed documentation

Ran Docs\Refresh-Docs.ps1 to regenerate Docs\DEV_GUIDE.md.

Verified Scenario B shows Cameron-style filters in the guide
.

Smoke test on 2025-08-05

Universe: STTK only

Result: one clean trade, TP +2.04.

Verified guardrails prevented repeat trades.

✅ Achievements

Scenario B is now aligned with Ross Cameron’s baseline rules.

Guardrails prevent over-trading and runaway losses.

Documentation is up to date and reflects the new parameters.

Git tag process in place (v0.3.2-b-baseline-gap10-guardrails) so this exact state can be restored anytime.

First successful run confirmed: one disciplined trade, profitable outcome.

▶️ Run Commands
1. Single-day run (Scenario B)
.\scripts\run_backtest.ps1 -Date 2025-08-05 -Scenario B

2. Multi-day run (Scenario B only)
$dates = '2025-08-05','2025-08-06','2025-08-07'
foreach ($d in $dates) {
  .\scripts\run_backtest.ps1 -Date $d -Scenario B
}

3. Summarize results

Range (if supported):

.\scripts\Summarize-Scenarios.ps1 -Start 2025-08-05 -End 2025-08-07


Per day:

$dates = '2025-08-05','2025-08-06','2025-08-07'
foreach ($d in $dates) {
  .\scripts\Summarize-Scenarios.ps1 -Date $d
}

4. Refresh docs
.\Docs\Refresh-Docs.ps1

5. Git versioning (save everything)
git add -A
git commit -m "Checkpoint: Scenario B Cameron baseline (gap>=10, $1–$20) + guardrails (max 1 trade/symbol, daily max loss); docs refreshed"
git tag -a v0.3.2-b-baseline-gap10-guardrails -m "Scenario B baseline locked: gap>=10, price 1–20, EMA+VWAP+MACD, TP 2.0/SL 2.5, gate 10, min_pm_vol 30k; guardrails added"
git push && git push --tags

🔜 Next Test Steps

Run Scenario B across multiple dates (2025-08-05 to 2025-08-07) using run_backtest.ps1 and confirm:

some days may show “no trades” (expected if no ticker met B rules),

summary output aligns with Cameron-style expectations (fewer but higher-quality trades).

Test with per-day top gappers

Use data/universe_topgappers_YYYY-MM-DD.txt instead of universe_sample.txt for Aug-06 and Aug-07 to validate real candidates.

Summarize multi-day runs with Summarize-Scenarios.ps1 to check win rate and PnL across days.

Evaluate quality

If trades are too few: consider carefully loosening filters (e.g., min_gap_pct 8 instead of 10, or min_pm_vol).

If trades appear but are noisy: keep filters strict.

Tag new version once multi-day runs are stable and reviewed (e.g., v0.3.3-b-multi-day-baseline).