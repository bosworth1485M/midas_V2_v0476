# Midas_V2 — B Baseline Summary & Commands
_Date: 2025-09-01 (America/Chicago)_

## What’s locked in
- **Scenario B = B_safe** (promoted):  
  - `tp_pct=2.0`, `sl_pct=2.5`, `macd_confirm=True`, `gate_minutes=10`, `min_pm_vol=30000`, `ema_confirm=True`, `vwap_confirm=True`, `rise_bars=2`.
- **Runner**: `scripts/run_day_simple.py` (v1.2.2) with auto-sanitize + auto-filter (defaults: gap ≥ 8%, price $1–$10, exclude dot-suffix tickers, Top-40).
- **Git tag**: `v0.5.5-B-baseline` (current working baseline).

---

## Results (Scenario B)
- **2025-08-05** — trades **25**, wins **12**, losses **13**, **PnL -67.40**
- **2025-08-06** — trades **38**, wins **25**, losses **13**, **PnL +174.33**
- **2025-08-07** — trades **15**, wins **7**, losses **8**, **PnL -7.17**
- **2025-08-12** — trades **15**, wins **8**, losses **7**, **PnL +23.35**
- **2025-08-13** — trades **17**, wins **10**, losses **7**, **PnL +3.98**

**Multi-day total (5 sessions)**  
- Trades **95**, Wins **55**, Losses **40**, **Win rate 57.89%**, **Total PnL +134.26**  
- Days: Positive **3**, Negative **1**, Flat **0**

> Takeaway: We’re close to the ~60%+ target and net positive overall. Aug 6 strong; Aug 12 & 13 green; Aug 5 & 7 modest drawdowns.

---

## One-day workflow (pure Python)

### Run a single day (fetch → sanitize → filter → backtest)
_Use these typical flags for a clean Ross-style universe_
```bash
python scripts/run_day_simple.py --date YYYY-MM-DD --scenarios B --refresh-samples --min-gap 10 --limit 30
```
_Defaults if you omit flags: gap ≥ 8%, price $1–$10, exclude dot-suffix, Top-40._

### Summarize a single day
```bash
python scripts/summarize_pnl.py --date YYYY-MM-DD --scenarios B
```

### Compare multiple days (already installed)
```bash
python scripts/summarize_multi.py --dates 2025-08-05,2025-08-06,2025-08-07,2025-08-12,2025-08-13 --scenario B
```

---

## Handy one-liners (optional tweaks, no PowerShell)

### Promote B = D (already done; shown for reference)
```bash
python -c "import json, pathlib; p=pathlib.Path('config/scenarios.json'); d=json.loads(p.read_text(encoding='utf-8')); d['B_backup']=d.get('B'); d['B']={'params': d['D']['params']}; p.write_text(json.dumps(d, indent=2), encoding='utf-8')"
```

### Switch risk to 2.0 / 2.0 (higher expectancy; optional)
```bash
python -c "import json, pathlib; p=pathlib.Path('config/scenarios.json'); d=json.loads(p.read_text(encoding='utf-8')); b=d['B']['params']; b['tp_pct']=2.0; b['sl_pct']=2.0; p.write_text(json.dumps(d, indent=2), encoding='utf-8')"
```

### Restore the 2.0 / 2.5 baseline (current)
```bash
python -c "import json, pathlib; p=pathlib.Path('config/scenarios.json'); d=json.loads(p.read_text(encoding='utf-8')); b=d['B']['params']; b['tp_pct']=2.0; b['sl_pct']=2.5; p.write_text(json.dumps(d, indent=2), encoding='utf-8')"
```

---

## Next steps
1. **Broaden validation**: Run a few more dates and add them to `summarize_multi.py`.
2. **Universe hygiene knobs** (add to run command as needed):  
   - `--min-gap 12` for stronger gaps  
   - `--max-price 8` to bias toward smaller names  
   - `--limit 20–30` to avoid noisy long lists
3. **Risk plan toward $500/day** (60% WR target):  
   - Keep `TP=2.0, SL=2.5` (steady) or test `2.0/2.0` on a few sessions.  
   - ~5 trades/day, risk $400–$600 per trade, daily max loss $1,000.
4. **Tag often** so we can always roll back a good state:
```bash
git tag -a v0.5.6-B-checkpoint -m "B baseline validated over more dates"
git push origin v0.5.6-B-checkpoint
```

---

_You can commit this file under `Docs/` if you want it in-repo._
