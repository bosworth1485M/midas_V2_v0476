# scripts/fetch_minutes_polygon.py
# Fetch 1-minute bars from Polygon for every symbol in data/samples/universe_sample.txt
# and write: data/samples/sample_<YYYY-MM-DD>_<SYMBOL>.csv
#
# Auth change only:
# - Load ROOT/.env with override=True
# - Sanitize POLYGON_API_KEY (strip quotes/whitespace)
# - Use Authorization: Bearer <key> header (no ?apiKey= in URL)

# --- bootstrap: ensure src on path + load .env from project root ---
import os, sys, argparse, pathlib, csv, json, urllib.request
from datetime import datetime, timedelta, time, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv(ROOT / ".env", override=True)
except Exception as e:
    sys.stderr.write(f"[WARN] dotenv load failed: {e}\n")
# --- end bootstrap ---

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception as e:
    raise SystemExit("[ERR] zoneinfo not available (need Python 3.9+)") from e

NY = ZoneInfo("America/New_York")

def load_key():
    k = (os.environ.get("POLYGON_API_KEY") or "").strip().strip('"').strip("'")
    if not k:
        raise SystemExit("[ERR] POLYGON_API_KEY missing (set env var or add to .env)")
    return k

def fetch_minutes(symbol: str, day: str, key: str):
    # Polygon timestamps are Unix ms (UTC). We’ll convert to ET later.
    to = (datetime.strptime(day, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/{day}/{to}?adjusted=true&sort=asc&limit=50000"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}", "User-Agent": "midas_v2/minutes/1.0"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (trading day to fetch)")
    ap.add_argument("--session", choices=["all","rth"], default="all",
                    help="Session filter in ET: all (default) or rth (09:30–16:00 ET)")
    args = ap.parse_args()

    key = load_key()
    day = args.date

    uni_path = pathlib.Path("data/samples/universe_sample.txt")
    if not uni_path.exists():
        raise SystemExit(f"[ERR] universe file not found: {uni_path}")

    symbols = [s.strip() for s in uni_path.read_text(encoding="utf-8").splitlines() if s.strip()]
    if not symbols:
        raise SystemExit("[ERR] universe has no symbols")

    out_dir = pathlib.Path("data/samples")
    out_dir.mkdir(parents=True, exist_ok=True)

    # RTH window in ET
    rth_start = time(9, 30)   # 09:30
    rth_end   = time(16, 0)   # 16:00

    wrote = empty = failed = 0
    for sym in symbols:
        try:
            data = fetch_minutes(sym, day, key)
            rows = data.get("results") or []
            if not rows:
                empty += 1
                print(f"[WARN] no minutes for {sym}")
                continue

            out = out_dir / f"sample_{day}_{sym}.csv"
            with out.open("w", newline="", encoding="ascii") as f:
                w = csv.writer(f)
                w.writerow(["time","open","high","low","close","volume"])

                for x in rows:
                    # Convert ms since epoch (UTC) -> ET (America/New_York)
                    ts_utc = datetime.fromtimestamp(x["t"]/1000, tz=timezone.utc)
                    ts_et  = ts_utc.astimezone(NY)
                    # Optional RTH filter
                    if args.session == "rth":
                        tt = ts_et.timetz()
                        tt_naive = time(tt.hour, tt.minute, tt.second)
                        if not (rth_start <= tt_naive <= rth_end):
                            continue

                    w.writerow([
                        ts_et.strftime("%H:%M"),
                        x["o"], x["h"], x["l"], x["c"], x["v"]
                    ])
            wrote += 1
            print("Wrote", out)
        except Exception as e:
            failed += 1
            print(f"[WARN] {sym} failed: {e}")

    print(f"Done. wrote={wrote} empty={empty} failed={failed}")

if __name__ == "__main__":
    main()