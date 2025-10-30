#!/usr/bin/env python3
# scripts/write_compare_bundle.py
import argparse, ast, json, re, time
from pathlib import Path

def _to_float(x):
    try: return float(x)
    except: return None

def _to_int(x):
    try: return int(x)
    except: return None

def parse_summary_table(date_str: str, text: str):
    """
    Robustly extract (used, wr_pct, tp, sl, pnl, score, top, band_min, band_max, open_rvol)
    from the RUN SUMMARY row that begins with the date. We take the last 4 '|' cells
    as Used, WR%, TP/SL, PnL to avoid index drift.
    """
    used = wr = tp = sl = pnl = score = top = band_min = band_max = open_rvol = None
    for line in text.splitlines():
        if line.strip().startswith(date_str):
            cells = [c.strip() for c in line.split("|")]
            if len(cells) >= 8:
                # Always take the last 4 cells as Used, WR%, TP/SL, PnL
                used_str, wr_str, tpsl_str, pnl_str = cells[-4], cells[-3], cells[-2], cells[-1]

                # Score, Top, Band, OpenRVOL are in the mid cells (best-effort)
                # Find Band & OpenRVOL by scanning known labels
                # Try to locate "Band" and "OpenRVOL" by relative positions seen in your summaries:
                # ... | Score | Top | Band | Enforce | OpenRVOL | Used | WR% | TP/SL | PnL
                # We search for a '...% / ...%' pattern for band, and first numeric for open_rvol
                for c in cells:
                    mband = re.search(r"(\d+(?:\.\d+)?)%\s*/\s*(\d+(?:\.\d+)?)%", c)
                    if mband:
                        band_min = _to_float(mband.group(1))
                        band_max = _to_float(mband.group(2))
                    mscore = re.search(r"(?:^|[^\d])(\d+(?:\.\d+)?)(?:$|[^\d])", c)
                    if (score is None) and ("≥" in c or ">=" in c):
                        # score column rendered like ">=2"
                        m = re.search(r"(\d+(?:\.\d+)?)", c)
                        if m: score = _to_float(m.group(1))
                    if (open_rvol is None) and (c.lower() != "none") and re.fullmatch(r"\d+(?:\.\d+)?", c):
                        # a lone number cell can be OpenRVOL in your table
                        open_rvol = _to_float(c)

                # Crisper way to get Score / Top: scan the date row tokens around Band:
                # not strictly required; summary JSON will still be filled from CLI params if provided

                # Parse Used / WR% / TP-SL / PnL
                used = _to_int(used_str)
                wr   = _to_float(wr_str.rstrip("% ").strip())
                mp   = re.search(r"(-?\d+(?:\.\d+)?)", pnl_str or "")
                if mp: pnl = _to_float(mp.group(1))
                mts  = re.search(r"(\d+)\s*/\s*(\d+)", tpsl_str or "")
                if mts:
                    tp = _to_int(mts.group(1))
                    sl = _to_int(mts.group(2))
            break
    return used, wr, tp, sl, pnl, score, top, band_min, band_max, open_rvol

