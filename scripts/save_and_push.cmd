@echo off
REM === Save and Push helper for Midas_V2 ===
cd /d %~dp0..

set /p MSG="Enter commit message: "

if "%MSG%"=="" (
    set MSG=Update from save_and_push.cmd
)

echo [INFO] Adding all changes...
git add -A

echo [INFO] Committing with message: %MSG%
git commit -m "%MSG%"

echo [INFO] Pushing to GitHub...
git push

echo [OK] Done.
pause
