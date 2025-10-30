@echo off
REM === Update from GitHub (safe) ===
cd /d %~dp0..

if not exist .git (
  echo [ERR] .git folder not found. Are you in C:\Users\boydp\Desktop\midas_V2 ?
  pause
  exit /b 1
)

REM Check for uncommitted changes
set CHANGES=
for /f "delims=" %%A in ('git status --porcelain') do set CHANGES=1

if defined CHANGES (
  echo [INFO] Stashing local changes...
  git stash push -u -m "auto-stash before pull" >nul
  set STASHED=1
)

echo [INFO] Fetching...
git fetch --all

echo [INFO] Pulling latest (rebase)...
git pull --rebase

if defined STASHED (
  echo [INFO] Restoring stashed changes...
  git stash pop
  if errorlevel 1 (
    echo [WARN] Stash pop had conflicts. Resolve them, then:
    echo        git add -A
    echo        git rebase --continue   (or)   git commit
  )
)

echo [OK] Up to date.
pause
