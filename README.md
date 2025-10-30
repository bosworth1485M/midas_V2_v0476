# Midas_V2

A flexible, Cameron-style small-cap momentum framework with clear separation between:
- **backtesting** and **live/paper trading**
- **data providers** and **brokers** (pluggable)
- **strategies**, **risk**, and **execution**

## Highlights
- Paper/Live switch via config or `--mode` argument
- Broker abstraction with Alpaca stub (easy to extend to Lightspeed, etc.)
- Safety checks: max daily loss, max per-trade risk, circuit breaker, cooldown after losses
- 4 scenario presets (A, B, C, D) inspired by common open/playbook variations
- Clean logging (rotating files) + run artifacts folder per date
- Windows-friendly runners (`.cmd` and PowerShell)

## Quickstart
```bash
# (optional) create venv then install
python -m venv .venv && .venv\Scripts\pip install -r requirements.txt

# A smoke test backtest on bundled sample data
python -m midas_v2.cli backtest --date 2025-08-05 --universe data/samples/universe_sample.txt --scenario B --out out\smoketest
```
On Windows CMD, use `scripts\run_backtest.cmd`.
On PowerShell, use `scripts\run_backtest.ps1`.

## Structure
```
midas_V2/
  config/
    midas.toml                # global settings
    scenarios.json            # A/B/C/D definitions
  data/samples/
    sample_2025-08-05_STTK.csv
    universe_sample.txt
  src/midas_v2/
    __init__.py
    cli.py
    settings.py
    utils_logging.py
    risk.py
    strategy.py
    datamodel.py
    dataprov/
      __init__.py
      base.py
      csv_local.py
    broker/
      __init__.py
      base.py
      alpaca_stub.py
    engine/
      __init__.py
      backtester.py
      live.py
  scripts/
    run_backtest.cmd
    run_backtest.ps1
    run_all_scenarios.cmd
    run_all_scenarios.ps1
requirements.txt
README.md
```

## Notes
- This is a **starter**; you can drop in your real data provider (Polygon, SIP) later.
- Execution in live/paper is disabled by default and runs in **dry-run** unless explicitly allowed.
