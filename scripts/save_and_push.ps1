# === Save and Push helper for Midas_V2 ===
Set-Location "$PSScriptRoot\.."

$MSG = Read-Host "Enter commit message"
if ([string]::IsNullOrWhiteSpace($MSG)) {
    $MSG = "Update from save_and_push.ps1"
}

Write-Host "[INFO] Adding all changes..."
git add -A

Write-Host "[INFO] Committing with message: $MSG"
git commit -m "$MSG"

Write-Host "[INFO] Pushing to GitHub..."
git push

Write-Host "[OK] Done."
Pause