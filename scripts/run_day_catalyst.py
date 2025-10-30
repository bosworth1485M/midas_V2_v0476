#!/usr/bin/env python3
# scripts/run_day_catalyst.py
"""
Run a single-day backtest using a prebuilt hybrid universe, with optional
news gating, band enforcing, and RVOL gating.

Outputs under out/<YYYYMMDD>/<SCENARIO>_hybrid/:
  - universe_used.txt
  - results_<DATE>.csv           (from midas_v2 backtester)
  - summary_hybrid_<DATE>.txt    (RUN SUMMARY + PER-SYMBOL table)

Key behaviors:
  • Accepts --band-min/--band-max; when --enforce-band is set, uses EFFECTIVE values
    (CLI override wins; else config; else None).
  • Shows OpenRVOL as the EFFECTIVE value in both [CFG] and RUN SUMMARY.
  • Loads gap_map sidecar (out/<YYYYMMDD>/scanner/gap_map_<DATE>.json) so per-symbol
    gap% / in_band / type are filled.
  • Prints the summary (and a human-readable Profile) to the console and writes the file.
  • Forwards --min-rvol-open and --gate-minutes to the backtester as CLI flags (flags > env > scenario).
  • NEW: Caps the FINAL post-news list with --top (so Top-N actually trims the traded list on news-only days).
"""

import argparse
import csv
import json
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ----------------------------- utilities -----------------------------

def sh(cmd, env=None):
    print("[CMD]", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True, env=env)

def ensure_env():
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    return env

def read_lines(path: Path):
    try:
        return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except FileNotFoundError:
        return []

def parse_catalyst_csv(path: Path):
    """Return dict: symbol -> {'score': float, 'headline': str}"""
    out = {}
    if not path or not path.exists():
        return out
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sym = (row.get("symbol") or row.get("Symbol") or "").strip().upper()
            if not sym:
                continue
            score_raw = row.get("score") or row.get("Score")
            try:
                score = float(score_raw) if score_raw not in (None, "", "None") else None
            except:
                score = None
            hl = row.get("headline") or row.get("Headline") or ""
            out[sym] = {"score": score, "headline": hl}
    return out

def safe_float(x):
    try:
        return float(x)
    except:
        return None

def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def read_config_bands():
    """
    Try to read default band min/max from config files if present.
    Recognizes a few common key names. Falls back to (None, None).
    """
    candidates = [
        ROOT / "config" / "scanner.json",
        ROOT / "config" / "scenarios.json",
        ROOT / "config" / "config.json",
    ]
    keys_try = [
        ("gap_min", "gap_max"),
        ("band_min", "band_max"),
        ("min_gap_pct", "max_gap_pct"),
    ]

    def hunt(d):
        for kmin, kmax in keys_try:
            if kmin in d and kmax in d:
                return safe_float(d[kmin]), safe_float(d[kmax])
        for k in ("scanner", "gap", "bands"):
            if isinstance(d.get(k), dict):
                v = hunt(d[k])
                if v != (None, None):
                    return v
        return (None, None)

    for p in candidates:
        data = read_json(p)
        if data:
            v = hunt(data)
            if v != (None, None):
                return v
    return (None, None)

def ymd_parts(date_str: str):
    ds = date_str
    ymd = ds.replace("-", "")
    return ds, ymd

