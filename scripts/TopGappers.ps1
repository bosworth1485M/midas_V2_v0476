# scripts\TopGappers.ps1
param(
  [Parameter(Mandatory=$true)][string]$Date,   # e.g. 2025-08-05
  [double]$MinPrice = 1.0,
  [double]$MaxPrice = 20.0,
  [double]$MinGap   = 5.0,     # percent
  [int]   $Top      = 50,      # how many to print
  [switch]$NoWrite              # use --NoWrite to avoid touching universe_sample.txt
)

function Get-PolygonKey {
  $k = ($env:POLYGON_API_KEY -replace '\s','')
  if (-not $k) {
    $envPath = Join-Path (Get-Location) '.env'
    if (Test-Path $envPath) {
      $line = (Get-Content -Raw $envPath) -split "`r?`n" |
              Where-Object { $_ -match '^POLYGON_API_KEY\s*=' } |
              Select-Object -First 1
      if ($line) { $k = (($line -replace '^POLYGON_API_KEY\s*=\s*','').Trim().Trim('"').Trim("'")) -replace '\s','' }
    }
  }
  if (-not $k) { throw "[ERR] POLYGON_API_KEY missing (set env var or add to .env)" }
  return $k
}

try {
  $k = Get-PolygonKey
  $headers = @{ 'X-Polygon-API-Key' = $k; 'Authorization' = ('Bearer '+$k) }

  $prevDate = ([datetime]::Parse($Date).AddDays(-1)).ToString('yyyy-MM-dd')
  $uPrev  = "https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/$prevDate?adjusted=true&apiKey=$k"
  $uToday = "https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/$Date?adjusted=true&apiKey=$k"

  # Use -creplace so only lowercase "t" (timestamp) is renamed; uppercase "T" (ticker) is preserved
  $rawPrev  = (Invoke-WebRequest -Uri $uPrev  -Headers $headers -TimeoutSec 60).Content
  $rawToday = (Invoke-WebRequest -Uri $uToday -Headers $headers -TimeoutSec 60).Content
  $prevAgg  = ($rawPrev  -creplace '"t":','"ts":') | ConvertFrom-Json
  $todayAgg = ($rawToday -creplace '"t":','"ts":') | ConvertFrom-Json

  # Map previous CLOSE by ticker
  $prevClose = @{}
  foreach ($r in $prevAgg.results) {
    $sym = $r.PSObject.Properties['T'].Value
    if ($sym) { $prevClose[$sym] = [double]$r.PSObject.Properties['c'].Value }
  }

  # Compute OPEN-GAP vs prev close; filter by price band and gap threshold
  $rows = foreach ($r in $todayAgg.results) {
    $sym = $r.PSObject.Properties['T'].Value
    if (-not $sym) { continue }
    if (-not $prevClose.ContainsKey($sym)) { continue }
    $o  = [double]$r.PSObject.Properties['o'].Value
    $pc = [double]$prevClose[$sym]
    if ($pc -le 0) { continue }
    $gap = (($o - $pc) / $pc) * 100.0
    if ($o -ge $MinPrice -and $o -le $MaxPrice -and $gap -ge $MinGap) {
      [pscustomobject]@{ symbol = $sym; gap = [math]::Round($gap,2); price = [math]::Round($o,4) }
    }
  }

  $rows = $rows | Sort-Object gap -Descending
  "Open-gap gappers (open vs prev close)  price=[{0}..{1}]  min_gap={2}%  count={3}" -f $MinPrice,$MaxPrice,$MinGap,($rows.Count) | Write-Host
  if ($rows.Count -gt 0) {
    $rows | Select-Object -First $Top | Format-Table symbol,gap,price -AutoSize
  } else {
    "(none)" | Write-Host
  }

  if (-not $NoWrite) {
    $outp = 'data/samples/universe_sample.txt'
    New-Item -ItemType Directory -Force (Split-Path $outp) | Out-Null
    ($rows | Select-Object -ExpandProperty symbol) -join "`r`n" | Set-Content $outp -Encoding ASCII
    "Wrote {0} symbols -> {1}" -f $rows.Count,$outp | Write-Host
  }

} catch {
  Write-Error $_.Exception.Message
  exit 1
}