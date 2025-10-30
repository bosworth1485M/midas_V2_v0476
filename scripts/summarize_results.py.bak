#!/usr/bin/env python3
# scripts/summarize_results.py
# v0.3.21: prints to console, writes authoritative one-pager, appends Run Parameters footer

import argparse, csv, json
from pathlib import Path

SCENARIOS = ["A", "B", "C", "D", "E"]
CAT_SUFFIXES = ["", "_catalyst"]  # baseline + catalyst variant

def read_csv_rows(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        return list(r)

def summarize_result_file(path: Path):
    rows = read_csv_rows(path)
    tp = sum(1 for r in rows if (r.get("outcome") or "").upper() == "TP")
    sl = sum(1 for r in rows if (r.get("outcome") or "").upper() == "SL")
    n = tp + sl
    win = (tp / n * 100.0) if n else 0.0
    return tp, sl, win, n

def load_scenarios_config(cfg_path: Path = Path("config/scenarios.json")):
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def read_cfg_snapshot(out_day_dir: Path):
    """
    Optional: if a runner/CLI dropped a params snapshot (e.g., _last_cfg.json or _cfg.json),
    load it to reflect CLI overrides like min_rvol_open. Otherwise return {}.
    """
    for name in ["_last_cfg.json", "_cfg.json", "_params.json"]:
        p = out_day_dir / name
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    return {}

def infer_catalyst_mode(cat_universe_csv: Path):
    """
    Infer catalyst details from catalyst_universe_<DATE>.csv if present.
    Returns dict like {"picked": N, "a_only": True/False} or {}.
    """
    if not cat_universe_csv.exists():
        return {}
    rows = read_csv_rows(cat_universe_csv)
    picked_rows = [r for r in rows if str(r.get("picked", "0")) in ("1", "True", "true")]
    a_only = True
    for r in picked_rows:
        try:
            if int(r.get("grade", "0")) < 2:
                a_only = False
                break
        except Exception:
            pass
    return {"picked": len(picked_rows), "a_only": a_only}

def main():
    ap = argparse.ArgumentParser(description="Summarize A–E (and catalyst) results for a given date and write the authoritative one-pager.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()

    date = args.date
    ymd = date.replace("-", "")
    out_day = Path("out") / ymd
    final_dir = out_day / "_final"
    final_dir.mkdir(parents=True, exist_ok=True)
    out_path = final_dir / f"summary_only_{date}.txt"

    # 1) Summaries (baseline + catalyst)
    lines = []
    found_any = False
    for s in SCENARIOS:
        for suf in CAT_SUFFIXES:
            dir_name = f"{s}{suf}"
            res_csv = out_day / dir_name / f"results_{date}.csv"
            if res_csv.exists():
                tp, sl, win, n = summarize_result_file(res_csv)
                label = f"{s}" if suf == "" else f"{s} (catalyst)"
                lines.append(f"{label}: TP={tp} SL={sl} Win%={win:.2f}")
                found_any = True

    if not found_any:
        lines.append("No scenario result files found for this date.")

    # Print to console (keeps old behavior)
    for ln in lines:
        print(ln)

    # 2) Write authoritative summary
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[AUTHORITATIVE] Wrote {out_path}")

    # 3) Append Run Parameters footer (self-documenting)
    scenarios_cfg = load_scenarios_config()
    cfg_snapshot = read_cfg_snapshot(out_day)

    footer = []
    footer.append("\n---")
    footer.append("Run Parameters:")

    # Which scenarios contributed lines
    present = []
    for s in SCENARIOS:
        if (out_day / s / f"results_{date}.csv").exists() or (out_day / f"{s}_catalyst" / f"results_{date}.csv").exists():
            present.append(s)
    footer.append(f"  scenarios_in_summary = {', '.join(present) if present else 'n/a'}")

    # Compact param block per present scenario from scenarios.json defaults
    for s in present:
        p = (scenarios_cfg.get(s, {}) or {}).get("params", {})
        if not p:
            continue
        footer.append(
            f"  [{s}] tp_pct/sl_pct={p.get('tp_pct')}/{p.get('sl_pct')}, "
            f"green_streak={p.get('green_streak','OFF')}, macd_rise_bars={p.get('macd_rise_bars','OFF')}, gate_minutes={p.get('gate_minutes')}, "
            f"min_pm_vol={p.get('min_pm_vol')}, "
            f"ema_confirm={p.get('ema_confirm')}, vwap_confirm={p.get('vwap_confirm')}, macd_confirm={p.get('macd_confirm')}"
        )

    # Catalyst hints (picked count + A-only inference)
    cat_dir = out_day / "catalyst"
    cat_universe_csv = cat_dir / f"catalyst_universe_{date}.csv"
    cat_info = infer_catalyst_mode(cat_universe_csv)
    if cat_info:
        footer.append(f"  [catalyst] picked={cat_info['picked']}, a_only={cat_info['a_only']}")

    # CLI/override hints (best-effort if a snapshot file exists)
    if cfg_snapshot:
        keys = ["min_rvol_open", "rvol_open_minutes", "max_trades_per_symbol", "daily_max_loss"]
        kv = ", ".join([f"{k}={cfg_snapshot.get(k)}" for k in keys if k in cfg_snapshot])
        if kv:
            footer.append(f"  [overrides] {kv}")

    # Append to file
    with out_path.open("a", encoding="utf-8") as f:
        f.write("\n".join(footer) + "\n")

    # Also echo footer to console (optional but handy)
    print("\n".join(footer))

if __name__ == "__main__":
    main()