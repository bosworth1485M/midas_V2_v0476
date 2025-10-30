#!/usr/bin/env python3
"""
Catalyst one-command runner (SAFE)

Pipeline:
1) Top gappers -> data/samples/universe_sample.txt
2) Enrich catalysts (denylist/A-only capable) -> out/<YYYYMMDD>/catalyst/{scores,news}.csv
3) Sanitize scores CSV (negatives -> score=0)
4) Pick Top-N (A-only by default; optional --allow-b-fill)
5) Fetch minutes (today)
6) Backtest to out/<YYYYMMDD>/<SCENARIO>_catalyst
7) Summarize (prints + authoritative one-pager)

Also: forwards RVOL flags (--min-rvol-open, --rvol-open-minutes) to CLI,
and writes out/<YYYYMMDD>/_last_cfg.json so the summarizer footer shows run knobs.
"""

import os, re, csv, io, sys, argparse, pathlib, subprocess, json

# -------------------- utilities --------------------

def sh(args, env=None):
    print("[CMD]", " ".join(args))
    return subprocess.run(args, check=False, env=env)

def sh_capture(args, env=None):
    print("[CMD]", " ".join(args))
    return subprocess.run(args, check=False, env=env, capture_output=True, text=True)

def ensure_dir(p: pathlib.Path):
    p.mkdir(parents=True, exist_ok=True)

def _read_csv_robust(path: pathlib.Path):
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if "\r\n" in text:
        text = text.replace("\r\n", "\n")
    sample = text[:4096]

    # Try sniffer
    delim = ","
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delim = dialect.delimiter
    except Exception:
        header_line = sample.split("\n", 1)[0] if sample else ""
        counts = {d: header_line.count(d) for d in [",",";","\t","|"]}
        delim = max(counts, key=counts.get) if counts and max(counts.values()) > 0 else ","

    f = io.StringIO(text)
    r = csv.DictReader(f, delimiter=delim)
    headers = [(h or "").strip().lower() for h in (r.fieldnames or [])]

    expected_any = {"symbol","ticker","score","catalyst_score","title","headline","grade","best_headline","desc","news_title"}
    if len(headers) <= 1 or not any(h in expected_any for h in headers):
        f2 = io.StringIO(text)
        r2 = csv.DictReader(f2, delimiter=",")
        headers2 = [(h or "").strip().lower() for h in (r2.fieldnames or [])]
        if any(h in expected_any for h in headers2) and len(headers2) >= len(headers):
            r = r2
            headers = headers2
            delim = ","

    rows = []
    for row0 in r:
        if row0 is None:
            continue
        row = {}
        for k, v in row0.items():
            kk = (k or "").strip().lower()
            vv = (v or "").strip()
            row[kk] = vv
        rows.append(row)

    return rows, delim, headers

# -------------------- sentiment & magnitude helpers --------------------

NEG_KEYS = (
    "revenue falls","falls","fall","declines","decline","drops","drop","misses","miss",
    "cuts guidance","cut guidance","cut outlook","lowered guidance","warns","warning",
    "plunge","plunges","downgrade","estimate cut","loss widens","loss narrows","net loss"
)
POS_KEYS = (
    "beats","beat","tops","top","surges","soars","soar","spikes","raises guidance",
    "raise guidance","lift guidance","lifts guidance","upgrade","record",
    "better than expected","strong","jumps","jump","growth","grows","up","increase",
    "increases","improves","approval","clearance","fda","contract win","partnership"
)

PCT_SYM  = re.compile(r"([+\-]?\d+(?:\.\d+)?)\s*[%％]\s*\+?", flags=re.I)
PCT_WORD = re.compile(r"([+\-]?\d+(?:\.\d+)?)\s*(?:percent|pct)", flags=re.I)

def find_pct(text: str):
    t = (text or "").lower()
    vals = []
    for m in PCT_SYM.finditer(t):
        try: vals.append(float(m.group(1)))
        except: pass
    for m in PCT_WORD.finditer(t):
        try: vals.append(float(m.group(1)))
        except: pass
    if not vals:
        m = re.search(r"\bup\s+([+\-]?\d+(?:\.\d+)?)\b", t)
        if m:
            try: vals.append(float(m.group(1)))
            except: pass
    if vals:
        pos = [v for v in vals if v > 0]
        return max(pos) if pos else max(vals, key=abs)
    return None

def pct_to_score(p: float) -> float:
    if p is None: return 0.0
    if p >= 60: return 3.0
    if p >= 35: return 2.5
    if p >= 15: return 2.0
    if p > 0:   return 1.0
    return 0.0

# -------------------- news CSV -> per-symbol max --------------------

