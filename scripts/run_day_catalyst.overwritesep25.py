import argparse, subprocess, sys, os, csv, re, json, textwrap
from pathlib import Path
from collections import defaultdict

# --- ensure repo/src is importable for `midas_v2` ---
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
# ----------------------------------------------------

# Validated config models (Pydantic v2)
from pathlib import Path as _PathForConfig
from midas_v2.config_models import ScannerConfig, ScenariosConfig, merge_scanner

# ─────────────────────────────── Junk-class detection ───────────────────────────────
CLASS_CODE_EXCLUDE = {"W", "U", "R", "P"}  # NASDAQ 5th letter = warrants/units/rights/preferred

def is_junky_symbol(sym: str) -> bool:
    s = sym.upper()
    if len(s) == 5 and s[-1] in CLASS_CODE_EXCLUDE:
        return True
    if "." in s:
        tail = s.split(".")[-1]
        if tail.isalpha() and len(tail) == 1:  # BRK.A
            return True
    if "-" in s:
        tail = s.split("-")[-1]
        if tail.isalpha() and len(tail) == 1:  # XYZ-A
            return True
    if len(s) >= 2 and s[-2] == "P" and s[-1].isalpha():  # PWpA
        return True
    return False

# ─────────────────────────────── Hybrid file loader ────────────────────────────────
def load_hybrid_list(path: Path):
    """TXT: 1 symbol/line; CSV: columns 'symbol' or 'ticker', optional 'gap_pct'."""
    syms = []
    with path.open(encoding="utf-8") as f:
        head = f.readline().strip()
        f.seek(0)
        if "," in head:  # CSV mode
            reader = csv.DictReader(f)
            for row in reader:
                sym = (row.get("symbol") or row.get("ticker") or "").strip().upper()
                graw = row.get("gap_pct")
                try:
                    g = float(str(graw).replace("%","")) if graw not in (None,"") else None
                except:
                    g = None
                if sym:
                    syms.append((sym, g))
        else:  # TXT mode
            for line in f:
                sym = line.strip().upper()
                if sym:
                    syms.append((sym, None))
    return syms

def top_by_gap(pairs, n):
    with_gap    = [p for p in pairs if isinstance(p[1], (int, float))]
    without_gap = [p for p in pairs if p[1] is None]
    with_gap.sort(key=lambda x: x[1], reverse=True)
    return (with_gap + without_gap)[:n]

# ─────────────────────────────── Gap% enrichment ───────────────────────────────────
TG_HEADER_RX = re.compile(r"^\s*SYMBOL\s+GAP%\s+PRICE", re.IGNORECASE)
TG_ROW_RX    = re.compile(r"^\s*([A-Za-z0-9.\-pP]{1,10})\s+(-?\d+(?:\.\d+)?)\s+")

def parse_topgappers_table(text: str):
    gaps = {}
    for line in text.splitlines():
        if TG_HEADER_RX.match(line):
            continue
        m = TG_ROW_RX.match(line)
        if m:
            sym = m.group(1).upper()
            gap = float(m.group(2))
            gaps[sym] = gap
    return gaps

def load_gap_map_from_files(date_str: str):
    gaps = {}
    raw_dir = Path("data/raw")
    csv_path = raw_dir / f"universe_topgappers_{date_str}.csv"
    txt_path = raw_dir / f"universe_topgappers_{date_str}.txt"
    if csv_path.exists():
        with csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sym = (row.get("symbol") or row.get("ticker") or "").strip().upper()
                if not sym: continue
                g = row.get("gap_pct")
                try:
                    gaps[sym] = float(str(g).replace("%",""))
                except:
                    pass
        if gaps:
            return gaps
    if txt_path.exists():
        txt = txt_path.read_text(encoding="utf-8", errors="ignore")
        p = parse_topgappers_table(txt)
        if p:
            return p
    return {}

def load_gap_map_from_topgappers_stdout(date_str: str, env: dict):
    try:
        cmd = [sys.executable, "scripts/topgappers.py", "--date", date_str]
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        return parse_topgappers_table(proc.stdout or "")
    except Exception:
        return {}

