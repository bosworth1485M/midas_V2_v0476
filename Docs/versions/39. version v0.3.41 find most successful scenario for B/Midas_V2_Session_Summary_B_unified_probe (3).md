# Midas_V2 — Session Summary (B_unified probe)

**Timestamp:** 2025-09-29 13:49

## What we did
- Restored **schema-driven params** for Scenario B in `config/scenarios.json` under `B.params`: `green_streak` and `macd_rise_bars` (validated by logs).
- Confirmed catalyst flow at **v0.3.40** (run branch at the tag’s code).
- Probed **Aug‑05/06/07** to find a single robust B profile; compared **gate 15** vs **gate 20**.
- Kept: **news-only score≥2**, **Top‑N**, **RVOL≥2.0**, **green=3**, **MACD rising bars=2**; TP/SL=2.0/2.5.

## Key findings
- **Gate 20** fixed the July‑like day (**Aug‑06**) while preserving Aug‑05; it **hurt Aug‑07** vs gate 15.
- **Score≥3** over‑filters on Aug‑06 (all kept were score=2 → 0 trades).
- Across the 3‑day probe, **gate 20** produced the better net result.

### Results snapshot
| Date | Profile | Used | WR% | TP/SL | PnL | Notes |
|---|---|:--:|:--:|:--:|---:|---|
| 2025-08-05 | Top-3 | RVOL 2.0 | gate 15 | green=3 | MACD=2 | 3 | 100.00% | 3/0 | +28.51 | Earlier baseline check |
| 2025-08-05 | Top-3 | RVOL 2.0 | gate 20 | green=3 | MACD=2 | 3 | 100.00% | 3/0 | +28.73 | Gate 20 holds |
| 2025-08-06 | Top-3 | RVOL 2.0 | gate 15 | green=3 | MACD=2 | 3 | 0.00% | 0/3 | -81.37 | Too early |
| 2025-08-06 | Top-2 | RVOL 2.0 | gate 15 | green=3 | MACD=2 | 2 | 0.00% | 0/2 | -65.84 | Still fails |
| 2025-08-06 | Top-2 | RVOL 2.0 | gate 20 | green=3 | MACD=2 | 2 | 50.00% | 1/1 | +11.16 | Gate 20 fixes day |
| 2025-08-06 | Top-3 | RVOL 2.0 | gate 20 | green=3 | MACD=2 | 3 | 66.67% | 2/1 | +17.96 | Best on 08‑06 |
| 2025-08-06 | Top-2 | RVOL 2.0 | gate 20 | score≥3 | 0 | 0.00% | 0/0 | +0.00 | Too strict (all score=2) |
| 2025-08-07 | Top-3 | RVOL 2.0 | gate 15 | green=3 | MACD=2 | 3 | 100.00% | 3/0 | +32.41 | Best on 08‑07 at 15m |
| 2025-08-07 | Top-3 | RVOL 2.0 | gate 20 | green=3 | MACD=2 | 3 | 66.67% | 2/1 | -15.83 | 20m misses early winner |
| 2025-08-07 | Top-2 | RVOL 2.0 | gate 20 | green=3 | MACD=2 | 2 | 50.00% | 1/1 | -23.79 | Worse than Top‑3 |

## Recommended unified B (for month validation)
- **newsOnly**, **score ≥ 2**
- **Top‑3**
- **Gap 10–40%**, price **$1–$20**
- **Opening RVOL ≥ 2.0**
- **Gate = 20 minutes**
- **Momentum:** `green_streak = 3`, `macd_rise_bars = 2`
- **Targets:** `TP 2.0%`, `SL 2.5%`

**Why:** Gate 20 fixed Aug‑06 (+17.96 with Top‑3) while keeping Aug‑05 strong. We’ll validate July & August day‑by‑day before freezing.

## Plan (next)
1. **Do not range‑run yet.** Use the **previous‑trading‑day** helper to drive `run_catalyst_flow.py` day‑by‑day across **August**, then **July**.  
2. Aggregate `_comparisons` to confirm **WR ≥ ~60%** and **positive PnL** per month.  
3. If both months are solid, **lock B_unified** into `scenarios.json`, update docs, and tag (e.g., `v0.3.41‑B_unified`).  
4. If July lags, keep B_unified as baseline; add a manual **B_slow** (Top‑2 and/or RVOL≥2.2) for choppy mornings.

## Notes
- Aug‑06 news kept were score=2; requiring score≥3 produced 0 trades.  
- Keep deny‑negative & exclude‑China filters for choppier months.  
- Later hygiene: ignore `data/samples/*.csv` and `out/` and untrack the already‑added cache files.

# Exact run commands (copy/paste)

**Aug-07 — Top-3, RVOL 2.0, gate 15, green=3, MACD=2**
```
python scripts\run_catalyst_flow.py --date 2025-08-07 --scenario B --news-first --require-news --news-min-score 2 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --compare --compare-label B_top3_rvol20_g15_green3_macd2
```

**(Check metrics)**
```
python scripts\check_comparison_metrics.py
```

**Aug-06 — Top-2, RVOL 2.0, gate 15, green=3, MACD=2**
```
python scripts\run_catalyst_flow.py --date 2025-08-06 --scenario B --news-first --require-news --news-min-score 2 --top 2 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --compare --compare-label B_top2_rvol20_g15_green3_macd2
```

**Aug-06 — Top-2, RVOL 2.0, gate 20, green=3, MACD=2**
```
python scripts\run_catalyst_flow.py --date 2025-08-06 --scenario B --news-first --require-news --news-min-score 2 --top 2 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 20 --compare --compare-label B_top2_rvol20_g20_green3_macd2
```

**Aug-06 — Top-2, RVOL 2.0, gate 20, **score≥3** (smoke strict)**
```
python scripts\run_catalyst_flow.py --date 2025-08-06 --scenario B --news-first --require-news --news-min-score 3 --top 2 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 20 --compare --compare-label B_top2_rvol20_g20_score3_green3_macd2
```

**Aug-06 — Top-3, RVOL 2.0, gate 20, green=3, MACD=2**
```
python scripts\run_catalyst_flow.py --date 2025-08-06 --scenario B --news-first --require-news --news-min-score 2 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 20 --compare --compare-label B_top3_rvol20_g20_green3_macd2
```

**Aug-05 — Top-3, RVOL 2.0, gate 20, green=3, MACD=2**
```
python scripts\run_catalyst_flow.py --date 2025-08-05 --scenario B --news-first --require-news --news-min-score 2 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 20 --compare --compare-label B_top3_rvol20_g20_green3_macd2
```

**Aug-07 — Top-3, RVOL 2.0, gate 20, green=3, MACD=2**
```
python scripts\run_catalyst_flow.py --date 2025-08-07 --scenario B --news-first --require-news --news-min-score 2 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 20 --compare --compare-label B_top3_rvol20_g20_green3_macd2
```

**Aug-07 — Top-2, RVOL 2.0, gate 20, green=3, MACD=2**
```
python scripts\run_catalyst_flow.py --date 2025-08-07 --scenario B --news-first --require-news --news-min-score 2 --top 2 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 20 --compare --compare-label B_top2_rvol20_g20_green3_macd2
```

**(Check metrics)**
```
python scripts\check_comparison_metrics.py
```

