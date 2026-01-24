After Copilot finishes (YOU run these, not Copilot)
Step A — verify the patch (one command)
git diff -- src/midas_v2/engine/backtester.py

Step B — run Dec range (one command)
python scripts\run_range_and_summarize.py --start 2025-12-02 --end 2025-12-06 --scenario B 2>&1 | Tee-Object -FilePath out\auto\B_runlog_20251202_20251206_v0.8.1.22.0.txt

Step C — run Oct range (one command)
python scripts\run_range_and_summarize.py --start 2025-10-20 --end 2025-10-31 --scenario B 2>&1 | Tee-Object -FilePath out\auto\B_runlog_20251020_20251031_v0.8.1.22.0.txt