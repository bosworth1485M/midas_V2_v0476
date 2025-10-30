param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Date,
    [string]$Universe = "data/samples/universe_sample.txt",
    [string[]]$Scenarios = @("A","B","C","D")
)

# Normalize: if Scenarios was passed as a single comma-separated string, split it
if ($Scenarios.Count -eq 1 -and $Scenarios[0] -match ",") {
    $Scenarios = $Scenarios[0].Split(",") | ForEach-Object { $_.Trim() }
}


# Run from project root and expose src/ to Python
Set-Location "$PSScriptRoot\.."
$env:PYTHONPATH = (Get-Location).Path + "\src"

# Prepare output root: out\YYYYMMDD
$yyyymmdd = ($Date -replace '-', '')
$outRoot  = Join-Path 'out' $yyyymmdd
if (-not (Test-Path $outRoot)) {
    New-Item -ItemType Directory -Path $outRoot | Out-Null
}

foreach ($S in $Scenarios) {
    Write-Host ("Running scenario {0}..." -f $S) -ForegroundColor Cyan

    $outDir = Join-Path $outRoot $S
    if (-not (Test-Path $outDir)) {
        New-Item -ItemType Directory -Path $outDir | Out-Null
    }

    & python -m midas_v2.cli backtest `
        --date $Date `
        --universe $Universe `
        --scenario $S `
        --out $outDir

    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-Host ("[ERR] Scenario {0} exited {1}" -f $S, $code) -ForegroundColor Red
        exit $code
    } else {
        Write-Host ("[ OK ] Scenario {0} done." -f $S) -ForegroundColor Green
    }

    Write-Host ""
}

Write-Host "All scenarios finished." -ForegroundColor Green
exit 0