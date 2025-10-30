# Strategy Patch Notes — v0.4.7 (Documentation-Only)
*Date:* 2025-10-20

> This document describes, in detail, the **planned** code changes for v0.4.8 to wire the 1‑minute green‑streak + 1‑second continuation confirmations into the main strategy. It is **not** a code change — just a specification you can follow verbatim when we implement.

---

## 0) Scope
- **No sizing changes** in this patch (adaptive sizing remains as-is).
- Only adds **filters/guards**: 1m green-streak with strong bodies, and 1s continuation window.
- Minimal disruption: new code is behind toggles and respects existing pipeline order.

---

## 1) Configuration — scenarios.json (per-scenario under `params`)
Add/confirm these keys for B/D/E (others optional):

```json
{
  "rise_bars": 3,
  "strong_body_min": 0.22,
  "use_micro_confirmation": true,
  "require_micro_continuation": true,
  "micro_window_secs": 60,
  "micro_require_ema_reclaim": true,
  "micro_require_vwap_hold": false,
  "micro_min_green_ratio": 0.60,
  "micro_allow_first_pullback": true
}
```

**Notes**
- Keep `use_micro_confirmation` and `require_micro_continuation` as synonyms (either enables the micro step).
- `strong_body_min = 0.22` means body >= 22% of candle range to qualify as “strong”.
- Start with `micro_min_green_ratio = 0.60` and tune after A/B tests.

---

## 2) Imports (strategy.py or the scenario evaluator where entries are decided)

Add near the top with other imports:

```python
# micro confirmation helper
from midas_v2.micro.micro_confirm import one_sec_continuation_ok
```

If you don’t have a central loader for 1s bars yet, add

```python
# 1-second data access (planned abstraction)
from midas_v2.data.one_sec_loader import load_1s_slice
```

(See §5 to create this file if it doesn’t exist.)

---

## 3) Candidate evaluation — pipeline order
**Where:** in the function that determines whether a candidate can enter (e.g., `eligible_for_entry` or equivalent).

**Add or adjust to enforce this order:**

```python
def eligible_for_entry(ctx, params, minute_bar, minute_series, state):
    # 1) Hard guards
    if not in_price_and_gap_band(ctx, params): return why("BAND_FAIL")
    if not premarket_volume_ok(ctx, params):   return why("PMVOL_FAIL")
    if not gate_minutes_ok(ctx, params):       return why("GATE_FAIL")

    # 2) Trend/structure confirms
    if not ema_slope_ok(ctx, params):          return why("EMA_SLOPE_FAIL")
    if vwap_required(params) and not vwap_ok(ctx, params):
                                                return why("VWAP_FAIL")

    # 3) Minute-level green-streak with strong bodies
    if not minute_green_streak_ok(minute_series, params.rise_bars, params.strong_body_min):
        return why("STREAK_FAIL")

    # 4) 1-second continuation (micro) — only if enabled
    if getattr(params, "use_micro_confirmation", False) or getattr(params, "require_micro_continuation", False):
        # Read 1s slice after the minute close
        sl = get_1s_slice_cached(ctx.symbol, minute_bar.close_time, params.micro_window_secs)
        if not one_sec_continuation_ok(
            sl,
            require_ema=getattr(params, "micro_require_ema_reclaim", True),
            require_vwap=getattr(params, "micro_require_vwap_hold", False),
            min_green_ratio=getattr(params, "micro_min_green_ratio", 0.60),
            allow_first_pullback=getattr(params, "micro_allow_first_pullback", True)
        ):
            return why("MICRO_CONTINUATION_FAIL")

    # 5) Eligible
    return ok()
```

**Helper for 1m green-streak with strong bodies**

```python
def minute_green_streak_ok(minute_series, rise_bars:int, strong_body_min:float) -> bool:
    last = minute_series[-rise_bars:]
    if len(last) < rise_bars:
        return False
    for c in last:
        if c.close <= c.open:
            return False
        body = abs(c.close - c.open)
        rng  = max(c.high - c.low, 1e-8)  # guard against zero range
        if (body / rng) < strong_body_min:
            return False
    return True
```

---

## 4) WHY logging (uniform reasons)
Add or confirm the following reasons are emitted to logs and counters:

