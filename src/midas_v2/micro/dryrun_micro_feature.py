# src/midas_v2/micro/dryrun_micro_feature.py
"""
Module-friendly dry run for micro_feature.should_block_entry().
Run as:
  $env:PYTHONPATH='src'; python -m midas_v2.micro.dryrun_micro_feature --symbol STTK --date 2025-08-05 --minute 13:41:00 --scenario B
"""

import argparse
from datetime import datetime, timezone

def main():
    ap = argparse.ArgumentParser(description="Dry-run micro_feature.should_block_entry() without sidecar/registry")
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--date", required=True)     # YYYY-MM-DD
    ap.add_argument("--minute", required=True)   # HH:MM:SS (UTC)
    ap.add_argument("--scenario", default="B")
    args = ap.parse_args()

    # Import here so this file can run as a module cleanly
    from midas_v2.features.micro_feature import should_block_entry

    minute_dt = datetime.fromisoformat(f"{args.date}T{args.minute}+00:00")
    minute_epoch = int(minute_dt.replace(tzinfo=timezone.utc).timestamp())

    # Minimal params shell (feature reads sidecar or defaults)
    DummyParams = type("DummyParams", (), {})
    params = DummyParams()

    block = should_block_entry(args.scenario, args.symbol, minute_epoch, params)
    print("=== micro_feature dry run ===")
    print(f"Scenario: {args.scenario}")
    print(f"Symbol  : {args.symbol}")
    print(f"Minute  : {minute_dt.isoformat()}")
    print(f"Epoch   : {minute_epoch}")
    print(f"BLOCK?  : {block}  (False = allow; True = block)")

if __name__ == "__main__":
    main()