def news_max_by_symbol(news_csv: pathlib.Path):
    if not news_csv.exists():
        return {}
    rows, _, _ = _read_csv_robust(news_csv)
    try:
        first = rows[0] if rows else {}
        print(f"[DEBUG] news headers: {list(first.keys())[:12]}")
    except Exception:
        pass

    mx = {}
    for row in rows:
        sym = (row.get("ticker") or row.get("symbol") or "").upper()
        if not sym:
            continue
        title = (row.get("title") or row.get("best_headline") or "").lower().strip()
        try:
            sc = float(row.get("best_score") or row.get("score") or "0")
        except Exception:
            sc = 0.0

        if any(k in title for k in NEG_KEYS):
            sc = 0.0
        else:
            pct = find_pct(title)
            if pct is not None:
                mapped = pct_to_score(pct)
                if mapped > sc:
                    print(f"[MAG] {sym} news matched {pct:.1f}% -> score {mapped}")
                sc = max(sc, mapped)
            elif any(k in title for k in POS_KEYS):
                sc = max(sc, 2.0)

        if sc > 0:
            mx[sym] = max(sc, mx.get(sym, 0.0))
    return mx

# -------------------- sanitize scores CSV (negatives -> score=0) --------------------

def sanitize_scores_csv(scores_csv: pathlib.Path):
    if not scores_csv.exists():
        return
    rows, delim, headers = _read_csv_robust(scores_csv)
    if not rows:
        return

    title_key = None
    for k in ("title","headline","news_title","best_headline","desc"):
        if k in rows[0]:
            title_key = k
            break

    out_lines = []
    out_headers = headers[:]
    if "grade" not in out_headers: out_headers.append("grade")
    for need in ("symbol","score"):
        if need not in out_headers:
            out_headers.append(need)

    for r in rows:
        sym = (r.get("symbol") or r.get("ticker") or "").upper()
        title = (r.get(title_key or "") or "").lower()
        try:
            score = float(r.get("score") or r.get("catalyst_score") or "0")
        except Exception:
            score = 0.0

        if any(k in title for k in NEG_KEYS):
            score = 0.0

        grade = 2 if score >= 2 else (1 if score >= 1 else 0)

        r2 = {k: r.get(k, "") for k in out_headers}
        r2["symbol"] = sym
        r2["score"] = f"{score}".rstrip("0").rstrip(".") if isinstance(score, float) else score
        r2["grade"] = grade
        out_lines.append(r2)

    with scores_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_headers, delimiter=delim)
        w.writeheader()
        for r2 in out_lines:
            w.writerow(r2)
    print(f"[SANITIZE] Applied negative-headline guard in {scores_csv.name}")

# -------------------- pick top-N (A-only by default) --------------------

def pick_topn(scores_csv: pathlib.Path, news_csv: pathlib.Path, topn: int, min_grade: int, allow_b_fill: bool):
    rows_raw, _, headers_s = _read_csv_robust(scores_csv)
    print(f"[DEBUG] scores headers: {headers_s}")

    news_max = news_max_by_symbol(news_csv)

    rows = []
    for row in rows_raw:
        sym = (row.get("symbol") or row.get("ticker") or "").upper()
        if not sym:
            continue
        try:
            score0 = float(row.get("score") or row.get("catalyst_score") or "0")
        except Exception:
            score0 = 0.0

        title = (row.get("title") or row.get("headline") or row.get("news_title") or row.get("best_headline") or row.get("desc") or "")
        title_l = title.lower()

        if any(k in title_l for k in NEG_KEYS):
            score0 = 0.0
            print(f"[NEG] {sym} negative headline -> forced score 0 at scores stage")

        score = max(score0, news_max.get(sym, 0.0))

        pct = find_pct(title_l)
        if pct is not None:
            mapped = pct_to_score(pct)
            if mapped > score:
                print(f"[MAG] {sym} title matched {pct:.1f}% -> score {mapped}")
            score = max(score, mapped)

        grade = 2 if score >= 2 else (1 if score >= 1 else 0)
        rows.append({"symbol": sym, "score": score, "grade": grade})

    # if scores were empty, fallback to news-only
    if not rows and news_max:
        for sym, sc in news_max.items():
            grade = 2 if sc >= 2 else (1 if sc >= 1 else 0)
            rows.append({"symbol": sym, "score": sc, "grade": grade})

    rows.sort(key=lambda x: (-x["score"], x["symbol"]))
    A = [r for r in rows if r["grade"] >= min_grade]
    B = [r for r in rows if r["grade"] == (min_grade - 1)]

    picked = []
    for r in A:
        if len(picked) >= topn: break
        picked.append(r["symbol"])

    if allow_b_fill and len(picked) < topn:
        for r in B:
            if len(picked) >= topn: break
            if r["symbol"] in picked: continue
            picked.append(r["symbol"])

    # IMPORTANT: No unconditional fallback. If not enough A (and no --allow-b-fill), we accept fewer or zero picks.
    print(f"[PICKER] rows_in_scores={len(rows_raw)} news_symbols={len(news_max)} min_grade={min_grade} allow_b_fill={allow_b_fill} -> picked={picked}")
    return picked, rows

