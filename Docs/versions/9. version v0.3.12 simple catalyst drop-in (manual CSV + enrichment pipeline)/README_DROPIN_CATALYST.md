# Drop‑in Catalyst (Minimal Steps)

## What this gives you
- Manual catalyst tagging for a single day (no APIs).
- A small enrichment script that filters your `universe_sample.txt` down to only catalyst tickers so your existing `run_day_simple.py` can work **without config edits**.

## Files
- `data/manual_catalysts/20250805.csv` – sample manual tags (STTK prefilled).
- `scripts/enrich_universe_catalyst.py` – reads manual CSV and rewrites `data/samples/universe_sample.txt` to contain only those tickers with catalysts.

## How to use in your project
1) Copy the **contents of this folder** into your project root (Midas_V2). Preserve subfolders.
2) Generate your universe the normal way for a day (e.g., 2025‑08‑05).
   - This should create `data/universe/universe_2025-08-05.csv` **or** update `data/samples/universe_sample.txt`.
3) Run the enrichment script (this will filter the TXT universe to only catalyst symbols):

   ```
   python scripts/enrich_universe_catalyst.py --date 2025-08-05 --root .
   ```

4) Run your backtest as usual (now the universe contains **only catalyst tickers**):

   ```
   python scripts/run_day_simple.py --date 2025-08-05 --scenario D
   ```

> You can add more rows to `data/manual_catalysts/20250805.csv` (one per symbol). Repeat for other dates by creating `YYYYMMDD.csv` files.
