# scripts/test_micro_gateway.py
import argparse, sys, pathlib
from datetime import datetime, timezone

def main():
    root = pathlib.Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))
    from midas_v2.micro.micro_gateway import check_micro_continuation

    ap = argparse.ArgumentParser(description="Smoke-test: micro_gateway single call")
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--date", required=True)     # YYYY-MM-DD
    ap.add_argument("--minute", required=True)   # HH:MM:SS UTC (e.g., 13:41:00)
    ap.add_argument("--resolution", default="5s", choices=["1s","5s"])
    ap.add_argument("--window", type=int, default=60)
    ap.add_argument("--ema", type=int, default=1)
    ap.add_argument("--vwap", type=int, default=0)
    ap.add_argument("--ratio", type=float, default=0.60)
    ap.add_argument("--allow", type=int, default=1)
    args = ap.parse_args()

    minute_dt = datetime.fromisoformat(f"{args.date}T{args.minute}+00:00")
    minute_epoch = int(minute_dt.replace(tzinfo=timezone.utc).timestamp())
    ok = check_micro_continuation(
        symbol=args.symbol,
        minute_close_epoch=minute_epoch,
        resolution=args.resolution,
        window_secs=args.window,
        require_ema=bool(args.ema),
        require_vwap=bool(args.vwap),
        min_green_ratio=float(args.ratio),
        allow_first_pullback=bool(args.allow),
    )
    print("GATEWAY RESULT:", "PASS" if ok else "BLOCK")

if __name__ == "__main__":
    main()