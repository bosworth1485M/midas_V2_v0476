# scripts\Get-TopGappers.ps1
param(
  [Parameter(Mandatory=$true)][string]$Date,   # e.g. 2025-08-05
  [switch]$Freeze                              # preview by default; write files only if -Freeze
)

function Get-PolygonKey {
  if ($env:POLYGON_API_KEY) {
    return ($env:POLYGON_API_KEY -replace '[\s\r\n\t]','')
  }
  $envPath = Join-Path (Get-Location) '.env'
  if (Test-Path $envPath) {
    $line = (Get-Content -Raw $envPath) -split "`r?`n" | Where-Object { $_ -match '^POLYGON_API_KEY\s*=' } | Select-Object -First 1
    if ($line) { return (($line -replace '^POLYGON_API_KEY\s*=\s*','').Trim().Trim('"').Trim("'") -replace '[\s\r\n\t]','') }
  }
  throw "[ERR] POLYGON_API_KEY missing (set env var or add to .env)"
}

# ---- Load config (one place for knobs) ----
$cfgPath = "config\topgappers.json"
$cfg = @{
  gap_basis       = 'open'  # 'open' or 'close'
  min_price       = 1.0
  max_price       = 20.0
  min_gap         = 5.0
  top_n           = 8
  set_universe    = $false
}
if (Test-Path $cfgPath) {
  try {
    $raw = Get-Content -Raw $cfgPath | ConvertFrom-Json
    $keys=@($cfg.Keys); foreach($k in $keys){ if ($raw.PSObject.Properties.Name -contains $k) { $cfg[$k] = $raw.$k } }
  } catch { Write-Warning "[WARN] Failed to parse ${cfgPath}: $($_.Exception.Message)" }
}

# ---- Fetch grouped daily for prev day & target day ----
$k   = Get-PolygonKey
$hdr = @{ 'X-Polygon-API-Key' = $k }
$y   = ([datetime]::Parse($Date).AddDays(-1).ToString('yyyy-MM-dd'))
$uPrev  = "https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/$y?adjusted=true&apiKey=$k"
$uToday = "https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/$Date?adjusted=true&apiKey=$k"

try { $prevAgg = Invoke-RestMethod -Uri $uPrev -TimeoutSec 60 } catch { throw "[ERR] prev-day fetch failed: $($_.Exception.Message)" }
try { $todayAgg= Invoke-RestMethod -Uri $uToday -TimeoutSec 60 } catch { throw "[ERR] today fetch failed: $($_.Exception.Message)" }

# ---- Build prev close map (use exact property names via PSObject.Properties) ----
$prevClose = @{}
foreach ($r in $prevAgg.results) {
  $sym = $r.PSObject.Properties['T'].Value
  if ($sym) { $prevClose[$sym] = [double]($r.PSObject.Properties['c'].Value) }
}

# ---- Compute gaps (open or close basis per config), filter, sort ----
$rows = New-Object System.Collections.Generic.List[object]
foreach ($r in $todayAgg.results) {
  $sym = $r.PSObject.Properties['T'].Value
  if (-not $sym) { continue }
  if (-not $prevClose.ContainsKey($sym)) { continue }
  $basis = if ($cfg.gap_basis -eq 'open') { [double]($r.PSObject.Properties['o'].Value) } else { [double]($r.PSObject.Properties['c'].Value) }
  $pc    = [double]$prevClose[$sym]
  if ($pc -le 0) { continue }
  $gapPct = (($basis - $pc) / $pc) * 100.0
  if ($basis -ge [double]$cfg.min_price -and $basis -le [double]$cfg.max_price -and $gapPct -ge [double]$cfg.min_gap) {
    $rows.Add([pscustomobject]@{ symbol=$sym; gap=[math]::Round($gapPct,2); price=[math]::Round($basis,4) })
  }
}

# ---- Preview (always) ----
"Top gappers preview: basis={0}  price=[{1}..{2}]  min_gap={3}%  top_n={4}" -f $cfg.gap_basis,$cfg.min_price,$cfg.max_price,$cfg.min_gap,$cfg.top_n | Write-Host
$rows | Sort-Object gap -Descending | Select-Object -First ([int]$cfg.top_n) | Format-Table symbol,gap,price -AutoSize

# ---- Freeze outputs only if requested ----
if ($Freeze) {
  $suffix = if ($cfg.gap_basis -eq 'open') { '_opengap' } else { '_closegap' }
  $txt = "data/samples/universe_topgappers_${Date}${suffix}.txt"
  $csv = "data/samples/topgappers_${Date}${suffix}.csv"
  New-Item -ItemType Directory -Force (Split-Path $txt) | Out-Null
  ($rows | Sort-Object gap -Descending | Select-Object -ExpandProperty symbol -First ([int]$cfg.top_n)) -join "`r`n" | Set-Content $txt -Encoding ASCII
  ($rows | Sort-Object gap -Descending | Select-Object -First ([int]$cfg.top_n)) | Export-Csv $csv -NoTypeInformation
  "Wrote: $txt" | Write-Host
  "Wrote: $csv" | Write-Host
  if ($cfg.set_universe) {
    Get-Content $txt | Set-Content "data/samples/universe_sample.txt"
    "Updated data/samples/universe_sample.txt" | Write-Host
  }
}

