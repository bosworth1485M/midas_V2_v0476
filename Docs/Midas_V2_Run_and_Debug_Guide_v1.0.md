Successful run — exact sequence (what should happen)

You run:

python scripts/run_day_simple.py --date 2025-08-07 --scenario E

0) Parse & setup

Creates (if missing): out\20250807\E\

No output yet except possible [WARN] Expected helper not found: ... if a helper is missing.

1) Build universe (top gappers)

Runs:

[CMD] <python> scripts/topgappers.py --date 2025-08-07 --no-write


Writes/overwrites: data\samples\universe_sample.txt (one symbol per line)

You’ll see a list of gappers and then:

[UNIVERSE] ...\data\samples\universe_sample.txt has <N> symbols

2) Fetch minute bars (Polygon)

Runs:

[CMD] <python> scripts/fetch_minutes_polygon.py --date 2025-08-07 --session rth


Writes/overwrites (one per symbol):

data\samples\sample_2025-08-07_<SYMBOL>.csv


Ends with something like:

Done. wrote=28 empty=0 failed=0

3) Backtest the scenario

Runs:

[CMD] <python> -m midas_v2.cli backtest --date 2025-08-07 --scenario E --universe data\samples\universe_sample.txt --out out\20250807\E


Writes/overwrites:

out\20250807\E\results_2025-08-07.csv


Shows:

[INFO] [WHY] Using StrategyParams: {...}
[OK] Backtest complete -> ...\out\20250807\E\results_2025-08-07.csv

4) Auto-summarize & save (new behavior)

Runs internally:

<python> scripts/summarize_results.py --date 2025-08-07


Saves captured summary to:

out\20250807\E\summary_2025-08-07.txt


Shows:

[OK] Summary saved -> out\20250807\E\summary_2025-08-07.txt


Finishes with:

[OK] Backtest done.

Quick verification (copy–paste checks)
dir .\out\20250807\E\
Get-Content .\out\20250807\E\summary_2025-08-07.txt -Head 20
(Get-Content .\out\20250807\E\results_2025-08-07.csv | Measure-Object -Line).Lines

🛠️ Errors & debugging — sequence + fixes

Below are the same four stages, but with what to check, typical errors, and one-liner fixes.

1) Universe build problems

Symptom: No [UNIVERSE] ... has N symbols, or N is 0, or command fails.

Check:

Test-Path .\scripts\topgappers.py
Get-Content .\data\samples\universe_sample.txt -Head 20


Likely causes & fixes:

Missing script → confirm file exists in scripts\.

Empty universe due to scanner filters → temporarily cap to Top-12:

(Get-Content .\data\samples\universe_sample.txt | Select-Object -First 12) | Set-Content .\data\samples\universe_sample.txt

2) Minute fetch problems (Polygon)

Symptom: No “Wrote data\samples\sample_<DATE>_<SYMBOL>.csv”, or many failed, or HTTP/401.

Check:

dir .\data\samples\sample_2025-08-07_*.csv


Likely causes & fixes:

401/403 → Polygon API key not loaded in environment. Re-load your key (as you normally do) and rerun fetch.

Network hiccup → rerun just the fetch step:

$D='2025-08-07'; python scripts/fetch_minutes_polygon.py --date $D --session rth

3) Backtest problems

Symptom: No results CSV, or CSV is header-only (1 line), or params look wrong.

Checks:

$csv='.\\out\\20250807\\E\\results_2025-08-07.csv'; (Get-Content $csv | Measure-Object -Line).Lines
Get-Content $csv -Head 10
Import-Csv $csv | Group-Object outcome | Select Name,Count | Format-Table -Auto


Interpretation:

1 line only = no valid trades met criteria (normal on some days when guards are strict).

Many losers = noisy universe; consider Top-12 (below) or raise min_pm_vol for B.

Bypass runner to see exact params:

python -m midas_v2.cli backtest --date 2025-08-07 --scenario B --universe data\samples\universe_sample.txt --out out\20250807\B


Confirm Scenario B config didn’t drift:

Select-String -Path .\config\scenarios.toml -Pattern '^\[scenario\.B\]|^vwap_confirm|^ema_confirm|^macd_confirm|^gate_minutes|^tp_pct|^sl_pct|^min_pm_vol|^dip_reclaim|^reclaim' -Context 0,1


Low-friction improvements (no code changes):

Trim to Top-12 before fetching minutes/backtest:

(Get-Content .\data\samples\universe_sample.txt | Select-Object -First 12) | Set-Content .\data\samples\universe_sample.txt


Optionally raise B’s premarket volume filter (e.g., 75k):

$path='.\config\scenarios.toml'; $lines=Get-Content $path -Raw -Encoding UTF8; $pattern="(\[scenario\.B\][\s\S]*?min_pm_vol\s*=\s*)\d+"; $new=$lines -replace $pattern,'${1}75000'; [IO.File]::WriteAllText($path,$new,[Text.UTF8Encoding]::new($false))

4) Summary save problems

Symptom: CSV exists but no summary_<DATE>.txt, or warning:

[WARN] summarize_results.py failed (exit N). Skipping save.


Checks:

Test-Path .\scripts\summarize_results.py
python scripts/summarize_results.py --date 2025-08-07


Fix (manual save if needed):

$D='2025-08-07'; $S='E'; $D8=$D -replace '-',''; $out="out\$D8\$S"; if(!(Test-Path $out)){ New-Item -ItemType Directory -Path $out | Out-Null }; python scripts/summarize_results.py --date $D | Out-File -Encoding UTF8 "$out\summary_$D.txt"

Minimal sanity control (use only if you suspect a regression)

Single known-good check for B on 2025-08-05 (STTK):

@('STTK') | Set-Content -Encoding ASCII .\data\samples\universe_sample.txt; python -m midas_v2.cli backtest --date 2025-08-05 --scenario B --universe data\samples\universe_sample.txt --out out\20250805\B; python scripts/summarize_results.py --date 2025-08-05


You should see B: TP=1 SL=0 in the summary (and the runner also auto-saves a summary when you use it).