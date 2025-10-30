python scripts\run_catalyst_range_and_summarize.py --start 2025-08-05 --end 2025-08-07 --scenario B --require-news --news-min-score 3 --top 2 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 2.4 --gate-minutes 20 --deny-negative --exclude-china --compare --compare-label B_sizingON_Aug05_07_A14_cap50_rvol26

python scripts\scan_run_bundles.py --scenario B --ignore-labels --dedupe-latest --per-day

python scripts\sizing_mode.py on-b

python scripts\sizing_mode.py off

python scripts\scan_run_bundles.py --scenario B --labels B_top2_score3_g20_rvol24_authFix --dedupe-latest --per-day --min-trades 1      