def enrich_gaps(pairs, date_str: str, env: dict):
    """Prefer hybrid CSV gaps > data/raw > topgappers stdout."""
    gap_map = {s: g for (s,g) in pairs if isinstance(g,(int,float))}
    file_gaps = load_gap_map_from_files(date_str)
    for (s,g) in pairs:
        if s not in gap_map and s in file_gaps:
            gap_map[s] = file_gaps[s]
    missing = [s for (s,_) in pairs if s not in gap_map]
    if missing:
        tg = load_gap_map_from_topgappers_stdout(date_str, env)
        for s in missing:
            if s in tg:
                gap_map[s] = tg[s]
    new_pairs = [(s, gap_map.get(s)) for (s,_) in pairs]
    return new_pairs, gap_map

# ───────────────────── Validated scanner (JSON is source of truth) ─────────────────
def load_validated_scanner_for_scenario(scenario_name: str | None):
    """Load global scanner.json and merge with scenarios.json[scenario].scanner if present."""
    scanner_global = ScannerConfig.model_validate_json(
        (_PathForConfig("config/scanner.json")).read_text(encoding="utf-8")
    )
    scenario_obj = None
    scn_path = _PathForConfig("config/scenarios.json")
    if scn_path.exists():
        scenarios_map = ScenariosConfig.model_validate_json(
            scn_path.read_text(encoding="utf-8")
        ).root
        if scenario_name:
            scenario_obj = scenarios_map.get(scenario_name)
    return merge_scanner(scanner_global, scenario_obj)

