# Addendum for Midas_V2 v0.4.6 — Polygon 1‑Second Data Check

This addendum documents **`scripts/check_polygon_1s.py`**, which we ran at the start to verify that 1‑second bars from Polygon are healthy before building micro‑level entry logic.

---

## 1) Purpose

- Verify that **1‑second OHLCV** data for a symbol and date is **present, continuous, and correctly ordered**.
- Surface any **gaps**, **timestamp drift**, or **schema issues** before we rely on micro‑signals.
- Produce a short **console report** (first/last timestamps, count of bars, sample rows).

This script complements the micro smoke tests by ensuring the **input data** is clean before we validate the **logic**.

---

## 2) Prerequisites

- A valid Polygon API key available to the script. Common patterns:
  - `.env` file with `POLYGON_API_KEY=...`
  - Or environment variable `POLYGON_API_KEY` set in the shell.
- Network access to Polygon’s historical data endpoints.
- Run from repository root so relative paths resolve.

---

## 3) Exact commands we use

> If unsure of flags, check the help first.

```powershell
python scripts\check_polygon_1s.py --help
```

**Typical invocation (example):**

```powershell
# Set project src on the path (if the script imports project code)
$env:PYTHONPATH='src'; python scripts\check_polygon_1s.py --date 2025-08-05 --symbol STTK --market-open 09:30:00 --market-close 16:00:00
```

- `--date YYYY-MM-DD` — trading session to fetch.
- `--symbol TICKER` — symbol to check.
- `--market-open/--market-close` — optional; helps the script confirm expected bar counts.

> If the script expects different flags on your machine, use `--help` output as the source of truth.

---

## 4) Expected console output (shape)

```
[OK] Polygon 1s fetch: symbol=STTK date=2025-08-05 bars=23400
     first=2025-08-05 09:30:00  last=2025-08-05 16:00:00
     gaps=0  dupes=0  non‑monotonic=0  tz=America/New_York
Sample:
time,open,high,low,close,volume
2025-08-05 09:30:00,10.01,10.05,9.98,10.03,1200
2025-08-05 09:30:01,10.03,10.07,10.01,10.06,1500
...
```

**How to read this:**
- **bars** should roughly match the open‑to‑close seconds (23,400 for 6.5 hours) if full‑day requested.
- **gaps/dupes/non‑monotonic** must be **zero**; otherwise we’ll distrust the day for micro‑testing.
- The **sample** confirms column order and numeric formatting.

---

## 5) What we were testing for

- **Presence** of 1‑second bars for the day and symbol(s) we plan to backtest.
- **Contiguity**: no missing seconds during market hours.
- **Ordering**: strictly increasing timestamps.
- **Sanity**: OHLC ranges make sense, volumes non‑negative.

If anything fails, we **stop** and diagnose the data (date/symbol choice, market holiday/half day, provider hiccup, API quota).

---

## 6) How this ties into the micro smoke tests

- `check_polygon_1s.py` validates **data quality**.
- `micro_smoke_test.py` validates **signal logic** (time gate, MACD rise, green streak, EMA/VWAP reclaim) on synthetic candles.
- Together, they ensure we won’t blame logic for **bad data** or vice‑versa.

---

## 7) Minimal runbook (copy/paste)

```powershell
# 1) Verify 1‑second data from Polygon for the target day/symbol
python scripts\check_polygon_1s.py --help
$env:PYTHONPATH='src'; python scripts\check_polygon_1s.py --date 2025-08-05 --symbol STTK --market-open 09:30:00 --market-close 16:00:00

# 2) Run the micro logic smoke tests (deterministic synthetic data)
$env:PYTHONPATH='src'; python src\midas_v2\micro\micro_smoke_test.py
```

**If both pass:** proceed to wire `find_first_entry()` into the main strategy.

---

## 8) Git add‑on (doc update only)

If you want to include this addendum in v0.4.6:

```powershell
python Docs\refresh_docs.py
git add -A
git commit -m "docs(v0.4.6): add Polygon 1s precheck (check_polygon_1s.py) and exact test commands"
git tag -f -a v0.4.6 -m "v0.4.6 updated docs: include 1s data precheck; micro smoke tests still 5/5"
git push
git push --tags --force
```

*(Use `-f/--force` on the tag only if you already created v0.4.6 and want the tag message to reflect this doc addition.)*

---

**Generated:** 2025-10-20 18:13:34
