# Scripts Quick Reference — Single Day & Range (v0.3.9)
Single day:
  python scripts\run_day_simple.py --date YYYY-MM-DD --scenario D
  python scripts\view_results.py --date YYYY-MM-DD --scenario D --preview 20 --top 5

Range:
  python scripts\run_range_and_summarize.py --start YYYY-MM-DD --end YYYY-MM-DD --scenario D
  python scripts\analyze_range_explained.py --csv out\auto\range_summary_<START>_<END>_D.csv