# ───────────────────────────── Catalyst news loader (BOM/quotes tolerant) ──────────
def load_news_map(date_str: str, override_path: str | None, min_score: float):
    """
    Loads canonical news CSV (symbol,score[,headline]).
    Tolerates BOM and quoted headers. Filters to score >= min_score.
    Search order if override not provided:
      1) data/catalyst/catalyst_news_YYYY-MM-DD.csv
      2) out/YYYYMMDD/catalyst/catalyst_news_YYYY-MM-DD.csv
    """
    def _norm(s: str) -> str:
        return (s or "").replace("\ufeff","").strip().strip('"').strip("'").lower()

    ymd = date_str.replace("-", "")
    candidates = []
    if override_path:
        candidates.append(Path(override_path))
    candidates += [
        Path(f"data/catalyst/catalyst_news_{date_str}.csv"),
        Path(f"out/{ymd}/catalyst/catalyst_news_{date_str}.csv"),
    ]

    news, used = {}, None
    for p in candidates:
        if not p.exists():
            continue
        used = p
        with p.open(encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                continue
            cols = {_norm(c): c for c in reader.fieldnames}
            if "symbol" not in cols or "score" not in cols:
                continue
            sym_col   = cols["symbol"]
            score_col = cols["score"]
            head_col  = cols.get("headline")
            for row in reader:
                s = (row.get(sym_col,"") or "").strip().upper()
                if not s:
                    continue
                try:
                    scr = float(str(row.get(score_col,"")).strip())
                except:
                    continue
                if scr >= float(min_score):
                    head = (row.get(head_col,"") if head_col else "").strip()
                    news[s] = {"score": int(scr) if float(scr).is_integer() else scr, "headline": head}
        break
    return news, (used or candidates[0])

# ───────────────────────────── Results parsing / summaries ─────────────────────────
def compute_summary(results_csv: Path, scenario: str) -> str:
    tp = sl = 0
    pnl_sum = 0.0
    outcome_key = pnl_key = None
    with results_csv.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames:
            for k in reader.fieldnames:
                lk = k.lower()
                if outcome_key is None and lk in ("outcome","result","status"): outcome_key = k
                if pnl_key    is None and lk in ("pnl","p&l","profit"): pnl_key = k
        if outcome_key:
            for row in reader:
                v = (row.get(outcome_key,"") or "").strip().upper()
                if v == "TP": tp += 1
                elif v == "SL": sl += 1
                if pnl_key:
                    try: pnl_sum += float(row.get(pnl_key, 0) or 0)
                    except: pass
        else:
            f.seek(0)
            rows = list(csv.reader(f))
            for r in rows[1:]:
                val = (r[1] if len(r) > 1 else "").strip().upper()
                if val == "TP": tp += 1
                elif val == "SL": sl += 1
                try:
                    pnl_sum += float(r[2]) if len(r) > 2 else 0.0
                except: pass
    total = tp + sl
    wr = (tp / total * 100.0) if total else 0.0
    return f"{scenario}: TP={tp} SL={sl} Win%={wr:.2f} PnL={pnl_sum:.2f}"

def per_symbol_breakdown(results_csv: Path):
    counts = defaultdict(int); wins = defaultdict(int); losses = defaultdict(int); pnl = defaultdict(float)
    with results_csv.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fields = [c.lower() for c in (reader.fieldnames or [])]
        sym_col = next((reader.fieldnames[i] for i,k in enumerate(fields) if k in ("symbol","ticker")), reader.fieldnames[0] if reader.fieldnames else 0)
        out_col = next((reader.fieldnames[i] for i,k in enumerate(fields) if k in ("outcome","result","status")), (reader.fieldnames+[""])[1] if reader.fieldnames else 1)
        pnl_col = next((reader.fieldnames[i] for i,k in enumerate(fields) if k in ("pnl","p&l","profit")), None)
        for row in reader:
            sym = (row.get(sym_col,"") if isinstance(sym_col,str) else (row.get(reader.fieldnames[sym_col],"") if reader.fieldnames else "")).strip().upper()
            if not sym: continue
            counts[sym] += 1
            v = (row.get(out_col,"") if isinstance(out_col,str) else (row.get(reader.fieldnames[out_col],"") if reader.fieldnames else "")).strip().upper()
            if v == "TP": wins[sym] += 1
            elif v == "SL": losses[sym] += 1
            if pnl_col:
                try: pnl[sym] += float(row.get(pnl_col,0) or 0)
                except: pass
    rows = []
    for sym in sorted(counts, key=lambda s: (-wins[s], losses[s], s)):
        rows.append({"symbol": sym, "trades": counts[sym], "tp": wins[sym], "sl": losses[sym], "pnl_sum": round(pnl[sym],2)})
    totals = {"trades": sum(counts.values()), "tp": sum(wins.values()), "sl": sum(losses.values()), "pnl_sum": round(sum(pnl.values()), 2)}
    return rows, totals

# NEW: run-summary printer/saver
def print_and_save_run_summary(out_dir: Path, *, date, scenario, news_first, score_gate, top_n,
                               min_gap, max_gap, enforce_band, min_rvol_open, rvol_open_minutes,
                               used_count, tp, sl, wr, pnl):
    print("\n[RUN SUMMARY]")
    band_str = ""
    if min_gap is not None and max_gap is not None:
        band_str = f"{min_gap:.0f}% / {max_gap:.0f}%"
    elif min_gap is not None:
        band_str = f"≥ {min_gap:.0f}%"
    elif max_gap is not None:
        band_str = f"≤ {max_gap:.0f}%"
    else:
        band_str = "-"

    rvol_str = "None"
    if min_rvol_open is not None:
        if rvol_open_minutes is not None:
            rvol_str = f"≥ {min_rvol_open:g} × / {int(rvol_open_minutes)}m"
        else:
            rvol_str = f"≥ {min_rvol_open:g} ×"

    # console table
    header = ("Date      | Scen | News-first | Score | Top | Band      | Enforce | OpenRVOL       | Used |   WR   | TP/SL |   PnL  ")
    print(header)
    print("-"*len(header))
    row = (f"{date} | {scenario:<4}| {'Yes' if news_first else 'No ':<10} | ≥{score_gate:g}  | "
           f"{(top_n if top_n else 0):>3} | {band_str:<9} | {'Yes' if enforce_band else 'No ':<7} | "
           f"{rvol_str:<13} | {used_count:>4} | {wr:>6.2f}% | {tp:>2}/{sl:<2} | {pnl:>6.2f}")
    print(row)

    # save csv + txt
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "run_summary.txt").write_text(header + "\n" + "-"*len(header) + "\n" + row + "\n", encoding="utf-8")
    with (out_dir / "run_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date","scenario","news_first","score_gate","top_n","band_min","band_max","enforce_band",
                    "min_rvol_open","rvol_open_minutes","used_symbols","wr","tp","sl","pnl"])
        w.writerow([date, scenario, "yes" if news_first else "no", score_gate, top_n or 0,
                    (f"{min_gap:.2f}" if min_gap is not None else ""), (f"{max_gap:.2f}" if max_gap is not None else ""),
                    "yes" if enforce_band else "no",
                    (f"{min_rvol_open:g}" if min_rvol_open is not None else ""),
                    (int(rvol_open_minutes) if rvol_open_minutes is not None else ""),
                    used_count, f"{wr:.2f}", tp, sl, f"{pnl:.2f}"])

