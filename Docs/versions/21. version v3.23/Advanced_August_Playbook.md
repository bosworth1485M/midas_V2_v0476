# Advanced August Playbook (Midas_V2 v0.3.21)

**Last updated:** 2025-09-20 15:28 (America/Chicago)

This playbook adds the missing pieces you asked for: **Top‑N testing**, plus the **exact one‑liners** we’ve been using so you can run August ranges without workflow changes.

---

## A. Run August (Baseline, then D, then E)
From `C:\Users\boydp\Desktop\midas_V2`:

**Scenario B (baseline):**
```powershell
python scripts/run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario B
```

**Scenario D (strict):**
```powershell
python scripts/run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario D
```

**Scenario E (dip reclaim):**
```powershell
python scripts/run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario E
```

Outputs appear per day under `out\YYYYMMDD\<Scenario>\` and a range summary under `out\range_summaries\`.

---

## B. Top‑N by Gap — How to Test (without changing scripts)

**Goal:** Try a small Top‑N (e.g., 8–12) *after* you finish the vanilla August runs so you can isolate the effect.

**Step 1 — Build the day’s universe (normal):**
```powershell
python scripts/topgappers.py --date 2025-08-06
```
This writes the canonical daily universe (e.g., `data\universe_topgappers_2025-08-06.txt` and updates your active universe file per your current wiring).

**Step 2 — Trim the universe file to Top‑N (Python-only one-liner):**
> Replace `data\universe_active.txt` with your actual active-universe path if different.

```powershell
python -c "import io,sys; p=r'data\universe_active.txt'; s=io.open(p,'r',encoding='utf-8').read().splitlines(); io.open(p,'w',encoding='utf-8').write('\n'.join(s[:10])+'\n')"
```
- Change `[:10]` to your desired N (e.g., `[:8]`, `[:12]`).
- This simply keeps the first N symbols already sorted by your existing gap logic.

**Step 3 — Run the normal day or range using the trimmed universe:**
```powershell
python scripts/run_day_simple.py --date 2025-08-06 --scenario B
```
(or use the range runner for Aug once you’ve applied trimming for each day during preprocessing).

**Reverting:** Re-run `scripts/topgappers.py` for that date to regenerate a full universe, or restore from Git if the universe is tracked.

---

## C. Opening RVOL Gate (plan it after August replication)
Keep this off until the August baseline is complete. When ready, introduce a single knob:
- Concept: compare first 10–15 min volume vs prior-day same window; require ≥ **1.5x**.
- Add as an optional flag in your runner; start at 1.5 and only then re-run Aug for A/B.

---

## D. Catalyst Universe Quick Pass (optional after Top‑N)
- Use `scripts/enrich_universe_catalyst.py` to score news.
- Prefer **A-grade** symbols; allow **B-grade** only to fill Top‑N on quiet days.
- Keep the rest of the guards the same (EMA/VWAP/MACD, rise_bars=3).

---

## E. Hygiene & Guardrails Recap
- Price band: **$1–$20**; Gap: **10–40%**; Min PM vol: **≥30k**.
- Denylist known trouble tickers if needed.
- TP/SL ~ **2.0 / 2.5**; daily stop ~ **-$1,000**.

---

## F. What “Good” Looks Like for August
- Consistent **WR ≥ 60%** on B or D across Aug (2025-08-05 → 2025-08-31).
- Stable PnL with a reasonable trade count (avoid over-fitting via too-small N).
- If it holds, validate on **July** with the same knobs before adding new ones.

