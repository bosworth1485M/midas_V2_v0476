# scripts/test_micro_adapter.py
import argparse
import sys, pathlib
from datetime import datetime, timezone

def main():
    # Make sure this repo's src/ is imported (not the older v044)
    root = pathlib.Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))
    print(f"[DEBUG] Using src: {root / 'src'}")

    # ✅ Correct loader imports
    from midas_v2.data.one_sec_loader import get_micro_slice_cached
    from midas_v2.data.polygon_micro_loader import polygon_1s_loader
    from midas_v2.micro.micro_adapter import run_micro_continuation

    p = argparse.ArgumentParser(description="Smoke test: one_sec_loader ➜ micro_adapter ➜ micro_confirm")
    p.add_argument("--symbol", required=True)
    p.add_argument("--date", required=True, help="YYYY-MM-DD (session date)")
    p.add_argument("--minute", required=True, help="HH:MM:SS (UTC, e.g., 13:41:00)")
    p.add_argument("--seconds", type=int, default=60)
    p.add_argument("--resolution", default="5s", choices=["1s", "5s"])
    p.add_argument("--ema", type=int, default=1)      # 1=require EMA hold
    p.add_argument("--vwap", type=int, default=0)     # 1=require VWAP hold
    p.add_argument("--ratio", type=float, default=0.60) # green ratio
    p.add_argument("--allow", type=int, default=1)    # 1=allow first pullback
    args = p.parse_args()

    minute_dt = datetime.fromisoformat(f"{args.date}T{args.minute}+00:00")
    minute_epoch = int(minute_dt.replace(tzinfo=timezone.utc).timestamp())
    print(f"[DEBUG] minute_close UTC={minute_dt.isoformat()}  epoch={minute_epoch}")

    # ✅ Correct loader call
    seconds_bars = get_micro_slice_cached(
        symbol=args.symbol,
        minute_close_ts=minute_epoch,
        seconds=args.seconds,
        resolution=args.resolution,
        loader=polygon_1s_loader,
    )
    print(f"[INFO] fetched {len(seconds_bars)} {args.resolution} bars for {args.symbol} after {args.minute} UTC")

    # ✅ Adapter call (uses new micro_adapter.py)
    ok = run_micro_continuation(
        seconds_bars,
        minute_epoch,
        args.seconds,
        bool(args.ema),
        bool(args.vwap),
        float(args.ratio),
        bool(args.allow),
    )
    print("MICRO CONTINUATION:", "PASS" if ok else "BLOCK")

if __name__ == "__main__":
    main()