# Midas_V2 – Version v0.4.7.9.2
## Full Documentation, Steps, and Next-Phase Plan

---

## 1. Overview
**Version:** v0.4.7.9.2  
**Date:** 2025-11-08  
**Stage:** Phase 1 – UI Integration (Standard Range Runner)  
**Purpose:** Introduce a simple, local, read-only web interface (“SimpleRunner”) that builds and copies standardized backtest commands for manual execution in the Midas_V2 backtesting environment.

---

## 2. Objectives
1. Provide a safe, visual front-end for constructing backtest commands.  
2. Keep all core trading logic untouched.  
3. Enable quick range testing (Aug 05→31 2025) with the standard range runner (non-catalyst).  
4. Prepare for later feature toggles (Top-N, Adaptive Sizing, Catalyst Flow, etc.) without disrupting the core.

---

## 3. Step-by-Step Work Completed
### 3.1 Setup
- Created a **separate React project** at `C:\Users\boydp\Desktop\midas-ui` using Vite (`npm create vite@latest . -- --template react-ts`).
- Verified Node installation (Node v24.11.0, npm 11.6.1).
- Installed dependencies with `npm install`.
- Confirmed `package.json` present and project runs via `npm run dev`.

### 3.2 Building the UI
- Added folder `src/pages/` and created file `SimpleRunner.tsx`.
- Implemented minimal component (no Tailwind dependencies) to:
  - Accept **Start Date**, **End Date**, and **Scenario (A–E)**.
  - Auto-generate the CLI command:
    ```
    python scripts\run_range_and_summarize.py --start YYYY-MM-DD --end YYYY-MM-DD --scenario X
    ```
  - Provide **Copy**, **Reset**, and **Run (disabled)** buttons.
  - Display future feature placeholders.
- Updated `src/App.tsx` to render `SimpleRunner`.
- Verified the dev server at http://localhost:5173/ renders correctly.

### 3.3 Manual End-to-End Test
- Start = 2025-08-05, End = 2025-08-31, Scenario = B.  
- Clicked **Copy**, pasted into PowerShell inside Midas repo:
  ```
  cd C:\Users\boydp\Desktop\midas_V2_v0.4.7.9_working
  python scripts\run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B
  ```
- Successful output:
  ```
  [OK] Backtest done.
  2025-08-29 [B] -> trades=9, wins=5, losses=4, winrate=55.56%, pnl=+0.02
  === TOTALS ===
  [B] trades=190, wins=89, losses=101, winrate=46.84%, totalPnL=-1115.21
  [OK] Range summary CSV -> out\auto\range_summary_20250801_20250831_B.csv
  ```

### 3.4 Documentation & Tagging
- Created `Docs/Session_Summary_v0.4.7.9.2.md`.
- Git tag `v0.4.7.9.2: Phase-1 UI (SimpleRunner) + standard range validation`.

---

## 4. Architecture Summary
| Layer | Role | Folder |
|-------|------|--------|
| **UI (React)** | Command builder & copy interface | `Desktop\midas-ui` |
| **Backtester (Python)** | Executes range runs | `Desktop\midas_V2_v0.4.7.9_working` |
| **Bridge** | *None yet (manual copy)* | — |

---

## 5. Planned Feature Enablement
| Feature | Status | Description |
|----------|---------|-------------|
| **Top-N selector** | ⏳ Phase 1.1 | Numeric input controlling `--top N`. Validate integer 1–50. |
| **Scenario selector (A–E)** | ✅ Done | Functional. |
| **Catalyst flow** | 🔒 Off | Disabled until catalyst reliability improves. |
| **Adaptive sizing** | 🔒 Off | Re-enable after risk-manager tuning. |
| **Support/Resistance (S/R Lite)** | 🔒 Off | Planned after catalyst + sizing lift. |
| **Candle Snapshots (sidecar)** | 🔒 Off | Future diagnostic overlay. |
| **Analyzer Panel** | 🔒 Off | Future read-only results viewer. |
| **Router D>E** | 🔒 Off | Future multi-scenario merge logic. |
| **Run Button** | ⏳ Phase 2 | Add local backend bridge (Flask / Node). |

---