# -------------------- main --------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--scenario", required=True, help="Scenario (e.g., B, D, E)")
    ap.add_argument("--topn", type=int, default=3, help="Max catalyst picks (default 3)")
    ap.add_argument("--min-grade", type=int, default=2, help="Minimum grade (2=A)")
    ap.add_argument("--allow-b-fill", action="store_true", help="Allow grade B fallback (off by default)")

    # RVOL passthrough to CLI
    ap.add_argument("--min-rvol-open", type=float, default=None,
                    help="Opening RVOL gate (e.g., 1.5 = 50% > prior day first N minutes).")
    ap.add_argument("--rvol-open-minutes", type=int, default=15,
                    help="Minutes window for opening RVOL comparison (default 15).")

    args = ap.parse_args()

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    src_dir = str(repo_root / "src")
    env = os.environ.copy()
    env["PYTHONPATH"] = src_dir + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    date = args.date
    ymd = date.replace("-", "")

    # 1) top gappers
    sh([sys.executable, "scripts/topgappers.py", "--date", date], env=env)
    universe_in = repo_root / "data" / "samples" / "universe_sample.txt"

    # 2) enrich catalysts (denylist etc.)
    cat_dir = repo_root / "out" / ymd / "catalyst"
    ensure_dir(cat_dir)
    scores_csv = cat_dir / f"catalyst_scores_{date}.csv"
    news_csv   = cat_dir / f"catalyst_news_{date}.csv"

    res = sh_capture([sys.executable, "scripts/enrich_universe_catalyst.py",
                      "--date", date, "--in", str(universe_in), "--out", str(scores_csv)], env=env)
    for line in (res.stdout or "").splitlines():
        print(line)
    if res.stderr:
        sys.stderr.write(res.stderr)

    # 2b) sanitize scores
    sanitize_scores_csv(scores_csv)

    # 3) pick & audit (A-only by default)
    picked, all_rows = pick_topn(scores_csv, news_csv,
                                 topn=args.topn,
                                 min_grade=args.min_grade,
                                 allow_b_fill=args.allow_b_fill)

    uni_out = repo_root / "data" / f"universe_catalyst_{date}.txt"
    uni_out.write_text("\n".join(picked) + ("\n" if picked else ""), encoding="utf-8")

    audit_csv = cat_dir / f"catalyst_universe_{date}.csv"
    with audit_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["symbol","score","grade","picked"])
        w.writeheader()
        picked_set = set(picked)
        for r in all_rows:
            w.writerow({"symbol": r["symbol"], "score": r["score"], "grade": r["grade"],
                        "picked": 1 if r["symbol"] in picked_set else 0})

    print(f"[CATALYST] picked={len(picked)} -> {uni_out}")
    print(f"[AUDIT] {audit_csv}")

    # 4) fetch minutes (today)
    sh([sys.executable, "scripts/fetch_minutes_polygon.py", "--date", date, "--session", "rth"], env=env)

    # 5) write params snapshot (for summarizer footer)
    out_day_dir = repo_root / "out" / ymd
    ensure_dir(out_day_dir)
    snapshot = {
        "date": date,
        "scenario": args.scenario,
        "min_rvol_open": args.min_rvol_open,
        "rvol_open_minutes": args.rvol_open_minutes,
        "max_trades_per_symbol": 1,      # keep aligned with CLI default unless you pass a flag there
        "daily_max_loss": 1000.0,        # keep aligned with CLI default unless overridden
        "catalyst_topn": args.topn,
        "catalyst_min_grade": args.min_grade,
        "catalyst_allow_b_fill": bool(args.allow_b_fill),
    }
    (out_day_dir / "_last_cfg.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    # 6) backtest (RVOL flags forwarded)
    out_dir = repo_root / "out" / ymd / f"{args.scenario}_catalyst"
    ensure_dir(out_dir)
    cmd = [sys.executable, "-m", "midas_v2.cli", "backtest",
           "--date", date, "--scenario", args.scenario,
           "--universe", str(uni_out), "--out", str(out_dir)]
    if args.min_rvol_open is not None:
        cmd += ["--min-rvol-open", str(args.min_rvol_open),
                "--rvol-open-minutes", str(args.rvol_open_minutes)]
    sh(cmd, env=env)

    # 7) summarize
    sh([sys.executable, "scripts/summarize_results.py", "--date", date], env=env)

if __name__ == "__main__":
    main()