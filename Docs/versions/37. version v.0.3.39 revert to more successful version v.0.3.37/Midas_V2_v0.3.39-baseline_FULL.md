
# Midas_V2 — v0.3.39-baseline (Simple Flow Only)

## Git reset & branch prep

cd C:\Users\boydp\Desktop\midas_V2
git stash push -u -m "WIP before clean v0.3.37"
# Output: Saved working directory and index state On fix/flow-compat: WIP before clean v0.3.37

git fetch --all --tags
git switch -c clean/v0.3.37 v0.3.37
git reset --hard
# Output: HEAD is now at f186bf1 v0.3.37: writer metrics fix + strict guard; add clear/check scripts; docs: explicit dated commands & AS-RUN

git tag --points-at HEAD
# Output: v0.3.37, v0.3.38-compare-clean

set PYTHONPATH=%CD%\src
python scripts\clear_out.py
# Output: [OK] out/ cleared and recreated.

---

## Run A — 2025-08-05

python scripts\run_catalyst_flow.py --date 2025-08-05 --scenario B --news-first --require-news --news-min-score 2 --top 4 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 1.8 --gate-minutes 15 --compare --compare-label B_primary_top4_rvol18_g15

# Output excerpt:
# [UNIVERSE] HLMN, OPAD, MD
# [SUMMARY] B: TP=3 SL=0 Win%=100.00 PnL=47.82
# [PROFILE] newsOnly + Top-4 + band 10-40 + RVOL 1.80

python scripts\check_comparison_metrics.py
# Output: 20250805 -> comparison_1759070666.json | used=3 wr%=100.0 tp=3 sl=0 pnl=47.82 | OK

---

## Run B — 2025-08-06

python scripts\run_catalyst_flow.py --date 2025-08-06 --scenario B --news-first --require-news --news-min-score 2 --top 4 --enforce-band --band-min 10 --band-max 40 --min-rvol-open 1.8 --gate-minutes 15 --compare --compare-label B_primary_top4_rvol18_g15

# Output excerpt:
# [UNIVERSE] EHTH, ZETA, JELD, CRCT
# [SUMMARY] B: TP=3 SL=1 Win%=75.00 PnL=51.26
# [PROFILE] newsOnly + Top-4 + band 10-40 + RVOL 1.80

python scripts\check_comparison_metrics.py
# Output:
# 20250805 -> comparison_1759070666.json | used=3 wr%=100.0 tp=3 sl=0 pnl=47.82 | OK
# 20250806 -> comparison_1759071195.json | used=4 wr%=75.0 tp=3 sl=1 pnl=51.26 | OK
# ALL GOOD ✅

---

## Tagging

git tag -a v0.3.39-baseline -m "v0.3.39-baseline: clean v0.3.37; Aug-05 B=3/0 +47.82; Aug-06 B=3/1 +51.26; simple-flow only (run_catalyst_flow)"
git push origin v0.3.39-baseline

# Output:
# To https://github.com/bosworth1485M/midas_V2.git
#  * [new tag]         v0.3.39-baseline -> v0.3.39-baseline
