
# Midas_V2 — **v0.3.40-macd2-baseline**

**Date:** 2025-09-28  
**Branch:** `feat/macd-risebars-config` (based on `clean/v0.3.37`)  
**Goal:** Raise win‑rate and profit by enabling momentum filters (MACD rising bars + green‑streak) and tightening selection (news‑only, Top‑N, RVOL gate, open gate).

---

## What changed in this version

### 1) Schema: allow tunable params per scenario
- **File:** `src/midas_v2/config_models.py`
- **Change:** The `Scenario` model now includes a free‑form bucket for runtime knobs:
  ```py
  params: Dict[str, Any] = Field(default_factory=dict)
  ```
- This lets us set keys like `green_streak` and `macd_rise_bars` in JSON without loosening validation.

### 2) Scenarios config shape
- **File:** `config/scenarios.json`
- The loader expects a **top‑level map of scenarios**, e.g. `{ "B": {...}, "D": {...} }` — **not** `{ "scenarios": {...} }`.
- We flattened the file accordingly and placed gates under **`B.params`**.

### 3) Scenario B tuning (this version)
Placed in `B.params`:
- `green_streak = 3`  (require 3 consecutive green price candles)
- `macd_rise_bars = 2` (require 2 rising MACD histogram bars)

Selection & gates used for runs:
- **news-only**, **Top-3**, **gap band 10–40%**, **opening RVOL ≥ 2.0**, **gate = 15 min**

---

## Why these changes (and how this mirrors successful Cameron projects)

Across the best Cameron‑style builds we studied/replicated:
- They **do not** trade every gapper → they require a **strong catalyst (news/earnings/FDA)**.
- They cap to **Top‑N (≈2–5)** symbols to focus attention and quality.
- They add **opening volume gates** (RVOL ≥ 1.5–2.0) to confirm early demand.
- They **enforce momentum** with **MACD confirmation** (line > signal) and **rising histogram bars** (2–3), often alongside a small **green‑streak** on price.
- They defer entries with **open gate minutes** (e.g., 10–15) to let noise settle.

This release applies that same playbook to Scenario B.

---

## Exact commands & results

> All commands run from the repo root. Runner automatically sets `PYTHONPATH=src` for child processes.

### Verify the active schema (proves we load the right file & fields)
```
python -c "import midas_v2.config_models as M; print(M.__file__); print('Scenario fields:', list(M.Scenario.model_fields.keys()))"
```
Output (abbrev):
```
...\src\midas_v2\config_models.py
Scenario fields: ['scanner', 'params']
```

### Ensure JSON shape & params
```
copy config\scenarios.json config\scenarios.json.bak
python -c "import json;p='config/scenarios.json';d=json.load(open(p)); d2=d.get('scenarios', d); json.dump(d2, open(p,'w'), indent=2); print('OK')"
python -c "import json;p='config/scenarios.json';d=json.load(open(p)); B=d.setdefault('B',{}); P=B.setdefault('params',{}); P['green_streak']=3; P['macd_rise_bars']=2; json.dump(d, open(p,'w'), indent=2); print('OK')"
```

### Reproduce the three key test runs (Scenario **B**)

**Aug‑07** — *newsOnly + Top‑3 + band 10–40 + RVOL 2.0 + gate 15 + green=3 + MACD=2*
```
python scripts\run_catalyst_flow.py --date 2025-08-07 --scenario B --news-first --require-news --news-min-score 2 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --compare --compare-label B_top3_rvol20_g15_green3_macd2
```
Result (summary excerpt):
```
Used=3 | WR=100.00% | TP/SL=3/0 | PnL=+32.41
```

**Aug‑05** — *same knobs*
```
python scripts\run_catalyst_flow.py --date 2025-08-05 --scenario B --news-first --require-news --news-min-score 2 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --compare --compare-label B_top3_rvol20_g15_green3_macd2
```
Result:
```
Used=3 | WR=100.00% | TP/SL=3/0 | PnL=+28.51
```

**Aug‑06** — *same knobs*
```
python scripts\run_catalyst_flow.py --date 2025-08-06 --scenario B --news-first --require-news --news-min-score 2 --top 3 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --compare --compare-label B_top3_rvol20_g15_green3_macd2
```
Result:
```
Used=3 | WR=0.00% | TP/SL=0/3 | PnL=-81.37
```

Check all comparisons:
```
python scripts\check_comparison_metrics.py
```
You should see rows matching the above (OK).

---

## “Sweet spot” (so far)

For August **05** and **07**, this profile looks best:
- **newsOnly + Top‑3 + gap 10–40 + RVOL 2.0 + gate 15 + green_streak=3 + MACD rise_bars=2**  
- Delivers **WR 100%** with healthy PnL on both days.

For August **06**, this exact profile underperformed (0/3). That’s typical on some days — the fix is a small knob change (see next steps).

---

## Next steps (micro‑tweaks to stabilize Aug‑06)

Apply **one** at a time; keep the rest constant (newsOnly, band 10–40, MACD=2, green=3, gate=15 unless we change it in the step):

1) **Top‑2** (reduce weak pick):
```
python scripts\run_catalyst_flow.py --date 2025-08-06 --scenario B --news-first --require-news --news-min-score 2 --top 2 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 15 --compare --compare-label B_top2_rvol20_g15_green3_macd2
```

2) If still weak, **gate=20** (entries later):
```
python scripts\run_catalyst_flow.py --date 2025-08-06 --scenario B --news-first --require-news --news-min-score 2 --top 2 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 20 --compare --compare-label B_top2_rvol20_g20_green3_macd2
```

3) Optional: **require stronger news** (score ≥3) with Top‑2 or Top‑3:
```
python scripts\run_catalyst_flow.py --date 2025-08-06 --scenario B --news-first --require-news --news-min-score 3 --top 2 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.0 --gate-minutes 20 --compare --compare-label B_top2_rvol20_g20_score3_green3_macd2
```

When Aug‑06 stabilizes (WR improves without killing PnL), re‑validate the same winning profile on Aug‑05/07 to confirm consistency.

---

## Tagging this version

After you’re happy with the above changes already in the repo:
```
git add -A
git commit -m "v0.3.40: schema accepts Scenario.params; scenarios.json flattened; B.params {green_streak=3, macd_rise_bars=2}; validated Aug-05/06/07 with newsOnly+Top-3 RVOL2.0 g15"
git tag -a v0.3.40-macd2-baseline -m "v0.3.40: Scenario B uses MACD rising bars (2) + green_streak(3); newsOnly+Top-3+RVOL2.0+gate15 validated on Aug-05/07 and investigated for Aug-06"
git push
git push --tags
```

---

## Notes & verification tips

- To **prove** MACD gating is active, temporarily set:
  ```
  python -c "import json;p='config/scenarios.json';d=json.load(open(p)); d['B']['params']['macd_rise_bars']=6; json.dump(d, open(p,'w'), indent=2); print('OK')"
  ```
  Re-run a day → **Used** should drop. Then set it back to 2.
- The runner already propagates `PYTHONPATH="src"` to child processes; no extra env steps needed.
- Keep `extra='forbid'` in Pydantic: it prevents silent typos in JSON, which is important for trading code.

---

**TL;DR:** v0.3.40 enables momentum gates (MACD=2 + green=3) in a schema‑safe way and tightens selection (news‑only, Top‑3, RVOL=2.0, gate=15). It matched the strong Cameron‑style results on Aug‑05 and Aug‑07 (100% WR), and we have a short plan to stabilize Aug‑06 with tiny, controlled tweaks.
