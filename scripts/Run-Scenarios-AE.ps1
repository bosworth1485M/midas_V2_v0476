# scripts\Run-Scenarios-AE.ps1
param(
  [Parameter(Mandatory = $true)][string]$Date,                     # e.g. 2025-08-05
  [string]$UniversePath = "data/samples/universe_sample.txt"
)

if (-not (Test-Path $UniversePath)) { throw "[ERR] Universe file not found: $UniversePath" }
$yy = ($Date -replace '-','')
$scenarios = @('A','B','C','D','E')

foreach ($s in $scenarios) {
  $outDir = ("out\{0}\{1}" -f $yy,$s)
  $cmd = "python -m midas_v2.cli backtest --date $Date --scenario $s --universe `"$UniversePath`" --out `"$outDir`""
  Write-Host "[RUN] $cmd"
  & python -m midas_v2.cli backtest --date $Date --scenario $s --universe $UniversePath --out $outDir
}

# Summarize
$glob = ("out\{0}\*\results_{1}.csv" -f $yy,$Date)
$files = Get-ChildItem $glob -ErrorAction SilentlyContinue
if (-not $files) { Write-Host "[INFO] No results CSVs found."; exit 0 }

foreach ($f in $files) {
  $sc = Split-Path $f.DirectoryName -Leaf
  $csv = Import-Csv $f.FullName
  $tp  = ($csv | ? { $_.outcome -eq 'TP' }).Count
  $sl  = ($csv | ? { $_.outcome -eq 'SL' }).Count
  $tot = $tp + $sl
  $win = if ($tot -gt 0) { [math]::Round(100.0*$tp/$tot,2) } else { 0 }
  "{0}: TP={1} SL={2} Win%={3} (rows={4})" -f $sc,$tp,$sl,$win,$csv.Count | Write-Host
}