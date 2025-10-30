# Midas_V2 – v0.3.12 Documentation
### Filters Roadmap (China Exclusion, Catalyst Requirement, Market Context Logging)

## Version Context
- **Previous tag:** v0.3.11 (pre-flight project guard + docs).  
- **This tag:** **v0.3.12-filters-roadmap**.  
- **Purpose:** Add optional filters (China exclusion, catalyst requirement) and logging (market context) without breaking existing scenario logic.

---

## A. Principles & Scope
- **Keep Scenario logic intact** (A–E). Filters live *before* strategy triggers.
- **No breaking changes**: default behavior remains identical with flags **off**.
- **Minimal new files**; prefer editing existing scripts.
- **One‑liners only** for run commands.

---

## B. Config Flags (add to `config/settings.json` or `scenarios.json`)
Add a new, global `filters` block and per‑scenario overrides optional.

```json
{
  "filters": {
    "exclude_china": true,
    "require_catalyst": true,
    "catalyst_window_minutes": 240,   
    "market_ctx": {
      "enable": true,
      "symbol": "SPY",            
      "gate": false,               
      "gate_min_change_pct": 0.60, 
      "gate_window_minutes": 30     
    }
  }
}
```

**Notes**
- `exclude_china=true` drops CN issuers from the *universe* before backtesting.
- `require_catalyst=true` keeps only symbols with a recognized news catalyst within the window prior to first trade gate (e.g., 4h pre‑open → gate time).
- `market_ctx.enable=true` merely logs the context; `gate=false` means “do not filter yet.” Turn on later if experiments show benefit.

---

## C. Data Plumbing (minimal, additive)
1. **Universe with metadata**
   - Extend `scripts/topgappers.py` to output `data/universe/universe_YYYY-MM-DD.csv` with columns:
     - `date,symbol,price,gap_pct`
     - **new:** `country, is_china, has_catalyst, catalyst_source, catalyst_type, catalyst_time`
   - Keep the plain `universe_sample.txt` for backward compatibility.

2. **Backtester intake**
   - In `midas_v2/loader/universe.py` (or equivalent), if the CSV exists, join metadata into the per‑symbol run context; else fall back to TXT.

3. **Run‑day script** (`scripts/run_day_simple.py`)
   - Add `--use-universe-csv` (default **on** if file exists).
   - Respect `filters.exclude_china` and `filters.require_catalyst` when constructing the working symbol list.

---

## D. China Filter (deterministic, simple)
**Strategy** (fastest path):
1. Use issuer country / country of incorporation from your **reference endpoint** (Polygon `v3/reference/tickers`, cached locally).
2. Mark `is_china = (country in {CN}) OR (exchange in {HKEX} ADR→CN)`.
3. Maintain a small **denylist** for edge cases (e.g., shell ADRs): `config/denylist_china.txt` (optional).

**Implementation**
- Edit `scripts/topgappers.py`:
  - When building the daily universe, query/cached‑read reference metadata → set `country` and `is_china`.
  - If `exclude_china`, drop those rows before writing `universe_YYYY-MM-DD.csv`.
- Caching: write `data/ref/ticker_meta.parquet` keyed by `symbol` with `country, exchange, last_updated`.

**Acceptance**
- For a known CN small‑cap, confirm it is excluded when the flag is on and included when off.

---

## E. Catalyst Filter (modular, keyword‑based first; API later)
**Two‑phase plan**
1. **Phase 1 – Heuristic/Keyword (no new subscription requirements)**
   - Parse pre‑market PR/news text from a lightweight source you already have or from locally stored notes.
   - Accept keywords: `['earnings', 'FDA', 'phase', 'trial', 'approval', 'agreement', 'contract', 'guidance', 'merger', 'acquisition', 'partnership', 'licensing', 'ticker mentions + %']`.
   - Time gate: within `catalyst_window_minutes` before the strategy gate.
   - Store `has_catalyst (bool)`, `catalyst_type`, `catalyst_time`, `catalyst_source` in universe CSV.

2. **Phase 2 – API‑based (Polygon News, Finnhub, Benzinga, etc.)**
   - Add `scripts/fetch_news.py --date YYYY-MM-DD --symbols <file>` that populates `data/news/YYYYMMDD/<SYMBOL>.json`.
   - Simple scorer selects the top most relevant headline and sets `has_catalyst` + fields above.

**Implementation (Phase 1, minimal changes)**
- Extend `scripts/topgappers.py` to call a small helper `src/midas_v2/services/catalyst.py`:
  - `infer_catalyst(symbol, date) -> (has_catalyst, type, ts, source)`
  - Start with a stub that reads from `data/manual_catalysts/YYYYMMDD.csv` (manual tagging allowed). This lets you backfill past days rapidly.
- Later swap stub with API calls without changing the call‑site.

**Backtest filter**
- If `require_catalyst=true`, keep only rows where `has_catalyst==True`.