def write_universe_used(symbols, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "universe_used.txt"
    path.write_text("\n".join(symbols) + "\n", encoding="utf-8")
    return path

def results_csv_path(out_dir: Path, date_str: str):
    return out_dir / f"results_{date_str}.csv"

def summarize_results(results_csv: Path):
    """
    Parse results CSV with columns at least: symbol,outcome,pnl
    Returns: (tp_count, sl_count, wr_pct, pnl_total, per_symbol dict)
    per_symbol: sym -> {'trades': n, 'tp': x, 'sl': y, 'pnl': sum}
    """
    tp = sl = 0
    pnl_total = 0.0
    per_symbol = {}
    if not results_csv.exists():
        return (0, 0, 0.0, 0.0, per_symbol)
    with results_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sym = (row.get("symbol") or row.get("Symbol") or "").strip().upper()
            outcome = (row.get("outcome") or row.get("Outcome") or "").strip().upper()
            pnl = safe_float(row.get("pnl") or row.get("PnL"))
            pnl = pnl or 0.0
            pnl_total += pnl
            if outcome == "TP":
                tp += 1
            elif outcome == "SL":
                sl += 1
            d = per_symbol.setdefault(sym, {"trades": 0, "tp": 0, "sl": 0, "pnl": 0.0})
            d["trades"] += 1
            if outcome == "TP":
                d["tp"] += 1
            elif outcome == "SL":
                d["sl"] += 1
            d["pnl"] += pnl
    used = tp + sl
    wr = (tp / used * 100.0) if used > 0 else 0.0
    return (tp, sl, wr, pnl_total, per_symbol)

def print_news_selection(catalyst_map, used_syms, min_score, src_path):
    print(f"[NEWS] Selected from catalyst (source: {src_path} , min_score={min_score})")
    kept = []
    for s in used_syms:
        info = catalyst_map.get(s)
        if info and info.get("score") is not None and info["score"] >= min_score:
            kept.append(s)
            title = (info.get("headline") or "").strip()
            print(f"  - {s}: score={int(info['score']) if info['score'] is not None else '?'}  {title[:120]}")
    print(f"[NEWS] counts: picked_from_news={len(kept)}  gap_only={max(0, len(used_syms)-len(kept))}  total_used={len(used_syms)}")

# ---------- pretty profile helpers ----------

def _fmt_num(x):
    if x is None:
        return "?"
    try:
        xf = float(x)
        return str(int(xf)) if xf.is_integer() else f"{xf:.2f}"
    except Exception:
        return str(x)

def _build_profile(require_news, news_first, top, band_min_eff, band_max_eff, min_rvol_open_eff):
    parts = []
    parts.append("newsOnly" if require_news else ("newsFirst" if news_first else "mixed"))
    if top:
        try:
            parts.append(f"Top-{int(top)}")
        except Exception:
            parts.append(f"Top-{top}")
    if band_min_eff is not None or band_max_eff is not None:
        parts.append(f"band {_fmt_num(band_min_eff)}-{_fmt_num(band_max_eff)}")
    if min_rvol_open_eff is not None:
        parts.append(f"RVOL {_fmt_num(min_rvol_open_eff)}")
    return " + ".join(parts)

# ----------------------------- main flow -----------------------------

def main():
    ap = argparse.ArgumentParser(description="Run a single-day backtest with hybrid universe + catalyst gating.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--universe", required=True, help="Path to hybrid universe file (symbols, one per line).")
    ap.add_argument("--top", type=int, default=None, help="Top-N informational label (final cap applied post-news).")
    ap.add_argument("--no-exclude", action="store_true")
    ap.add_argument("--extra-exclude", type=str, help="Comma-separated tickers to exclude.")
    ap.add_argument("--catalyst", type=str, help="CSV with columns: symbol,score,headline")
    ap.add_argument("--news-first", action="store_true")
    ap.add_argument("--require-news", action="store_true")
    ap.add_argument("--news-min-score", type=float, default=1.0)
    ap.add_argument("--enforce-band", action="store_true")
    ap.add_argument("--macd-rise-bars", type=int, help="Optional override for backtester via env MIDAS_MACD_RISE_BARS")
    ap.add_argument("--gate-minutes", type=int, help="Optional override for backtester via env/CLI gate minutes")
    ap.add_argument("--min-rvol-open", type=float, help="Optional override for backtester via env/CLI MIDAS_MIN_RVOL_OPEN")

    # band overrides (effective values win over config)
    ap.add_argument("--band-min", type=float, help="Override min gap%% band for enforce-band (e.g., 10).")
    ap.add_argument("--band-max", type=float, help="Override max gap%% band for enforce-band (e.g., 40).")

    args = ap.parse_args()
    env = ensure_env()

    ds, ymd = ymd_parts(args.date)
    out_dir = ROOT / f"out/{ymd}/{args.scenario}_hybrid"
    universe_path = Path(args.universe)

    print(f"[CATALYST-DAY] date={ds} scenario={args.scenario} universe={universe_path}")
    print(f"[OUT] {out_dir}")

    # ------------------- load base universe + catalyst -------------------
    base_list = read_lines(universe_path)
    catalyst_map = parse_catalyst_csv(Path(args.catalyst)) if args.catalyst else {}

    # require-news / news-first handling
    min_score = args.news_min_score if args.news_min_score is not None else 1.0
    news_syms = [s for s in base_list if catalyst_map.get(s, {}).get("score") is not None and catalyst_map[s]["score"] >= min_score]

    if args.require_news:
        used_syms = news_syms[:]  # strict intersection
    elif args.news_first:
        rest = [s for s in base_list if s not in news_syms]
        used_syms = news_syms + rest
    else:
        used_syms = base_list[:]

    # Exclusions
    if args.extra_exclude:
        extra = {s.strip().upper() for s in args.extra_exclude.split(",") if s.strip()}
        used_syms = [s for s in used_syms if s not in extra]
    if not args.no_exclude:
        pass  # place to apply a denylist if you maintain one

    # --- POST-NEWS CAP (final list) ---
    if args.top is not None and args.top > 0:
        used_syms = used_syms[:args.top]

    # ------------------- preflight: configured bands ---------------------
    band_min_cfg, band_max_cfg = read_config_bands()
    print(f"[PREFLIGHT] Gap band (scanner.json/scenarios.json): min={band_min_cfg} max={band_max_cfg}")

    # Effective knobs: CLI overrides win over config
    band_min_eff = args.band_min if args.band_min is not None else band_min_cfg
    band_max_eff = args.band_max if args.band_max is not None else band_max_cfg
    min_rvol_open_eff = args.min_rvol_open  # if None, backtester will use its config

    # gap map (for filtering AND per-symbol rows)
    gap_map = {}
    guess_gap_json = ROOT / f"out/{ymd}/scanner/gap_map_{ds}.json"
    gm = read_json(guess_gap_json)
    if isinstance(gm, dict):
        for k, v in gm.items():
            gap_map[str(k).upper()] = safe_float(v)

    # ------------------- enforce band using effective values -------------
    removed = 0
    if args.enforce_band and (band_min_eff is not None or band_max_eff is not None):
        def in_band_val(g):
            if g is None:
                return True  # unknown gap → keep
            ok_min = (band_min_eff is None or g >= band_min_eff)
            ok_max = (band_max_eff is None or g <= band_max_eff)
            return ok_min and ok_max
        kept_syms = []
        for s in used_syms:
            g = gap_map.get(s)  # may be None
            if in_band_val(g):
                kept_syms.append(s)
            else:
                removed += 1
        used_syms = kept_syms
        print(f"[FILTER] enforce-band removed {removed} out-of-band symbol(s)")
    elif args.enforce_band:
        print("[FILTER] enforce-band requested but no effective band bounds found; skipped.")

    # ------------------- echo selection + news context -------------------
    out_dir.mkdir(parents=True, exist_ok=True)
    write_universe_used(used_syms, out_dir)
    print(f"[UNIVERSE] {len(used_syms)} symbols -> {out_dir / 'universe_used.txt'}")
    if used_syms:
        print("[UNIVERSE] " + ", ".join(used_syms[:32]))

    if args.catalyst and Path(args.catalyst).exists():
        print_news_selection(catalyst_map, used_syms, min_score, args.catalyst)

    # ------------------- config echo (effective values) ------------------
    scen_cfg = read_json(ROOT / "config" / "scenarios.json") or {}
    def pull(d, k): return d.get(k) if isinstance(d, dict) else None
    scen_d = pull(scen_cfg, args.scenario) or scen_cfg
    green_streak = pull(scen_d, "green_streak")
    macd_rise_bars_cfg = pull(scen_d, "macd_rise_bars")
    max_trades_per_symbol = pull(scen_d, "max_trades_per_symbol")
    daily_max_loss = pull(scen_d, "daily_max_loss")
    rvol_open_minutes = pull(scen_d, "rvol_open_minutes")

    backtest_env = ensure_env()
    if args.min_rvol_open is not None:
        backtest_env["MIDAS_MIN_RVOL_OPEN"] = str(args.min_rvol_open)
        print(f"[OVERRIDE] MIDAS_MIN_RVOL_OPEN={args.min_rvol_open}")
    if args.macd_rise_bars is not None:
        backtest_env["MIDAS_MACD_RISE_BARS"] = str(args.macd_rise_bars)
    if args.gate_minutes is not None:
        backtest_env["MIDAS_GATE_MINUTES"] = str(args.gate_minutes)

    print(f"[CFG] scenario= {args.scenario}  min_rvol_open= {min_rvol_open_eff}  rvol_open_minutes= {rvol_open_minutes}  "
          f"green_streak= {green_streak}  macd_rise_bars= {macd_rise_bars_cfg if args.macd_rise_bars is None else args.macd_rise_bars}  "
          f"max_trades_per_symbol= {max_trades_per_symbol}  daily_max_loss= {daily_max_loss}")

    # ------------------- run backtester (midas_v2.cli) -------------------
    universe_used_path = out_dir / "universe_used.txt"
    bt_cmd = [
        sys.executable, "-m", "midas_v2.cli", "backtest",
        "--date", ds,
        "--scenario", args.scenario,
        "--universe", str(universe_used_path),
        "--out", str(out_dir),
    ]
    # forward RVOL & gate flags to backtester as CLI (flags > env > scenario defaults)
    if args.min_rvol_open is not None:
        bt_cmd += ["--min-rvol-open", str(args.min_rvol_open)]
    if args.gate_minutes is not None:
        bt_cmd += ["--gate-minutes", str(args.gate_minutes)]

    try:
        sh(bt_cmd, env=backtest_env)
    except subprocess.CalledProcessError:
        print("[ERROR] backtest process failed.")
        raise

    # ------------------- summarize + write hybrid summary ----------------
    results_path = results_csv_path(out_dir, ds)
    tp, sl, wr, pnl_total, per_symbol = summarize_results(results_path)

    # Pre-format strings for summary row (ASCII only to avoid mojibake)
    score_str = f">={int(min_score) if float(min_score).is_integer() else min_score}"
    top_str   = f"{args.top}" if args.top is not None else "—"
    band_min_str = f"{band_min_eff:.2f}" if band_min_eff is not None else "?"
    band_max_str = f"{band_max_eff:.2f}" if band_max_eff is not None else "?"
    band_str = f"{band_min_str}% / {band_max_str}%" if args.enforce_band else "—"
    open_rvol_str = f"{min_rvol_open_eff:.2f}" if min_rvol_open_eff is not None else "None"
    news_first_str = "Yes" if args.news_first else "No"
    enforce_str    = "Yes" if args.enforce_band else "No"

    summary_path = out_dir / f"summary_hybrid_{ds}.txt"
    lines = []
    lines.append(f"{args.scenario}: TP={tp} SL={sl} Win%={wr:.2f} PnL={pnl_total:.2f}")          # [0]
    lines.append(f"[PROFILE] {_build_profile(args.require_news, args.news_first, args.top, band_min_eff, band_max_eff, min_rvol_open_eff)}")  # [1]
    lines.append("")                                                                              # [2]
    lines.append("[RUN SUMMARY]")                                                                 # [3]
    lines.append("Date      | Scen | News-first | Score | Top | Band             | Enforce | OpenRVOL       | Used |   WR   | TP/SL |   PnL")  # [4]
    lines.append("-------------------------------------------------------------------------------------------------------------------------------")  # [5]
    lines.append(f"{ds} | {args.scenario:<3}| {news_first_str:<10} | {score_str:<3} | {top_str:>3} | {band_str:<16} | {enforce_str:<7} | {open_rvol_str:<14} | {tp+sl:>4} | {wr:>7.2f}% | {tp:>2}/{sl:<2} | {pnl_total:>6.2f}")  # [6]
    lines.append("")                                                                              # [7]
    lines.append("[PER-SYMBOL]")                                                                  # [8]
    lines.append(f"[DEFS] in_band=yes if {band_min_str}% <= gap <= {band_max_str}% (inclusive) ; type=standard if in_band ; type=rocket if gap > 40.00%")  # [9]
    lines.append("symbol   included_by  news_score  gap%    in_band  type     traded  trades  TP  SL    PnL   headline")  # [10]

    def in_band_gap(g):
        if g is None:
            return None
        ok_min = (band_min_eff is None or g >= band_min_eff)
        ok_max = (band_max_eff is None or g <= band_max_eff)
        return ok_min and ok_max

    for s in used_syms:
        info = catalyst_map.get(s, {})
        score = info.get("score")
        headline = (info.get("headline") or "").strip()
        g = gap_map.get(s)
        g_str = f"{g:>5.2f}" if g is not None else "?   "
        ib = in_band_gap(g)
        ib_str = "yes" if ib else ("no" if ib is not None else "?")
        typ = "standard" if (ib is True) else ("rocket" if (g is not None and g > 40.0) else "?")
        stats = per_symbol.get(s, {"trades": 0, "tp": 0, "sl": 0, "pnl": 0.0})
        included_by = "news" if s in news_syms else "gap"
        lines.append(f"{s:<7} {included_by:<12} {int(score) if score is not None else '':>10}  "
                     f"{g_str:<6} {ib_str:<7} {typ:<8} "
                     f"{'yes' if stats['trades']>0 else 'no ':<7} {stats['trades']:>6}  "
                     f"{stats['tp']:>2}  {stats['sl']:>2}  {stats['pnl']:>6.2f}  {headline[:80]}")

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] Backtest complete -> {results_path}")
    print(f"[OK] Hybrid summary saved -> {summary_path}")

    # --- Console echo (classic behavior + profile) ---
    print("\n[SUMMARY]")
    print(lines[0])  # one-liner
    print(lines[1])  # [PROFILE] …
    print(lines[4])  # header
    print(lines[5])  # separator
    print(lines[6])  # summary row
    print("")

if __name__ == "__main__":
    main()