@echo off
REM === One-click Git setup for Midas_V2 ===
cd /d %~dp0..
if not exist .git (
    echo [INFO] Initializing git repository...
    git init
) else (
    echo [INFO] Git repository already exists.
)

REM Write .gitignore if it doesn't exist
if not exist .gitignore (
    echo [INFO] Creating .gitignore...
    > .gitignore echo # Python
    >> .gitignore echo __pycache__/
    >> .gitignore echo *.pyc
    >> .gitignore echo *.pyo
    >> .gitignore echo *.pyd
    >> .gitignore echo *.so

    >> .gitignore echo.
    >> .gitignore echo # Virtual envs
    >> .gitignore echo .venv/
    >> .gitignore echo env/
    >> .gitignore echo venv/

    >> .gitignore echo.
    >> .gitignore echo # OS cruft
    >> .gitignore echo .DS_Store
    >> .gitignore echo Thumbs.db

    >> .gitignore echo.
    >> .gitignore echo # IDE configs
    >> .gitignore echo .vscode/
    >> .gitignore echo .idea/

    >> .gitignore echo.
    >> .gitignore echo # Logs and outputs
    >> .gitignore echo logs/
    >> .gitignore echo out/

    >> .gitignore echo.
    >> .gitignore echo # Data
    >> .gitignore echo data/raw/
    >> .gitignore echo data/tmp/
    >> .gitignore echo *.csv
    >> .gitignore echo *.parquet

    >> .gitignore echo.
    >> .gitignore echo # Secrets
    >> .gitignore echo .env
    >> .gitignore echo *.key
    >> .gitignore echo *.pem

    >> .gitignore echo.
    >> .gitignore echo # Checkpoints / temp
    >> .gitignore echo *.bak
    >> .gitignore echo *.swp
    >> .gitignore echo *.tmp
)

git add -A
git commit -m "Initial commit of Midas_V2 starter" || echo [INFO] Nothing new to commit.
echo [OK] Git setup complete.
pause
