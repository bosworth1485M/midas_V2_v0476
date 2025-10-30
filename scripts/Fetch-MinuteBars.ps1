# scripts\Fetch-MinuteBars.ps1
param(
  [Parameter(Mandatory = $true)][string]$Date,                  # e.g. 2025-08-05
  [string]$UniversePath = "data/samples/universe_sample.txt"
)

function Get-PolygonKey {
  if ($env:POLYGON_API_KEY) { return $env:POLYGON_API_KEY }
  $envPath = Join-Path (Get-Location) '.env'
  if (Test-Path $envPath) {
    $line = (Select-String -Path $envPath -Pattern '^POLYGON_API_KEY=' -ErrorAction SilentlyContinue | Select-Object -First 1).Line
    if ($line) { return ($line -split '=',2)[1].Trim() }
  }
  throw "[ERR] POLYGON_API_KEY not found in env or .env"
}

if (-not (Test-Path $UniversePath)) { throw "[ERR] Universe file not found: $UniversePath" }
$symbols = Get-Content $UniversePath | ? { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique
if (-not $symbols) { throw "[ERR] Universe file is empty: $UniversePath" }

$k   = Get-PolygonKey
$to  = ([datetime]::Parse($Date).AddDays(1).ToString('yyyy-MM-dd'))
$ok  = 0; $fail = 0

foreach ($sym in $symbols) {
  $url = "https://api.polygon.io/v2/aggs/ticker/$sym/range/1/minute/$Date/$to?adjusted=true&sort=asc&limit=50000&apiKey=$k"
  try {
    $resp = Invoke-RestMethod -Uri $url -TimeoutSec 60
    if (-not $resp.results) { Write-Warning "[WARN] No minute bars for $sym"; $fail++; continue }
    $rows = @('time,open,high,low,close,volume')
    foreach ($x in $resp.results) {
      $ts = [DateTimeOffset]::FromUnixTimeMilliseconds($x.t).ToLocalTime().ToString('HH:mm')
      $rows += ("{0},{1},{2},{3},{4},{5}" -f $ts,$x.o,$x.h,$x.l,$x.c,$x.v)
    }
    $out = "data/samples/sample_${Date}_${sym}.csv"
    New-Item -ItemType Directory -Force (Split-Path $out) | Out-Null
    ($rows -join "`r`n") | Set-Content $out -Encoding ASCII
    $ok++
  } catch {
    Write-Warning "[WARN] $sym download failed: $($_.Exception.Message)"; $fail++
  }
}

Write-Host ("Minute data downloaded: OK={0}, FAIL={1}" -f $ok,$fail)