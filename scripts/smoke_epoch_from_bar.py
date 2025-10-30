# scripts/smoke_epoch_from_bar.py  # v0.4.8
import argparse, sys, pathlib  # v0.4.8
from types import SimpleNamespace  # v0.4.8

def main():
    ap = argparse.ArgumentParser(description="Smoke test: minute_close_epoch_from_bar")  # v0.4.8
    ap.add_argument("--date", required=True, help="Session date YYYY-MM-DD")  # v0.4.8
    ap.add_argument("--tz", default="America/New_York", help="Session TZ (default: America/New_York)")  # v0.4.8
    g = ap.add_mutually_exclusive_group(required=True)  # v0.4.8
    g.add_argument("--ts", type=int, help="bar.ts epoch seconds (numeric)")  # v0.4.8
    g.add_argument("--t", help="bar.t 'HH:MM' or 'HH:MM:SS' (string)")  # v0.4.8
    args = ap.parse_args()  # v0.4.8

    root = pathlib.Path(__file__).resolve().parents[1]  # v0.4.8
    sys.path.insert(0, str(root / "src"))  # v0.4.8
    from midas_v2.utils.epoch_tools import minute_close_epoch_from_bar  # v0.4.8

    # Build a minimal bar object with either .ts or .t  # v0.4.8
    if args.ts is not None:  # v0.4.8
        bar = SimpleNamespace(ts=args.ts)  # v0.4.8
    else:
        bar = SimpleNamespace(t=args.t)  # v0.4.8

    epoch = minute_close_epoch_from_bar(bar, args.date, args.tz)  # v0.4.8
    print("=== epoch smoke ===")  # v0.4.8
    print("date:", args.date)  # v0.4.8
    print("tz  :", args.tz)  # v0.4.8
    print("bar :", {"ts": getattr(bar, 'ts', None), "t": getattr(bar, 't', None)})  # v0.4.8
    print("epoch:", epoch)  # v0.4.8

if __name__ == "__main__":  # v0.4.8
    main()  # v0.4.8