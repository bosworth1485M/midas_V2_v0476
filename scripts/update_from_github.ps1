# === Update from GitHub (safe) ===
Set-Location "$PSScriptRoot\.."

if (-not (Test-Path ".git")) {
  Write-Host "[ERR] .git folder not found. Are you in C:\Users\boydp\Desktop\midas_V2 ?" -ForegroundColor Red
  Pause
  exit 1
}

$hasChanges = (git status --porcelain) -ne ""
if ($hasChanges) {
  Write-Host "[INFO] Stashing local changes..."
  git stash push -u -m "auto-stash before pull" | Out-Null
  $stashed = $true
}

Write-Host "[INFO] Fetching..."
git fetch --all

Write-Host "[INFO] Pulling latest (rebase)..."
git pull --rebase

if ($stashed) {
  Write-Host "[INFO] Restoring stashed changes..."
  git stash pop
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] Stash pop had conflicts. Resolve them, then run:" -ForegroundColor Yellow
    Write-Host "       git add -A"
    Write-Host "       git rebase --continue   (or)   git commit"
  }
}

Write-Host "[OK] Up to date."
Pause