#!/usr/bin/env python3
"""
Scan compare bundles (out/**/_comparisons/comparison_*.json), aggregate results,
and print leaderboards. Supports a human-readable Profile view, label-free grouping,
and an optional per-day breakdown table.

Examples:
  python scripts/scan_run_bundles.py --scenarios B --dedupe-latest --min-trades 1 --profile-only --per-day
  python scripts/scan_run_bundles.py --scenarios B,E
  python scripts/scan_run_bundles.py --dates 2025-08-05,2025-08-06
"""

import argparse, csv, glob, json, os, sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
OUT  = ROOT / "out"

# ------------------------ helpers ------------------------

def parse_list(s):
    if not s: return None
    return [x.strip() for x in s.split(",") if x.strip()]

def find_files(dates=None):
    if dates:
        files = []
        for ds in dates:
            ymd = ds.replace("-", "")
            files.extend(glob.glob(str(OUT / f"{ymd}" / "_comparisons" / "comparison_*.json")))
        return files
    return glob.glob(str(OUT / "*" / "_comparisons" / "comparison_*.json"))

def load_json_safe(fp):
    try:
        with open(fp, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _to_float(x, nd=None):
    try:
        v = float(x)
        return round(v, nd) if nd is not None else v
    except Exception:
        return None

def row_from_bundle(fp, data):
    """Normalize a comparison_* bundle to a single-row dict."""
    m  = data.get("metrics") or {}
    p  = data.get("params")  or {}
    tp = m.get("tp"); sl = m.get("sl")
    used = m.get("used")
    if used is None and (tp is not None or sl is not None):
        try: used = int(tp or 0) + int(sl or 0)
        except: used = 0
    return {
        "run_id": data.get("run_id"),
        "date": str(data.get("date") or ""),
        "ymd": str(data.get("date") or "").replace("-", ""),
        "scenario": str(data.get("scenario") or ""),
        "label": str(data.get("label") or ""),
        "wr_pct": _to_float(m.get("wr_pct")),
        "pnl": _to_float(m.get("pnl")),
        "tp": int(tp) if str(tp).isdigit() else (tp or 0),
        "sl": int(sl) if str(sl).isdigit() else (sl or 0),
        "used": int(used) if str(used).isdigit() else (used or 0),
        # normalized knobs from params
        "band_min": _to_float(p.get("band_min"), 4),
        "band_max": _to_float(p.get("band_max"), 4),
        "min_rvol_open": _to_float(p.get("min_rvol_open"), 4),
        "news_only": None if p.get("news_only") is None else bool(p.get("news_only")),
        "news_first": None if p.get("news_first") is None else bool(p.get("news_first")),
        "enforce_band": None if p.get("enforce_band") is None else bool(p.get("enforce_band")),
        "top": int(p.get("top")) if str(p.get("top")).isdigit() else p.get("top"),
        "news_min_score": _to_float(p.get("news_min_score"), 2),
        "file": fp,
        "mtime": os.path.getmtime(fp),
    }

def filter_rows(rows, scenarios=None, label_substr=None, labels_exact=None):
    out = []
    scen_set  = set(scenarios) if scenarios else None
    labels_set= set(labels_exact) if labels_exact else None
    for r in rows:
        if scen_set and r["scenario"] not in scen_set: continue
        if labels_set and r["label"] not in labels_set: continue
        if label_substr and (label_substr.lower() not in r["label"].lower()): continue
        out.append(r)
    return out

def dedupe_latest(rows):
    """Keep only most recent bundle per (date, scenario, label)."""
    best = {}
    for r in rows:
        k = (r["date"], r["scenario"], r["label"])
        if k not in best or r["mtime"] > best[k]["mtime"]:
            best[k] = r
    return list(best.values())

def write_csv(rows, path):
    if not rows: return
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = ["run_id","date","ymd","scenario","label","wr_pct","pnl","tp","sl","used",
            "band_min","band_max","min_rvol_open","news_only","news_first","enforce_band",
            "top","news_min_score","file","mtime"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in sorted(rows, key=lambda x: (x["ymd"], x["scenario"], x["label"], x["mtime"])):
            w.writerow(r)

# -------- profile & grouping --------

def pretty_profile_from_row(r):
    parts = []
    parts.append("newsOnly" if r.get("news_only") else ("newsFirst" if r.get("news_first") else "mixed"))
    if r.get("top") not in (None, "", 0):
        try: parts.append(f"Top-{int(r['top'])}")
        except: parts.append(f"Top-{r['top']}")
    def _fmt(x):
        if x is None: return "?"
        xf = _to_float(x, 2)
        return str(int(xf)) if (xf is not None and float(xf).is_integer()) else (f"{xf:.2f}" if xf is not None else "?")
    bm, bx, rv = r.get("band_min"), r.get("band_max"), r.get("min_rvol_open")
    if bm is not None or bx is not None:
        parts.append(f"band {_fmt(bm)}-{_fmt(bx)}")
    if rv is not None:
        parts.append(f"RVOL {_fmt(rv)}")
    if r.get("news_min_score") not in (None, 1, 1.0):
        parts.append(f"score >= {_fmt(r.get('news_min_score'))}")
    return " + ".join(parts)

def params_key(r):
    """Param-only grouping key (ignores label)."""
    return (
        r["scenario"],
        bool(r.get("news_only")),
        bool(r.get("news_first")),
        (int(r["top"]) if str(r.get("top")).isdigit() else r.get("top")),
        r.get("band_min"),
        r.get("band_max"),
        r.get("min_rvol_open"),
        r.get("news_min_score"),
    )

def key_to_name(k, ignore_labels=False):
    if ignore_labels:
        return f"Scenario={k[0]} | Profile"
    if len(k) == 1:
        return f"Scenario={k[0]}"
    if len(k) == 2:
        return f"Scen={k[0]} | Label={k[1]}"
    return f"Scen={k[0]} | Label={k[1]} | band=({k[2]},{k[3]}) | RVOL={k[4]}"

def aggregate(rows, mode="label", ignore_labels=False):
    """Aggregate TP/SL/PnL/Trades/Days for the grouping."""
    agg = defaultdict(lambda: {"tp":0,"sl":0,"pnl":0.0,"used":0,"days":set(),"sample":None})
    for r in rows:
        if ignore_labels:
            if mode in ("label", "label+knobs"):
                k = params_key(r)
            elif mode == "scenario":
                k = (r["scenario"],)
        else:
            if mode == "label":
                k = (r["scenario"], r["label"])
            elif mode == "scenario":
                k = (r["scenario"],)
            else:
                k = (r["scenario"], r["label"], r.get("band_min"), r.get("band_max"), r.get("min_rvol_open"))
        a = agg[k]
        a["tp"]   += r.get("tp") or 0
        a["sl"]   += r.get("sl") or 0
        a["pnl"]  += r.get("pnl") or 0.0
        a["used"] += r.get("used") or 0
        if r["date"]: a["days"].add(r["date"])
        if a["sample"] is None: a["sample"] = r
    out = []
    for k,a in agg.items():
        used = a["used"]
        wr = (a["tp"]/used*100.0) if used else 0.0
        out.append({
            "key": k,
            "wr_pct": round(wr, 2),
            "pnl": round(a["pnl"], 2),
            "tp": a["tp"],
            "sl": a["sl"],
            "used": used,
            "days": len(a["days"]),
            "sample": a["sample"],
        })
    out.sort(key=lambda x: (-x["wr_pct"], -x["pnl"], -x["used"]))
    return out

def build_profile_map(aggs):
    return {a["key"]: pretty_profile_from_row(a["sample"]) for a in aggs}

# ------------------- per-day breakdown -------------------

def per_day_breakdown(rows, ignore_labels=False):
    """Return per-day dicts; when ignoring labels, aggregate per (date,scenario,params)."""
    day_map = defaultdict(lambda: {"tp":0,"sl":0,"pnl":0.0,"used":0})
    for r in rows:
        if ignore_labels:
            k = (r["date"], r["scenario"])
        else:
            k = (r["date"], r["scenario"], r["label"])
        d = day_map[k]
        d["tp"]   += r.get("tp") or 0
        d["sl"]   += r.get("sl") or 0
        d["pnl"]  += r.get("pnl") or 0.0
        d["used"] += r.get("used") or 0
    out = []
    for k, d in sorted(day_map.items(), key=lambda kv: kv[0][0]):  # by date
        if ignore_labels:
            date, scen = k; lbl = None
        else:
            date, scen, lbl = k
        used = d["used"]
        wr = (d["tp"]/used*100.0) if used else 0.0
        out.append({
            "date": date, "scenario": scen, "label": lbl,
            "tp": d["tp"], "sl": d["sl"], "used": used,
            "wr_pct": round(wr, 2), "pnl": round(d["pnl"], 2)
        })
    return out

def print_per_day(title, days, profile_only=False, ignore_labels=False, max_rows=100):
    print("\n" + title)
    print("-" * len(title))
    # widths for per-day table
    W_DATE, W_SCEN, W_WR, W_PNL, W_TPSL, W_TR = 10, 5, 6, 9, 7, 6
    if profile_only or ignore_labels:
        print(f"{'Date':{W_DATE}} {'Scen':{W_SCEN}} {'WR%':>{W_WR}} {'PnL':>{W_PNL}} {'TP/SL':>{W_TPSL}} {'Trades':>{W_TR}}")
        for d in days[:max_rows]:
            tpsl = f"{d['tp']}/{d['sl']}"
            print(f"{d['date']:{W_DATE}} {d['scenario']:{W_SCEN}} {d['wr_pct']:>{W_WR}.2f} {d['pnl']:>{W_PNL}.2f} {tpsl:>{W_TPSL}} {d['used']:>{W_TR}}")
    else:
        W_LABEL = 40
        print(f"{'Date':{W_DATE}} {'Scen':{W_SCEN}} {'Label':{W_LABEL}} {'WR%':>{W_WR}} {'PnL':>{W_PNL}} {'TP/SL':>{W_TPSL}} {'Trades':>{W_TR}}")
        for d in days[:max_rows]:
            tpsl = f"{d['tp']}/{d['sl']}"
            print(f"{d['date']:{W_DATE}} {d['scenario']:{W_SCEN}} {(d['label'] or '')[:W_LABEL]:{W_LABEL}} {d['wr_pct']:>{W_WR}.2f} {d['pnl']:>{W_PNL}.2f} {tpsl:>{W_TPSL}} {d['used']:>{W_TR}}")

# ------------------- printing (compact widths) -------------------

def print_table(title, aggs, profiles, ignore_labels=False, profile_only=False, max_rows=10):
    print("\n" + title)
    print("-" * len(title))

    # compact widths; ALIGNMENT FIX: TP/SL width matches header exactly
    PROFILE_W = 55
    W_WR      = 6
    W_PNL     = 8
    W_TPSL    = 5   # header "TP/SL" is 5 → data must also be 5
    W_TRADES  = 6
    W_DAYS    = 4

    if profile_only:
        print(f"{'Profile':{PROFILE_W}} {'WR%':>{W_WR}} {'PnL':>{W_PNL}} {'TP/SL':>{W_TPSL}} {'Trades':>{W_TRADES}} {'Days':>{W_DAYS}}")
        for a in aggs[:max_rows]:
            prof = profiles.get(a["key"], "")
            tpsl = f"{a['tp']}/{a['sl']}"
            print(
                f"{prof[:PROFILE_W]:{PROFILE_W}} "
                f"{a['wr_pct']:>{W_WR}.2f} "
                f"{a['pnl']:>{W_PNL}.2f} "
                f"{tpsl:>{W_TPSL}} "
                f"{a['used']:>{W_TRADES}} "
                f"{a['days']:>{W_DAYS}}"
            )
    else:
        GROUP_W = 40
        PROF_W  = PROFILE_W
        print(f"{'Group':{GROUP_W}} {'Profile':{PROF_W}} {'WR%':>{W_WR}} {'PnL':>{W_PNL}} {'TP/SL':>{W_TPSL}} {'Trades':>{W_TRADES}} {'Days':>{W_DAYS}}")
        for a in aggs[:max_rows]:
            name = key_to_name(a["key"], ignore_labels=ignore_labels)
            prof = profiles.get(a["key"], "")
            tpsl = f"{a['tp']}/{a['sl']}"
            print(
                f"{name[:GROUP_W]:{GROUP_W}} {prof[:PROF_W]:{PROF_W}} "
                f"{a['wr_pct']:>{W_WR}.2f} "
                f"{a['pnl']:>{W_PNL}.2f} "
                f"{tpsl:>{W_TPSL}} "
                f"{a['used']:>{W_TRADES}} "
                f"{a['days']:>{W_DAYS}}"
            )

def write_md_summary(path, aggs_label, aggs_scen, aggs_params,
                     profiles_label, profiles_scen, profiles_params,
                     ignore_labels=False, per_day_rows=None, profile_only=False):
    """Write a markdown summary; skip redundant third table when ignoring labels; add per-day if requested."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    def add(title, aggs, profiles):
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| Group | Profile | WR% | PnL | TP/SL | Trades | Days |")
        lines.append("|---|---|---:|---:|---:|---:|---:|")
        for a in aggs[:50]:
            name = key_to_name(a["key"], ignore_labels=ignore_labels)
            prof = profiles.get(a["key"], "")
            lines.append(f"| {name} | {prof} | {a['wr_pct']:.2f} | {a['pnl']:.2f} | {a['tp']}/{a['sl']} | {a['used']} | {a['days']} |")
        lines.append("")
    add("Top by Profile" if ignore_labels else "Top by Label", aggs_label, profiles_label)
    add("Top by Scenario", aggs_scen, profiles_scen)
    if not ignore_labels:
        add("Top by Label+Knobs", aggs_params, profiles_params)
    if per_day_rows:
        lines.append("## Per-day breakdown")
        lines.append("")
        if profile_only or ignore_labels:
            lines.append("| Date | Scenario | WR% | PnL | TP/SL | Trades |")
            lines.append("|---|---|---:|---:|---:|---:|")
            for d in per_day_rows:
                lines.append(f"| {d['date']} | {d['scenario']} | {d['wr_pct']:.2f} | {d['pnl']:.2f} | {d['tp']}/{d['sl']} | {d['used']} |")
        else:
            lines.append("| Date | Scenario | Label | WR% | PnL | TP/SL | Trades |")
            lines.append("|---|---|---|---:|---:|---:|---:|")
            for d in per_day_rows:
                lines.append(f"| {d['date']} | {d['scenario']} | {d['label'] or ''} | {d['wr_pct']:.2f} | {d['pnl']:.2f} | {d['tp']}/{d['sl']} | {d['used']} |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")

# ----------------------------- main -----------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dates", help="Comma-separated YYYY-MM-DD list (default: scan all)")
    ap.add_argument("--scenario", help="(Deprecated) single scenario filter; prefer --scenarios")
    ap.add_argument("--scenarios", help="Comma-separated scenarios, e.g., B,E")
    ap.add_argument("--label", help="Substring filter on label")
    ap.add_argument("--labels", help="Comma-separated exact labels")
    ap.add_argument("--dedupe-latest", action="store_true", help="Keep only most recent bundle per (date,scenario,label)")
    ap.add_argument("--max-rows", type=int, default=10, help="Rows to show per console table")
    ap.add_argument("--min-trades", type=int, default=0, help="Hide groups with Trades < N")
    ap.add_argument("--profile-only", action="store_true", help="Console: show Profile only (hide label text)")
    ap.add_argument("--ignore-labels", action="store_true", help="Group purely by parameters (Profile), ignoring labels")
    ap.add_argument("--per-day", action="store_true", help="Print a per-day breakdown table")
    args = ap.parse_args()

    dates = parse_list(args.dates)
    scenarios = parse_list(args.scenarios) or ([args.scenario] if args.scenario else None)
    labels_exact = parse_list(args.labels)

    ignore_labels = args.ignore_labels or args.profile_only

    files = find_files(dates)
    if not files:
        print("No comparison JSONs found.")
        sys.exit(0)

    rows = []
    for fp in files:
        data = load_json_safe(fp)
        if not data: continue
        rows.append(row_from_bundle(fp, data))

    if args.dedupe_latest:
        rows = dedupe_latest(rows)

    rows = filter_rows(rows, scenarios=scenarios, label_substr=args.label, labels_exact=labels_exact)
    if not rows:
        print("No rows after filters.")
        sys.exit(0)

    if args.min_trades and args.min_trades > 0:
        rows = [r for r in rows if (r.get("used") or 0) >= args.min_trades]
        if not rows:
            print(f"No rows with Trades >= {args.min_trades}.")
            sys.exit(0)

    # Write flat index for audit
    write_csv(rows, OUT / "compare_index.csv")

    # Aggregations
    ag_label  = aggregate(rows, mode="label",        ignore_labels=ignore_labels)
    ag_scen   = aggregate(rows, mode="scenario",     ignore_labels=False)
    ag_params = aggregate(rows, mode="label+knobs",  ignore_labels=ignore_labels)

    # Profiles
    profiles_label  = build_profile_map(ag_label)
    profiles_scen   = build_profile_map(ag_scen)
    profiles_params = build_profile_map(ag_params)

    # Console tables
    print_table("Top by Profile" if ignore_labels else "Top Groups by Label (WR% first)",
                ag_label, profiles_label, ignore_labels=ignore_labels,
                profile_only=args.profile_only, max_rows=args.max_rows)
    print_table("Top Groups by Scenario (WR% first)",
                ag_scen,  profiles_scen,  ignore_labels=False,
                profile_only=args.profile_only, max_rows=args.max_rows)
    if not ignore_labels:
        print_table("Top Groups by Label+Knobs (WR% first)",
                    ag_params, profiles_params, ignore_labels=ignore_labels,
                    profile_only=args.profile_only, max_rows=args.max_rows)

    # Per-day breakdown (optional)
    per_day_rows = None
    if args.per_day:
        per_day_rows = per_day_breakdown(rows, ignore_labels=ignore_labels)
        print_per_day("Per-day breakdown", per_day_rows,
                      profile_only=args.profile_only, ignore_labels=ignore_labels, max_rows=100)

    # Markdown summary
    write_md_summary(OUT / "compare_summary.md",
                     ag_label, ag_scen, ag_params,
                     profiles_label, profiles_scen, profiles_params,
                     ignore_labels=ignore_labels, per_day_rows=per_day_rows, profile_only=args.profile_only)

    # Recommendation
    best = (ag_label[0] if ignore_labels else (ag_params[0] if ag_params else None))
    best_prof = (profiles_label.get(best["key"], "") if best and ignore_labels
                 else profiles_params.get(best["key"], "") if best else "")
    if best:
        print(f"\n[RECOMMEND] Profile → {best_prof}  |  WR={best['wr_pct']:.2f}%  Trades={best['used']}  PnL={best['pnl']:.2f}  over {best['days']} day(s)")

if __name__ == "__main__":
    main()