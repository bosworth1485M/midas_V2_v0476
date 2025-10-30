@echo off
REM Run from project root and expose src/ to Python
cd /d %~dp0..
set "PYTHONPATH=%cd%\src"

set DATE=2025-08-05
set UNIVERSE=data\samples\universe_sample.txt

for %%S in (A B C D) do (
  echo Running scenario %%S...
  python -m midas_v2.cli backtest --date %DATE% --universe %UNIVERSE% --scenario %%S --out out\%DATE:-=%\%%S
)

pause
