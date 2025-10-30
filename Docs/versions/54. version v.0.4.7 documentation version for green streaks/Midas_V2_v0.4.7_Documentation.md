# Midas_V2 v0.4.7 — 1-Second Candle & Green-Streak Smoke Test Documentation
*Documentation-only release — 2025-10-20*

## Purpose (Refined)
The purpose of this phase is **not only** to validate the handling of **1-second candles**, but also to confirm that the **three prior candles in the 1-minute timeframe have strong green bodies** and that this **green momentum continues into the 1-second timeframe**. We are aligning **macro (1-minute)** structure with **micro (1-second)** continuation to improve confidence before entries.

**Goals**
- Enforce a **green-streak=3** rule on the 1-minute series (strong-body greens).
- Verify that this streak **continues on 1-second bars** just after the 1-minute close (micro continuation).
- Preserve gate logic (e.g., **gate=10–15 min**, EMA/VWAP confirms) while we validate microstructure.
- Produce a documentation-only tag **v0.4.7** with exact commands and smoke-test evidence.

---

## Architecture at a Glance (ASCII Diagram)
```
+----------------------+       +-------------------------------------+
| 1-minute Series      |       | 1-second Series (micro continuation)|
| (macro confirmation) |       |                                     |
+----------------------+       +-------------------------------------+
| t-3  | t-2 | t-1     |       | 60s window right after minute close |
|  G   |  G  |  G      |       |  (e.g., [t, t+60s))                 |
|strong|strong|strong  |       |  - Rising sequence (G,G,...)        |
+----------------------+       |  - EMA reclaim holds                |
            |                  |  - VWAP (if enabled) slopes/holds   |
            +------------------>  -> one_sec_continuation_ok == True |
                               +-------------------------------------+
                        (Enter only if BOTH blocks pass)
```

**Legend**
- **G** = green (close > open) with *strong body* threshold (configurable).
- **one_sec_continuation_ok** = function validating micro continuation from `micro_confirm.py`.

---

## Scripts Involved
1. **`src/midas_v2/micro/micro_confirm.py`**
   - Provides micro-level confirmation helpers, notably:
     - `one_sec_continuation_ok(...)`: checks that the immediate 1-second window after a 1-minute green streak continues to print green/up seconds (optionally with EMA/VWAP adherence).
   - Intended to be imported by strategy logic or smoke tests.

2. **`src/midas_v2/micro/micro_smoke_test.py`**
   - A deterministic harness that validates the green-streak + micro continuation rules on synthetic or fixture data.
   - Emits `[PASS]/[FAIL]` lines for each guard (time gate, EMA reclaim, etc.).

3. **`src/midas_v2/micro/check_polygon_1s.py`**
   - A utility to verify that **Polygon** 1-second data are fetched, normalized, and time-aligned correctly for a symbol/date window.
   - Helps confirm that the 1-second source is healthy before wiring to live strategy.
   