**Acceptance**
- Manually tag 2–3 symbols for 2025‑08‑05; confirm only tagged ones are traded when `require_catalyst=true`.

---

## F. Market Context (log now, experiment later)
**What to log**
- `SPY` (or `DIA`) % change from prior close to: (a) open, (b) gate time, (c) 30‑min window high/low.
- Simple trend label at gate: `UP` if price > VWAP & 9‑EMA on 1‑min; else `DOWN`.

**Implementation**
- In `scripts/run_day_simple.py` before processing symbols:
  - Load SPY minute bars for the date (you already fetch minutes).
  - Compute `pct_from_prev_close`, `intraday_change_0_30m`, `vwap_relation`.
  - Persist to `out/<DATE>/market_ctx.json` and attach to run summary.

**Optional gate (off by default)**
- If `filters.market_ctx.gate=true`, then proceed only if `intraday_change_0_30m >= gate_min_change_pct`.

**Acceptance**
- Verify JSON appears and contains fields; when `gate=true`, confirm symbols are skipped if the condition fails.

---

## G. CLI Additions (one‑liners)
1. **Single day (auto‑universe, filters applied)**
```
python scripts/run_day_simple.py --date 2025-08-05 --scenario D
```

2. **Range run with summaries (filters respected)**
```
python scripts/run_range_and_summarize.py --start 2025-08-05 --end 2025-08-31 --scenario D
```

3. **Rebuild summaries after toggling flags**
```
python scripts/rebuild_range_summary.py --start 2025-08-05 --end 2025-08-31 --scenario D
```

*No extra flags needed; the scripts read `filters` from config and the universe CSV if present.*

---

## H. Metrics & Reporting
- Add columns to daily results summary:
  - `n_universe_pre`, `n_after_china_filter`, `n_after_catalyst_filter`.
  - Market context snapshot: `spy_gate_pct`, `spy_trend_gate`.
- Compare WR/PnL with a 2×2 matrix over a month:
  - Baseline vs `exclude_china`            
  - Baseline vs `require_catalyst`
- Target: **WR +3–8 pts** from China exclusion; **WR +5–12 pts** from Catalyst (historically typical in similar projects).

---

## I. Minimal Code Changes (file‑by‑file)
- `scripts/topgappers.py`
  - + reference lookup (country/exchange) with small local cache
  - + write `universe_YYYY-MM-DD.csv` with metadata columns
  - + stubbed `infer_catalyst()` call (manual file first)
- `scripts/run_day_simple.py`
  - + detect CSV universe and read metadata
  - + apply filters based on config
  - + compute market context JSON (always log)
- `midas_v2/loader/universe.py` (or similar intake)
  - + merge metadata into symbol context; expose `ctx.is_china`, `ctx.has_catalyst`
- `config/settings.json` (or `scenarios.json`)
  - + `filters` block shown above
- `tools/` (optional)
  - `services/catalyst.py` (stub now → API later)

---

## J. Backfill & Manual Tagging Workflow (fast start)
1. Create `data/manual_catalysts/20250805.csv` with headers:
   - `symbol,catalyst_type,catalyst_time,catalyst_source`
2. Rerun `run_day_simple.py`; the stub marks `has_catalyst` from this file.
3. Iterate a few days to validate lift before wiring an external News API.

---

## K. Versioning & Guardrails
1. Commit and tag this change set:
```
git add -A && git commit -m "v0.3.12: China exclusion + catalyst filter (stub) + market context logging" && git tag -a v0.3.12 -m "v0.3.12: Filters roadmap implemented" && git push && git push --tags
```
2. If anything regresses:
```
git reset --hard v0.3.11 && git push --force-with-lease
```

---

## L. Validation Plan (7‑day pilot)
1. Run **D_strict** for 2025‑08‑05 → 2025‑08-31 with `exclude_china=true`, `require_catalyst=false`. Capture lift.
2. Repeat with `require_catalyst=true` using manual tags for top movers only.
3. Compare WR/PnL; if positive, keep flags on and proceed to API integration for catalysts.

---

## M. Future (API Catalyst, Better Features)
- Plug Polygon/Benzinga/Finnhub news → replace manual CSV.
- Add **“quality score”** for catalysts (e.g., FDA > earnings > PR fluff) to scale risk sizing later.
- Consider **sector heat** and **opening RVOL gate** once filters stabilize.

---

## N. Quick To‑Do Checklist
- [ ] Add `filters` block to config
- [ ] Patch `topgappers.py` to emit universe CSV with metadata
- [ ] Implement stubbed `infer_catalyst()` backed by `data/manual_catalysts/`
- [ ] Modify `run_day_simple.py` to read CSV + apply filters
- [ ] Log `market_ctx.json` per day
- [ ] Run 7‑day pilot; compare WR/PnL
- [ ] Tag results and decide on API integration
