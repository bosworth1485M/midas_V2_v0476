# Midas V2 – Automation & Profitability Roadmap (v0.4.7.9.3)
### (Includes Full Feature Module Catalog and Intelligent Backend Plan)

## 1️⃣ Overview
Midas V2 is evolving from a manual, backtested platform into an intelligent, self-optimizing system.
It will ultimately:
- Patch and run configurations safely from a local backend.
- Stream results live to the web UI.
- Record every run and automatically recall the most profitable parameter sets.
- Continuously learn from prior outcomes to guide future tuning.

## 2️⃣ Phase Summary
### Phase 1 – Claude UI Acceptance
- Confirm the Claude-styled web UI builds the same range-runner command as before.
- Run manually in the Midas repo to verify identical outputs.
- Tag → v0.4.7.9.2-ui-accepted.

### Phase 2 – Tiny Backend Helper (v0)
Safe JSON patching for a few standard Cameron parameters.
- Backend in tools/backend/
- Endpoints:
  - GET /current
  - POST /patch?dry_run=1 | apply=1
- Allowlist: price_min, price_max, top
- Atomic writes + timestamped backups
- Dates remain on CLI

After each patch:
```
python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B
```

### Phase 3 – Add More Standard Parameters
Extend backend/UI for gap_min, gap_max, min_rvol_open.
Run the same range after each change and document results.
Tag → v0.4.7.9.3.

### Phase 4 – Feature Modules
Activate and test major trading features sequentially:
1. Green-Streak (minute)
2. Micro-Continuation (1 s)
3. Adaptive Sizing
4. VWAP & S/R context
5. Catalyst Intelligence (re-engineered)

Each follows the Profit-Tuning Loop (≥ +3 pp WR or +0.2 R expectancy).

### Phase 5 – Backend /run + Live Results
- Backend adds /run to execute the range runner.
- Streams logs to a scrolling console on the website.
- After completion, reads summary CSV → returns metrics (WR %, PF, Expectancy R, PnL).
- UI displays a results card and link to CSV.

### Phase 6 – Memory & Intelligence Layer
Backend automatically stores every run (JSONL or SQLite).
- /history/save, /history/top, /history/recall endpoints.
- Website shows Run History and Top Runs tables.
- System identifies and recalls the most profitable configurations based on Expectancy R + stability.
- Intelligence grows with data:
  - Weighted scoring by expectancy, PF, and trade count.
  - Flags stable profitable sets (“recommended defaults”).
  - Suggests parameters that repeatedly underperform (“candidates for review”).

### Phase 7 – Full Automation & Self-Optimization
- Scheduled validation of top parameter sets on new data.
- Backend promotes stable winners and downgrades regressions.
- UI presents AI Insights such as:
  - “This parameter set produced the highest expectancy over 3 months.”
  - “Adaptive Sizing + VWAP confirm + Catalyst ≥ 2 gave consistent profitability.”

## 3️⃣ Comprehensive Feature Module Catalog
(See prior detailed tables covering: Core Filters, Momentum, Microstructure, Risk, VWAP/S-R, Catalyst Intelligence with added sources, Router, Band-Context, Backend/Automation, Elite Refinements.)

## 6️⃣ Guiding Principles
- JSON = single source of truth for strategy params.
- CLI = runtime only (dates and scenario).
- Incremental change → manual test → measure → tag.
- Always backup configs and store run history.
- Profitability measured scientifically (A/B tests).
- Website intelligence: recalls and recommends the most profitable runs automatically.
- Documentation and transparency at every stage.
- Automation follows stability and profit validation.