> Note: Filenames reflect your current layout under `src\midas_v2\micro\`.

---

## Exact Commands Used in Recent Smoke Tests

### 1) Run the micro smoke test (1-second continuation + gates)
```powershell
$env:PYTHONPATH='src'; python src\midas_v2\micro\micro_smoke_test.py
```
**Observed output (sample):**
```
[PASS] Time gate 15s allows entries (clean uptrend, EMA reclaim)    -> idx=34
[PASS]
```

### 2) Verify import & core function availability
```powershell
python -c "import sys; sys.path.insert(0,'src'); from midas_v2.micro.micro_confirm import one_sec_continuation_ok; print('OK')"
```
**Expected output:**
```
OK
```

### 3) Check Polygon 1-second data for a concrete window
*(Use any symbol/date you tested; STTK and 2025-08-05 are good examples.)*
```powershell
$env:PYTHONPATH='src'; python src\midas_v2\micro\check_polygon_1s.py --symbol STTK --date 2025-08-05 --start 09:30 --end 09:45
```
**What to look for:**
- A printed row count of 1s bars in the window, min/max timestamps, and any gaps.
- Optional sanity prints (first 5 rows, last 5 rows).
- Confirm exchange trading seconds (no pre/post in the target window unless intentional).

> If your script exposes different flags (e.g., `--from`/`--to`, `--window`), run `-h` to see help and adjust accordingly.

---

## How to Interpret the Smoke Test
- If **(1m) green-streak=3 with strong bodies** is found but **(1s) continuation** fails, the entry should be **blocked**. This avoid false momentum that fades immediately after a 1-minute close.
- If both pass (plus your time gate and EMA/VWAP rules), the setup is **eligible** for entry in scenario routing (B/D/E as configured).

---

## Wiring Plan — Step-by-Step Integration into Main Logic

**Goal:** Integrate the 1-minute green-streak and 1-second continuation checks into `strategy.py` (and/or your scenario evaluators) with minimal disruption and full guardrails.

1. **Config flags (JSON)**
   - Add under each scenario (e.g., `B.params`):
     ```json
     {
       "rise_bars": 3,
       "strong_body_min": 0.22,
       "require_micro_continuation": true,
       "micro_window_secs": 60,
       "micro_require_ema_reclaim": true,
       "micro_require_vwap_hold": false
     }
     ```
   - Keep defaults conservative; allow per-scenario overrides.

2. **Strategy entry pipeline**
   - **Order of checks**:
     1. Price/gap bands, min premarket volume, opening **gate-minutes**.
     2. EMA slope + VWAP slope/confirm (if enabled).
     3. **Minute-level green-streak=3** with **strong-body** threshold.
     4. **Call** `one_sec_continuation_ok(...)` for the first `micro_window_secs` just after the last 1-minute close.
     5. If all true → **entry eligible**; otherwise **skip**.

3. **Function hook**
   - Import once at top of strategy:
     ```python
     from midas_v2.micro.micro_confirm import one_sec_continuation_ok
     ```
   - Call with explicit parameters pulled from scenario JSON.

4. **Data access**
   - Ensure the 1-second loader is available in your data layer (reuse what `check_polygon_1s.py` uses).
   - Cache the 1-second slice for the minute under test to avoid repeated IO.

5. **Risk manager compatibility**
   - Do **not** change sizing here; keep adaptive sizing off for this tag.
   - Log a clear reason when a trade is **blocked** by micro continuation.

6. **Logging & WHY lines**
   - Add `WHY:` lines when:
     - minute streak fails,
     - micro continuation fails,
     - EMA/VWAP fails,
     - or trade becomes eligible.

7. **Unit & smoke tests**
   - Keep `micro_smoke_test.py` green.
   - Add a small unit test (fixture with a failing continuation) to prevent regressions.

8. **Backtest toggle**
   - Add a scenario toggle `use_micro_confirmation` (alias of `require_micro_continuation`) so you can A/B test impact on WR/PnL.

9. **Telemetry (optional)**
   - Count how many candidates passed minute-streak but failed micro continuation; this helps tune thresholds later.

10. **Docs & Tag**
   - Update `Docs/DEV_GUIDE.md` after wiring.
   - Tag next code version (e.g., v0.4.8) only **after** integration and a short range test pass.

---

## Next Steps Checklist
- [ ] Wire JSON flags and the `one_sec_continuation_ok` hook into `strategy.py`.
- [ ] Run **day-level** backtests on 2–3 known symbols/dates to confirm no breakage.
- [ ] Run a **short August range** (e.g., 2025‑08‑05 → 2025‑08‑07) with `use_micro_confirmation=true`.
- [ ] Capture analyzer metrics (WR, PnL) vs the baseline.
- [ ] If stable/positive, plan v0.4.8 (code tag) and proceed to broader ranges.

---

## GitHub Versioning (Documentation-only v0.4.7)
Use your canonical one‑liners:

```bash
git add -A
git commit -m "v0.4.7: Documentation-only — 1s continuation + 1m green-streak plan and smoke-test commands"
git tag -a v0.4.7 -m "Documentation-only: 1s continuation + 1m green-streak"
git push
git push --tags
```

---

## Session Footer
This document is intended for `Docs/versions/` and should be referenced at the start of the next session.

**Title:** Midas_V2 v0.4.7 — 1-Second Candle & Green-Streak Smoke Test Documentation  
**Tag:** v0.4.7 (documentation-only)  
**Date:** 2025-10-20
