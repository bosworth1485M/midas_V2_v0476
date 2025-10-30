## v0.3.45-step4 — 2025-10-06
**Experiment:** Stricter catalysts (`news_min_score ≥ 3`) with baseline guards (newsOnly + Top-3, band 10–40, RVOL ≥2.0, gate=15).

**Finding:** Too strict under current scoring → **0 symbols picked** on 2025-08-05/06/07 (all days produced 0 trades).  
This matches prior observations: our raw “score 3” set is narrow.

**Why it matters:** Raising the threshold reduces noise but currently **over-filters**; we lose otherwise good A-grade setups.

**Recommendation (next):**
- Expand what contributes to a “3” via **boosts** (+1) for FDA decisions, raised guidance, major contracts/partnerships, strong analyst upgrades, M&A.  
- Slightly **widen the news lookback window** (e.g., 24–36h with decay) so late-evening/early-AM PRs are included.  
- If still sparse, use **Top-2** with score≥3 days.

**Commands used:**
- Range run (score 3):  
  `python scripts\run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B --news-first --require-news --news-min-score 3 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --deny-negative --exclude-china --compare --compare-label B_top3_score3_g15_rvol2`
- Quick view (prefers latest with trades; use label filter to see earlier score 2 runs):  
  `python scripts\scan_runs_simple.py --start 2025-08-05 --end 2025-08-07 --scenarios B`  
  `python scripts\scan_runs_simple.py --start 2025-08-05 --end 2025-08-07 --scenarios B --label-substr rvol2_g15`

**Outcome snapshot:**  
- Score ≥3: 0/0/0 (no trades) on 08-05, 08-06, 08-07  
- Score ≥2 (earlier baseline): WR 77.78%, TP/SL 7/2, PnL +1.63 over 3 days