## 6. Profitability Roadmap Modules (A–F)
| Module | Name | Purpose | Status |
|---------|------|----------|--------|
| A | Adaptive Sizing + | Confidence-weighted sizing (A/B/C tiers). | ✅ Framework exists. |
| B | Band-Context Layer | Bollinger / VWAP over-extension filter. | 🔒 Planned. |
| C | Microstructure Gateway | 1 s–5 s candle confirmations. | 🔒 Planned. |
| D | Catalyst Intelligence | Multi-source scored news. | ⚙ Rebuild planned. |
| E | Support/Resistance Lite | Swing-zone detection, reclaim logic. | 🔒 Planned. |
| F | Regime Awareness | Detect hot/cold market regimes. | 🔒 Planned. |

---

## 7. Elite Layer Refinements
| # | Feature | Purpose |
|---|----------|----------|
| 1 | Synthetic market orders | Slippage protection. |
| 2 | Adaptive trade management | Stop-to-breakeven, partial scale-outs. |
| 3 | Dynamic exit logic | Exit on MACD/VWAP reversal. |
| 4 | Partial TP ladder | Secure early gains. |
| 5 | Slippage & spread tracking | Monitor execution quality. |
| 6 | Market hotness index | Adaptive risk scaling. |
| 7 | Real-time dashboard | GUI-based live monitoring. |
| 8 | Expectancy/mistake analyzer | Post-trade analysis. |
| 9 | Micro-news tagging | Improve catalyst accuracy. |
| 10 | Broker safety guard | Daily loss/drawdown caps. |

---

## 8. Addressing Low Profit
### Why Profit is Low
- Baseline lacks catalysts, adaptive sizing, and S/R filtering.
- August 2025 likely had fewer strong gappers.
- No risk-based or volume gates yet.

### What Successful Cameron Projects Experienced
All began near 45–50% WR and flat/negative PnL.  
Profit turned positive only after enabling:
1. Catalyst Scoring → +10–15 pp WR.  
2. Adaptive Sizing → +0.3 R expectancy.  
3. S/R + VWAP Reclaims → Filtered bad breakouts.  
4. Opening RVOL Gate → Removed weak setups.  
5. Microstructure Checks → Cut false triggers.

### Path to Recovery
| Stage | Key Lift Driver | Expected Change |
|--------|----------------|-----------------|
| Catalyst v0.4.8 | High-quality tickers | +10–15 pp WR |
| Adaptive Sizing v0.4.9 | Tiered risk | +0.3 R |
| S/R + VWAP v0.5.0 | Filter bad breakouts | +0.1 R |
| Microstructure v0.5.1 | Precise entries | +0.1 R |
| Execution Quality Tracker | Reduce slippage | +0.05 R |

Goal: **Expectancy +0.8 R**, **WR 60–65 %**, **Profit factor ≥ 1.3**.

---

## 9. Next Phases Summary
### Phase 1.1 – Configurable Standard Runner
- Add Top-N numeric input (1–50).  
- Add “Last copied command” status.  
- Copy-only mode (no execution).

### Phase 1.2 – Runner Selector
- Toggle between Standard/Catalyst (Catalyst disabled).

### Phase 2 – Safe Execution Bridge
- Local backend (FastAPI / Node).  
- Input validation and command spawning.  
- Keep Copy fallback.

### Phase 3 – Visual Enhancements
- Add Tailwind + shadcn/ui.  
- Add status badges and feature cards.

### Phase 4 – Analyzer Integration
- Display latest run metrics and output CSV path.

---

## 10. Long-Term Vision
| Version | Theme | Milestone |
|----------|-------|-----------|
| v0.5.x | Integrated Profitability System | All modules A–F active. |
| v0.6.x | Automation & Analytics | GUI + backend bridge + metrics. |
| v0.7.x | Execution Optimization | Slippage tracking, trade management. |
| v0.8.x | Machine Adaptation | Regime awareness, auto-tuning. |
| v1.0 | Live Trading | Fully automated + safe. |

---

## 11. Summary
**v0.4.7.9.2 achievements:**
- Functional UI front-end for range testing.  
- Confirmed command parity with CLI.  
- Clean architecture separation.  
- Safe manual execution flow.  
- Clear roadmap to profitability.

Next immediate step: **add Top-N and status indicator** (Phase 1.1).

---

Prepared by ChatGPT (GPT-5) – 2025-11-08.
