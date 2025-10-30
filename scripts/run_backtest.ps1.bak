# Run from project root and expose src/ to Python
Set-Location "$PSScriptRoot\.."
$env:PYTHONPATH = (Get-Location).Path + "\src"

param(
  [string]$Date = "2025-08-05",
  [string]$Universe = "data/samples/universe_sample.txt",
  [ValidateSet("A","B","C","D")][string]$Scenario = "B",
  [string]$Out = "out/smoketest"
)
python -m midas_v2.cli backtest --date $Date --universe $Universe --scenario $Scenario --out $Out
Pause