def save_trades_breakdown(out_dir: Path, rows, totals, gap_map, preflight_band, news_map, news_path):
    txt = out_dir / "trades_by_symbol.txt"
    csvp = out_dir / "trades_by_symbol.csv"
    min_gap, max_gap = preflight_band

    header_cols = ["symbol","included_by","news_score","news_headline","gap_pct","in_band","type","traded","trades","tp","sl","pnl_sum"]

    def inband(gp):
        if not isinstance(gp,(int,float)): return ""
        ok = True
        if min_gap is not None and gp < min_gap: ok = False
        if max_gap is not None and gp > max_gap: ok = False
        return "yes" if ok else "no"

    def type_of_gap(gp):
        if not isinstance(gp,(int,float)): return ""
        if max_gap is not None and gp > max_gap:
            return "rocket"
        # standard = in-band
        if (min_gap is None or gp >= min_gap) and (max_gap is None or gp <= max_gap):
            return "standard"
        return ""

    # TXT
    lines = [",".join(header_cols)]
    for r in rows:
        sym = r["symbol"]
        gp  = gap_map.get(sym)
        n   = news_map.get(sym)
        included_by = "news" if n else "gap"
        news_score  = (n.get("score") if n and n.get("score") is not None else 0)
        head        = "" if not n else (n.get("headline","") or "").replace('"', "'")
        gap_str     = "" if gp is None else f"{gp:.2f}"
        traded      = "yes" if r["trades"] > 0 else "no"
        type_str    = type_of_gap(gp)
        lines.append(f"{sym},{included_by},{news_score},\"{head}\",{gap_str},{inband(gp)},{type_str},{traded},{r['trades']},{r['tp']},{r['sl']},{r['pnl_sum']}")
    lines.append(f"TOTALS,,,,,,,{totals['trades']},{totals['tp']},{totals['sl']},{totals['pnl_sum']}")
    lines.append(f"# news_source: {news_path}")
    txt.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # CSV
    with csvp.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header_cols)
        for r in rows:
            sym = r["symbol"]; gp = gap_map.get(sym)
            n   = news_map.get(sym)
            included_by = "news" if n else "gap"
            news_score  = (n.get("score") if n and n.get("score") is not None else 0)
            head        = "" if not n else n.get("headline","")
            gap_str     = "" if gp is None else f"{gp:.2f}"
            traded      = "yes" if r["trades"] > 0 else "no"
            type_str    = type_of_gap(gp)
            w.writerow([sym, included_by, news_score, head, gap_str, inband(gp), type_str, traded, r["trades"], r["tp"], r["sl"], r["pnl_sum"]])
        w.writerow(["TOTALS","","","","","", "", totals["trades"], totals["tp"], totals["sl"], totals["pnl_sum"]])
        w.writerow(["# news_source", str(news_path)])