def main():
    ap = argparse.ArgumentParser(description="Write comparison TXT+JSON bundle for a completed run.")
    ap.add_argument("--date", required=True)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--universe", required=True)
    ap.add_argument("--catalyst-csv", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--label", default=None)

    # CLI overrides → JSON params
    ap.add_argument("--band-min", type=float)
    ap.add_argument("--band-max", type=float)
    ap.add_argument("--min-rvol-open", type=float)
    ap.add_argument("--rvol-open-minutes", type=int)
    ap.add_argument("--news-first", action="store_true")
    ap.add_argument("--require-news", action="store_true")
    ap.add_argument("--enforce-band", action="store_true")
    ap.add_argument("--top", type=int)
    ap.add_argument("--news-min-score", type=float)
    ap.add_argument("--deny-negative", action="store_true")
    ap.add_argument("--exclude-china", action="store_true")
    args = ap.parse_args()

    summary_path  = Path(args.summary)
    universe_path = Path(args.universe)
    catalyst_csv  = Path(args.catalyst_csv)
    out_dir       = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    # Read summary text
    try:
        summary_txt = summary_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        summary_txt = "[ERROR] summary not found; run may have failed earlier.\n"

    # Parse RUN SUMMARY row
    used, wr, tp, sl, pnl, score_p, top_p, band_min_p, band_max_p, open_rvol_p = parse_summary_table(args.date, summary_txt)

    # Fallback from the one-liner (B: TP=… SL=… Win%=… PnL=…)
    if (tp is None or sl is None or wr is None or pnl is None):
        m = re.search(r"\bTP\s*=\s*(\d+)\s+SL\s*=\s*(\d+)\s+Win%=\s*([\d.]+)\s+PnL=\s*([-+]?\d+(?:\.\d+)?)", summary_txt)
        if m:
            tp_f, sl_f, wr_f, pnl_f = m.groups()
            tp   = tp if tp   is not None else int(tp_f)
            sl   = sl if sl   is not None else int(sl_f)
            wr   = wr if wr   is not None else float(wr_f)
            pnl  = pnl if pnl is not None else float(pnl_f)
            if used is None and tp is not None and sl is not None:
                used = tp + sl

    # Detect booleans from text (low precedence)
    def has(token: str) -> bool | None:
        return True if token in summary_txt else None
    news_only_txt    = has("require-news active")
    news_first_txt   = has("news-first ordering applied")
    enforce_band_txt = has("enforce-band")

    # Try to pick RVOL fields from banner
    def grab(name: str):
        m = re.search(rf"{name}\s*=\s*([^\s]+)", summary_txt);  return m.group(1) if m else None
    min_rvol_open_txt     = grab("min_rvol_open")
    rvol_open_minutes_txt = grab("rvol_open_minutes")
    green_streak          = grab("green_streak")
    macd_rise_bars        = grab("macd_rise_bars")
    max_trades            = grab("max_trades_per_symbol")
    daily_max_loss        = grab("daily_max_loss")

    # WHY dict (StrategyParams) if present
    tp_pct = sl_pct = gate_minutes = None
    ema_confirm = vwap_confirm = macd_confirm = None
    rise_bars = min_pm_vol = None
    mwhy = re.search(r"Using StrategyParams:\s*(\{.*\})", summary_txt)
    if mwhy:
        try:
            d = ast.literal_eval(mwhy.group(1))
            tp_pct       = _to_float(d.get("tp_pct"))
            sl_pct       = _to_float(d.get("sl_pct"))
            gate_minutes = _to_int(d.get("gate_minutes"))
            ema_confirm  = bool(d.get("ema_confirm")) if d.get("ema_confirm") is not None else None
            vwap_confirm = bool(d.get("vwap_confirm")) if d.get("vwap_confirm") is not None else None
            macd_confirm = bool(d.get("macd_confirm")) if d.get("macd_confirm") is not None else None
            rise_bars    = _to_int(d.get("rise_bars"))
            min_pm_vol   = _to_int(d.get("min_pm_vol"))
        except Exception:
            pass

    # Final params (CLI > parsed)
    score           = args.news_min_score if args.news_min_score is not None else score_p
    top             = args.top            if args.top            is not None else top_p
    band_min        = args.band_min       if args.band_min       is not None else band_min_p
    band_max        = args.band_max       if args.band_max       is not None else band_max_p

    min_rvol_open_t = None if (min_rvol_open_txt in (None, "None")) else _to_float(min_rvol_open_txt)
    min_rvol_open   = args.min_rvol_open  if args.min_rvol_open  is not None else (min_rvol_open_t or open_rvol_p)

    rvol_open_minutes_t = None if (rvol_open_minutes_txt in (None, "None")) else _to_int(rvol_open_minutes_txt)
    rvol_open_minutes   = args.rvol_open_minutes if args.rvol_open_minutes is not None else rvol_open_minutes_t

    news_first      = True if args.news_first else news_first_txt
    news_only       = True if args.require_news else news_only_txt
    enforce_band    = True if args.enforce_band else enforce_band_txt
    deny_negative   = True if args.deny_negative else None
    exclude_china   = True if args.exclude_china else None

    # Write TXT (header + full summary)
    run_id = int(time.time())
    label  = args.label or "auto"
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    cmp_txt = out_dir / f"summary_{run_id}.txt"
    header = f"# TEST label={label} date={args.date} scenario={args.scenario} (self-described in JSON)\n\n"
    cmp_txt.write_text(header + summary_txt, encoding="utf-8")

    # Build JSON
    payload = {
        "schema_version": "compare.v1",
        "run_id": run_id,
        "label": label,
        "date": args.date,
        "scenario": args.scenario,
        "params": {
            "news_only": news_only, "news_first": news_first,
            "deny_negative": deny_negative, "exclude_china": exclude_china,
            "news_min_score": score, "top": top, "enforce_band": enforce_band,
            "band_min": band_min, "band_max": band_max,
            "min_rvol_open": min_rvol_open, "rvol_open_minutes": rvol_open_minutes,
            "green_streak": _to_int(green_streak) if green_streak not in (None, "None") else None,
            "macd_rise_bars": _to_int(macd_rise_bars) if macd_rise_bars not in (None, "None") else None,
            "max_trades_per_symbol": _to_int(max_trades) if max_trades not in (None, "None") else None,
            "daily_max_loss": _to_float(daily_max_loss) if daily_max_loss not in (None, "None") else None,
            "tp_pct": tp_pct, "sl_pct": sl_pct, "gate_minutes": gate_minutes
        },
        "metrics": { "wr_pct": wr, "pnl": pnl, "tp": tp, "sl": sl, "used": used },
        "filter_stats": None,
        "artifacts": {
            "summary_txt": str(Path(args.summary)),
            "universe_txt": str(Path(args.universe)),
            "catalyst_csv": str(Path(args.catalyst_csv)),
        }
    }

    cmp_json = out_dir / f"comparison_{run_id}.json"
    cmp_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[COMPARE] Wrote bundle -> {cmp_txt.name}, {cmp_json.name}")

if __name__ == "__main__":
    main()