- `WHY BAND_FAIL` — price/gap band mismatch  
- `WHY PMVOL_FAIL` — insufficient premarket volume  
- `WHY GATE_FAIL` — early open gate not satisfied  
- `WHY EMA_SLOPE_FAIL` — EMA slope/confirm failed  
- `WHY VWAP_FAIL` — VWAP slope/hold failed  
- `WHY STREAK_FAIL` — 1m green-streak or strong body thresholds not met  
- `WHY MICRO_CONTINUATION_FAIL` — 1s window failed continuation rules  
- `WHY OK` — candidate eligible

These should appear in both per-trade logs and daily summaries.

---

## 5) Data access — one-second loader & cache
**New file (recommended):** `src/midas_v2/data/one_sec_loader.py`

```python
# Minimal interface for a 1s slice loader and a tiny cache

_one_sec_cache = {}

def load_1s_slice(symbol: str, dt_minute_close, seconds: int):
    \"\"\"Return an iterable of dicts or rows with fields:
    ts, open, high, low, close, volume (one row per second)
    covering [dt_minute_close, dt_minute_close + seconds).

    Implementation should wrap your Polygon 1s fetch used by check_polygon_1s.py
    and normalize to a consistent schema.\
    \"\"\"
    raise NotImplementedError

def get_1s_slice_cached(symbol, minute_close_ts, seconds, loader=load_1s_slice):
    key = (symbol, minute_close_ts, seconds)
    if key not in _one_sec_cache:
        _one_sec_cache[key] = loader(symbol, minute_close_ts, seconds)
    return _one_sec_cache[key]
```

**Alternative:** If you already have a loader, expose an alias `get_1s_slice_cached` in `strategy.py` reusing that function.

---

## 6) micro_confirm.py — function contract (docstring)
Ensure `one_sec_continuation_ok` is documented to accept the parameters we’ll use:

```python
def one_sec_continuation_ok(
    one_sec_bars,
    require_ema: bool = True,
    require_vwap: bool = False,
    min_green_ratio: float = 0.60,
    allow_first_pullback: bool = True
) -> bool:
    \"\"\"Return True if the first micro window after the 1-minute close
    continues up (e.g., >= min_green_ratio green seconds), respecting EMA/VWAP flags.

    Expected input schema: iterable of rows/dicts with fields
    'open','close','high','low','ts','volume' (one row per second).

    Implementation details are up to micro_confirm.py; unit tests will enforce behavior.
    \"\"\"
```

> If your current function already exists but has different names/args, adjust the call site (strategy) to match.

---

## 7) CLI overrides (backtester)
If your CLI supports these flags, map them to scenario params for A/B testing without editing JSON:

```
--rise-bars 3
--strong-body-min 0.22
--use-micro-confirmation true
--micro-window-secs 60
--micro-require-ema true
--micro-require-vwap false
--micro-min-green-ratio 0.60
--micro-allow-first-pullback true
```

**Precedence:** runner/CLI flags override JSON.

---

## 8) Analyzer updates
Record and report:
- Count of candidates that **passed** minute streak but **failed** micro continuation.
- WR/PnL deltas with micro ON vs OFF.
- (Optional) histogram of green-ratio in the 1s window for winners vs losers.

This gives you a direct read on how much the micro step filters false breaks.

---

## 9) Tests
- Keep `micro_smoke_test.py` passing.
- Add a **failing fixture** (1m streak passes; 1s continuation fails) → assert `MICRO_CONTINUATION_FAIL` in logs.
- Add a **passing fixture** (both pass) → assert `OK`.
- Gate test: with `gate_minutes` not met, ensure micro check does **not** run.

---

## 10) Rollout & Safety
1. Back up / copy `strategy.py` before editing.
2. Implement the changes in v0.4.8 working directory.
3. Run day checks (2–3 known symbols).
4. Run short Aug range (Aug 5–7, 2025).
5. Compare metrics with micro ON/OFF.
6. If stable/positive → tag v0.4.8 (code).

---

## 11) Optional future refinements (not for v0.4.8)
- **Dynamic `micro_min_green_ratio`** based on catalyst score or RVOL.
- **VWAP slope** requirement at 1s granularity (not just hold).
- **Latency guard** for live trading (ensure 1s slice is complete before decision).
- **Adaptive window**: shorten to 20–30s if early continuation is strongly positive.

---

## Appendix A — Example log lines
```
WHY STREAK_FAIL symbol=STTK minute=2025-08-05T09:41:00Z body_ratio=0.18<thresh=0.22
WHY MICRO_CONTINUATION_FAIL symbol=STTK window=[09:41:00,09:42:00) green_ratio=0.48<thresh=0.60 ema_hold=True vwap=False
WHY OK symbol=STTK minute=2025-08-05T09:43:00Z
```