# ───────────────────────────────────────── Main ────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--scenario", required=True, help="Scenario ID (e.g., B, D, E, B_widegap)")
    ap.add_argument("--universe", required=True, help="Path to hybrid universe file (txt or csv)")
    ap.add_argument("--top", type=int, help="Restrict to Top-N by gap_pct")
    ap.add_argument("--no-exclude", action="store_true", help="Disable default junk-class exclusion")
    ap.add_argument("--extra-exclude", help="Additional regex to exclude (applied after default)")
    ap.add_argument("--catalyst", help="Path to catalyst news CSV")
    ap.add_argument("--news-first", action="store_true", help="Order by news(score desc) then gap; fill remainder with gap-only")
    ap.add_argument("--require-news", action="store_true", help="Keep only symbols that appear in the news CSV (intersection)")
    ap.add_argument("--news-min-score", type=float, default=1.0, help="Minimum score to count a symbol as 'news' (default: 1.0)")
    # Run-only overrides via CLI (JSON will be applied first; CLI can still override)
    ap.add_argument("--enforce-band", action="store_true", help="Drop out-of-band symbols per scanner gap band")
    ap.add_argument("--macd-rise-bars", type=int, dest="macd_rise_bars", help="Override MACD histogram rise bars (e.g., 2)")
    ap.add_argument("--gate-minutes", type=int, dest="gate_minutes", help="Override gate minutes (e.g., 5)")
    ap.add_argument("--min-rvol-open", type=float, dest="min_rvol_open", help="Override opening RVOL gate (e.g., 1.5)")
    args = ap.parse_args()

    uni_path = Path(args.universe).resolve()
    if not uni_path.exists():
        print(f"[ERROR] Universe file not found: {uni_path}"); sys.exit(2)

    ymd = args.date.replace("-", "")
    out_dir = Path(f"out/{ymd}/{args.scenario}_hybrid").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # === Validated scanner config (JSON is source of truth) ===
    scanner = load_validated_scanner_for_scenario(args.scenario)
    min_gap = scanner.min_gap_pct
    max_gap = scanner.max_gap_pct
    # === End validated scanner ===

    # === Scenario params (JSON) → ENV (JSON first; CLI may override) ===
    scenario_params = {}
    scn_path = Path("config/scenarios.json")
    if scn_path.exists():
        try:
            scenarios_map = ScenariosConfig.model_validate_json(scn_path.read_text(encoding="utf-8")).root
            scn = scenarios_map.get(args.scenario)
            if scn and isinstance(scn.params, dict):
                scenario_params = scn.params
        except Exception:
            scenario_params = {}

    # Enforce-band setting (JSON prevails; CLI can force on)
    enforce_band = bool(scenario_params.get("enforce_band", False)) or bool(args.enforce_band)

    # Export JSON params to ENV (then apply CLI overrides if given)
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"

    # JSON -> ENV
    if scenario_params.get("macd_rise_bars") is not None:
        env["MIDAS_MACD_RISE_BARS"] = str(scenario_params["macd_rise_bars"])
        print(f"[CFG] MIDAS_MACD_RISE_BARS={env['MIDAS_MACD_RISE_BARS']} (from JSON)")
    elif scenario_params.get("rise_bars") is not None:  # alias
        env["MIDAS_MACD_RISE_BARS"] = str(scenario_params["rise_bars"])
        print(f"[CFG] MIDAS_MACD_RISE_BARS={env['MIDAS_MACD_RISE_BARS']} (from JSON rise_bars)")

    if scenario_params.get("gate_minutes") is not None:
        env["MIDAS_GATE_MINUTES"] = str(scenario_params["gate_minutes"])
        print(f"[CFG] MIDAS_GATE_MINUTES={env['MIDAS_GATE_MINUTES']} (from JSON)")

    if scenario_params.get("min_rvol_open") is not None:
        env["MIDAS_MIN_RVOL_OPEN"] = str(scenario_params["min_rvol_open"])
        print(f"[CFG] MIDAS_MIN_RVOL_OPEN={env['MIDAS_MIN_RVOL_OPEN']} (from JSON)")

    if scenario_params.get("rvol_open_minutes") is not None:
        env["MIDAS_RVOL_OPEN_MINUTES"] = str(scenario_params["rvol_open_minutes"])
        print(f"[CFG] MIDAS_RVOL_OPEN_MINUTES={env['MIDAS_RVOL_OPEN_MINUTES']} (from JSON)")

    # CLI overrides (explicit use)
    if args.macd_rise_bars is not None:
        env["MIDAS_MACD_RISE_BARS"] = str(args.macd_rise_bars)
        print(f"[OVERRIDE] MIDAS_MACD_RISE_BARS={env['MIDAS_MACD_RISE_BARS']}")
    if args.gate_minutes is not None:
        env["MIDAS_GATE_MINUTES"] = str(args.gate_minutes)
        print(f"[OVERRIDE] MIDAS_GATE_MINUTES={env['MIDAS_GATE_MINUTES']}")
    if args.min_rvol_open is not None:
        env["MIDAS_MIN_RVOL_OPEN"] = str(args.min_rvol_open)
        print(f"[OVERRIDE] MIDAS_MIN_RVOL_OPEN={env['MIDAS_MIN_RVOL_OPEN']}")

    # 1) Load hybrid
    pairs = load_hybrid_list(uni_path)

    # 2) Default junk-class exclude
    if not args.no_exclude:
        before = len(pairs)
        pairs = [(s,g) for (s,g) in pairs if not is_junky_symbol(s)]
        removed = before - len(pairs)
        if removed:
            print(f"[FILTER] Removed {removed} junk-class symbol(s)")

    # 3) Optional extra exclude
    if args.extra_exclude:
        rx = re.compile(args.extra_exclude, re.IGNORECASE)
        before = len(pairs)
        pairs = [(s,g) for (s,g) in pairs if not rx.search(s)]
        if len(pairs) != before:
            print(f"[FILTER] Extra exclude removed {before-len(pairs)} symbol(s) by regex: {args.extra_exclude}")

    # 4) Enrich gaps ALWAYS (for display and optional top-N)
    pairs, gap_map = enrich_gaps(pairs, args.date, env)

    # 5) Load catalyst news with min-score filter (tolerant headers)
    news_map, news_path = load_news_map(args.date, args.catalyst, args.news_min_score)

    # 6) Apply hybrid precedence and Top-N
    if args.require_news:
        pairs = [(s,g) for (s,g) in pairs if s in news_map]
        print(f"[NEWS] require-news active -> using {len(pairs)} symbols from news∩gap (min_score={args.news_min_score})")

    if args.news_first:
        def rank_key(pg):  # pg = (symbol, gap)
            s, g = pg
            is_news = 1 if s in news_map else 0
            score = news_map.get(s, {}).get("score") or 0
            gapv  = g or gap_map.get(s) or 0.0
            return (is_news, score, gapv)
        pairs = sorted(pairs, key=rank_key, reverse=True)
        if args.top:
            pairs = pairs[:args.top]
        print(f"[NEWS] news-first ordering applied (news>=min_score {args.news_min_score} > score > gap)")
    elif args.top:
        pairs = top_by_gap(pairs, args.top)

    # 7) Enforce gap band (after ordering/Top-N), if enabled
    def _in_band_val(g):
        if not isinstance(g, (int, float)):
            return False
        if min_gap is not None and g < min_gap:
            return False
        if max_gap is not None and g > max_gap:
            return False
        return True

    if enforce_band and (min_gap is not None or max_gap is not None):
        before = len(pairs)
        pairs = [(s, g) for (s, g) in pairs if _in_band_val(g)]
        removed = before - len(pairs)
        print(f"[FILTER] enforce-band removed {removed} out-of-band symbol(s)")

    # 8) Persist used universe
    used_syms = [p[0] for p in pairs]
    used_uni_txt = out_dir / "universe_used.txt"
    used_uni_txt.write_text("\n".join(used_syms) + "\n", encoding="utf-8")

    print(f"[CATALYST-DAY] date={args.date} scenario={args.scenario} universe={uni_path}")
    print(f"[OUT] {out_dir}")
    print(f"[UNIVERSE] {len(used_syms)} symbols -> {used_uni_txt}")
    if not used_syms:
        sys.exit("[ERROR] No symbols after filtering; aborting.")
    else:
        print("[UNIVERSE] " + ", ".join(used_syms))

    # 9) Catalyst news announce + counts
    picked = [s for s in used_syms if s in news_map]
    not_picked = [s for s in used_syms if s not in news_map]
    if picked:
        print("[NEWS] Selected from catalyst (source:", news_path, f", min_score={args.news_min_score})")
        for s in picked:
            n = news_map.get(s, {})
            scr = n.get("score")
            head = textwrap.shorten((n.get("headline","") or ""), width=96, placeholder="…")
            print(f"  - {s}: score={scr if scr is not None else ''}  {head}")
    if not_picked:
        print("[NEWS] Gap-only (no news tag): " + ", ".join(not_picked))
    print(f"[NEWS] counts: picked_from_news={len(picked)}  gap_only={len(not_picked)}  total_used={len(used_syms)}")

    # 10) Preflight gap band + messages (from validated JSON)
    if min_gap is not None or max_gap is not None:
        print("[PREFLIGHT] Gap band (scanner.json/scenarios.json):",
              f"min={min_gap}" if min_gap is not None else "min=None",
              f"max={max_gap}" if max_gap is not None else "max=None")
        for s in used_syms:
            gp = gap_map.get(s)
            if isinstance(gp,(int,float)):
                if min_gap is not None and gp < min_gap:
                    print(f"[SKIP-BAND] {s}: gap {gp:.2f}% < {min_gap:.2f}%")
                if max_gap is not None and gp > max_gap:
                    print(f"[SKIP-BAND] {s}: gap {gp:.2f}% > {max_gap:.2f}%")

    # 11) Temp universe file for CLI
    tmp_uni = out_dir / "universe_tmp.txt"
    tmp_uni.write_text("\n".join(used_syms) + "\n", encoding="utf-8")

    # 12) Run backtest directly (no day-runner)
    bt_cmd = [
        sys.executable, "-m", "midas_v2.cli", "backtest",
        "--date", args.date, "--scenario", args.scenario,
        "--universe", str(tmp_uni), "--out", str(out_dir),
    ]
    subprocess.run(bt_cmd, env=env, check=True)

    # 13) Normalize filename and summarize
    default_csv = out_dir / f"results_{args.date}.csv"
    hybrid_csv  = out_dir / f"results_hybrid_{args.date}.csv"
    if default_csv.exists():
        default_csv.replace(hybrid_csv)
    if not hybrid_csv.exists():
        return print("[ERROR] No results CSV found to compute summary.")

    # Existing one-line summary (kept)
    line = compute_summary(hybrid_csv, args.scenario)
    print(line)
    (out_dir / f"summary_hybrid_{args.date}.txt").write_text(line + "\n", encoding="utf-8")
    print(f"[OK] Hybrid summary saved -> {out_dir / f'summary_hybrid_{args.date}.txt'}")

    # 14) Per-symbol totals (for run summary table), then print the table
    rows, totals = per_symbol_breakdown(hybrid_csv)
    tp = totals["tp"]; sl = totals["sl"]; pnl = totals["pnl_sum"]
    denom = (tp + sl)
    wr = round((tp / denom * 100.0), 2) if denom else 0.0

    min_rvol_open = scenario_params.get("min_rvol_open")
    rvol_open_minutes = scenario_params.get("rvol_open_minutes")

    print_and_save_run_summary(
        out_dir,
        date=args.date,
        scenario=args.scenario,
        news_first=bool(args.news_first),
        score_gate=float(args.news_min_score),
        top_n=int(args.top) if args.top else None,
        min_gap=min_gap, max_gap=max_gap,
        enforce_band=bool(enforce_band),
        min_rvol_open=min_rvol_open,
        rvol_open_minutes=rvol_open_minutes,
        used_count=len(used_syms),
        tp=tp, sl=sl, wr=wr, pnl=pnl
    )

    # 15) Per-symbol (with inclusion + news_score + in_band + type)
    rows_by_sym = {r["symbol"]: r for r in rows}

    print("\n[PER-SYMBOL]")

    # Definition line
    defs = []
    if min_gap is not None and max_gap is not None:
        defs.append(f"in_band=yes if {min_gap:.2f}% ≤ gap ≤ {max_gap:.2f}% (inclusive)")
    elif min_gap is not None:
        defs.append(f"in_band=yes if gap ≥ {min_gap:.2f}%")
    elif max_gap is not None:
        defs.append(f"in_band=yes if gap ≤ {max_gap:.2f}%")

    type_defs = ["type=standard if in_band"]
    if max_gap is not None:
        type_defs.append(f"type=rocket if gap > {max_gap:.2f}%")

    print("[DEFS] " + " ; ".join(defs + type_defs))

    print("symbol   included_by  news_score  gap%    in_band  type     traded  trades  TP  SL    PnL   headline")

    def classify_type(gp):
        if not isinstance(gp,(int,float)): return ""
        if max_gap is not None and gp > max_gap: return "rocket"
        if (min_gap is None or gp >= min_gap) and (max_gap is None or gp <= max_gap): return "standard"
        return ""

    for s in used_syms:
        gp = gap_map.get(s)
        gap_str = "" if gp is None else f"{gp:.2f}"
        in_band = ""
        if isinstance(gp,(int,float)) and (min_gap is not None or max_gap is not None):
            ok = True
            if min_gap is not None and gp < min_gap: ok = False
            if max_gap is not None and gp > max_gap: ok = False
            in_band = "yes" if ok else "no"
        r = rows_by_sym.get(s, {"trades":0,"tp":0,"sl":0,"pnl_sum":0.0})
        traded = "yes" if r["trades"]>0 else "no"
        n = news_map.get(s)
        included_by = "news" if n else "gap"
        news_score  = (n.get("score") if n and n.get("score") is not None else 0)
        head = "" if not n else textwrap.shorten(n.get("headline",""), width=60, placeholder="…")
        type_str = classify_type(gp)
        print(f"{s:6}  {included_by:10}  {news_score:10}  {gap_str:>6}   {in_band:>6}   {type_str:7}  {traded:>6}   {r['trades']:6}  {r['tp']:2}  {r['sl']:2}  {r['pnl_sum']:>7.2f}  {head}")

    save_trades_breakdown(out_dir, rows, totals, gap_map, (min_gap, max_gap), news_map, news_path)

if __name__ == "__main__":
    main()