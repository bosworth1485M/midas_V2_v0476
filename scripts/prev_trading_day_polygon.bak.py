# scripts/prev_trading_day_polygon.py
# Get the previous TRADING day (NYSE) for a given YYYY-MM-DD using Polygon grouped endpoint.
# No external deps. Requires POLYGON_API_KEY in env or .env.

import os, sys, json, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timedelta

API_FMT = "https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{date}?adjusted=true&apiKey={key}"

def load_key():
    k = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not k:
        envp = Path(".env")
        if envp.exists():
            for line in envp.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.strip().startswith("POLYGON_API_KEY="):
                    k = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not k:
        print("[ERR] POLYGON_API_KEY missing (set env var or add to .env)", file=sys.stderr)
        sys.exit(1)
    return "".join(k.split())

def grouped_count(date_str: str, key: str) -> int:
    url = API_FMT.format(date=date_str, key=key)
    req = urllib.request.Request(url, headers={"User-Agent": "midas_v2/prevday/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    # Polygon usually includes queryCount/resultsCount
    return int(data.get("resultsCount") or 0)

def find_prev_trading_day(target: str, key: str, max_back: int = 30) -> str:
    d = datetime.strptime(target, "%Y-%m-%d").date()
    # step back at least one day
    for i in range(1, max_back + 1):
        day = (d - timedelta(days=i)).isoformat()
        try:
            cnt = grouped_count(day, key)
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="ignore")[:200]
            except Exception:
                pass
            print(f"[ERR] HTTP {e.code} on {day}: {body}", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"[ERR] {e}", file=sys.stderr)
            sys.exit(3)
        if cnt > 0:
            return day
    print("[ERR] Could not determine previous trading day within window.", file=sys.stderr)
    sys.exit(4)

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Previous trading day via Polygon grouped endpoint")
    ap.add_argument("--date", required=True, help="Target trading date (YYYY-MM-DD)")
    ap.add_argument("--quiet", action="store_true", help="Print date only")
    args = ap.parse_args()

    key = load_key()
    prev = find_prev_trading_day(args.date, key)
    print(prev if args.quiet else f"Previous trading day for {args.date} is {prev}")

if __name__ == "__main__":
    main()