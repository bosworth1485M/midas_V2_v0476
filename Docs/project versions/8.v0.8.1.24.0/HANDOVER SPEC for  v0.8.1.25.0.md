HANDOVER SPEC — v0.8.1.25.0
Project: Midas_V2
Prior validated logic: v0.8.1.24.0 POST_DAMAGE_VWAP_HEAL_ESCAPE_HATCH (strategy change)
Next version purpose: v0.8.1.25.0 execution correctness fix (minute duplicate timestamp canonicalization)
Scope rule: v0.8.1.25.0 must be a single-change correctness version; no strategy changes.

1) Current Version State
v0.8.1.24.0 Strategy Outcome (Validated)


Escape hatch correctly:


✅ Restores SLMT 2025-10-23 winner


✅ Blocks BKYI 2025-10-27 failure




Wider range behavior:


Range 2025-10-20→10-31: C restored one healed winner; no BKYI regression


Range 2025-11-03→11-07: C admitted one healed entry (NFE) that later proved data-contaminated (duplicate timestamps)




Execution correctness bug discovered (must be fixed in v0.8.1.25.0)


Duplicate minute timestamps exist (e.g., NFE 2025-11-04 has two 15:05 rows)


backtester currently merges duplicates only for pos_bar_by_ts, but evaluates strategy on raw bars


mismatch detected via:


[WARN] [POS_MGMT_MISMATCH] ... eval_ohlc ... pos_ohlc ...




Quantification (so far):


POS_MGMT_MISMATCH appears on NFE (2025-11-04) and SLMT (2025-10-23)





2) Folder / Version Definitions for Testing
You will run tests across three separate folders/windows:
Test Matrix Names (for v0.8.1.25.0 onward)


C_new = v0.8.1.25.0 (post-fix build)


B_ref = v0.8.1.24.0 (pre-fix escape hatch baseline)


A_ref = v0.8.1.22.0 (unprotected baseline)



Note: This is intentionally not labeled “A/B/C” in the classic sense — it’s a 3-way baseline matrix with C_new as the new candidate.


3) Canonical Run Command Format (applies to all tests)
Always use range runner and capture stderr+stdout:
python scripts\run_range_and_summarize.py --start YYYY-MM-DD --end YYYY-MM-DD --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_<START>_<END>_B_<LABEL>.txt

Where <LABEL> is one of:


A (v0.8.1.22.0)


B (v0.8.1.24.0)


C (v0.8.1.25.0)



4) Completed Testing in v0.8.1.24.0 (Historical Record)
4.1 Single-day sanity tests (commands)
SLMT winner day — 2025-10-23
A (v0.8.1.22.0):
python scripts\run_range_and_summarize.py --start 2025-10-23 --end 2025-10-23 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251023_20251023_B_A.txt

B (v0.8.1.23.0):
python scripts\run_range_and_summarize.py --start 2025-10-23 --end 2025-10-23 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251023_20251023_B_B.txt

C (v0.8.1.24.0):
python scripts\run_range_and_summarize.py --start 2025-10-23 --end 2025-10-23 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251023_20251023_B_C.txt

Result summary:


A: 1 trade TP (+27.78)


B: 0 trades


C: 1 trade TP (+27.78)


BKYI failure day — 2025-10-27
A:
python scripts\run_range_and_summarize.py --start 2025-10-27 --end 2025-10-27 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251027_20251027_B_A.txt

C:
python scripts\run_range_and_summarize.py --start 2025-10-27 --end 2025-10-27 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251027_20251027_B_C.txt

Result summary:


A: 2 trades, both SL (BKYI same-bar SL present)


C: 0 trades (BKYI blocked)



4.2 Wider ranges completed (commands)
Range R1 — 2025-10-20 → 2025-10-31
A:
python scripts\run_range_and_summarize.py --start 2025-10-20 --end 2025-10-31 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251020_20251031_B_A.txt

B:
python scripts\run_range_and_summarize.py --start 2025-10-20 --end 2025-10-31 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251020_20251031_B_B.txt

C (v0.8.1.24.0):
python scripts\run_range_and_summarize.py --start 2025-10-20 --end 2025-10-31 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251020_20251031_B_C.txt

Result summary:


A: trades=7 pnl=-56.18


B: trades=0 pnl=0.00


C: trades=1 pnl=+27.78


Range R2 — 2025-11-03 → 2025-11-07
A:
python scripts\run_range_and_summarize.py --start 2025-11-03 --end 2025-11-07 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251103_20251107_B_A.txt

B:
python scripts\run_range_and_summarize.py --start 2025-11-03 --end 2025-11-07 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251103_20251107_B_B.txt

C (v0.8.1.24.0):
python scripts\run_range_and_summarize.py --start 2025-11-03 --end 2025-11-07 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251103_20251107_B_C.txt

Result summary:


A: trades=3 pnl=+21.20


B: trades=0 pnl=0.00


C: trades=1 pnl=-35.00 (NFE; later proven contaminated by duplicate timestamps)



5) v0.8.1.25.0 Required Single Change
Objective
Fix execution correctness by ensuring:


duplicates are canonicalized once into the bars list before evaluation


pos_bar_by_ts uses the same canonical bars


POS_MGMT_MISMATCH must disappear for known repro days



6) Bug Repro Proof (Captured)
Repro Day 1: NFE — 2025-11-04
Raw sample contains two 15:05 bars:


15:05 low=1.4201 close=1.43


15:05 low=1.5300 close=1.54


This creates:


DUP_TS duplicates=390


POS_MGMT_MISMATCH symbol=NFE ts=15:05


Repro Day 2: SLMT — 2025-10-23
Mismatches occur during SLMT run; must disappear after fix.

7) v0.8.1.25.0 Validation Plan (VERY DETAILED)
7.1 Bug Fix Verification — Must Pass (exact dates)
After implementing v0.8.1.25.0:
C_new only (v0.8.1.25.0) — repro day SLMT
python scripts\run_range_and_summarize.py --start 2025-10-23 --end 2025-10-23 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251023_20251023_B_C25.txt

C_new only — repro day NFE
python scripts\run_range_and_summarize.py --start 2025-11-04 --end 2025-11-04 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251104_20251104_B_C25.txt

Pass/Fail check (must be 0 lines):
Select-String -Path .\out\auto\B_runlog_*_B_C25.txt -Pattern "\[WARN\] \[POS_MGMT_MISMATCH\]"

Secondary diagnostic (optional but recommended):


DUP_TS may still appear, but mismatch must not.



7.2 Full Re-run of previously tested ranges in v0.8.1.25.0 (C_new vs B_ref vs A_ref)
IMPORTANT: for each range below, run all three versions:


C_new = v0.8.1.25.0


B_ref = v0.8.1.24.0


A_ref = v0.8.1.22.0


This allows:


verifying the bug fix does not change strategy behavior (except outcomes on contaminated cases)


confirming escape hatch still behaves as before


retaining the baseline comparison points



7.3 Ranges to rerun (the ones we already used)
Range R1 — 2025-10-20 → 2025-10-31
A_ref (22):
python scripts\run_range_and_summarize.py --start 2025-10-20 --end 2025-10-31 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251020_20251031_B_A22.txt

B_ref (24):
python scripts\run_range_and_summarize.py --start 2025-10-20 --end 2025-10-31 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251020_20251031_B_B24.txt

C_new (25):
python scripts\run_range_and_summarize.py --start 2025-10-20 --end 2025-10-31 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251020_20251031_B_C25.txt

Bug check:
Select-String -Path .\out\auto\B_runlog_20251020_20251031_B_C25.txt -Pattern "\[WARN\] \[POS_MGMT_MISMATCH\]"

Range R2 — 2025-11-03 → 2025-11-07
A_ref (22):
python scripts\run_range_and_summarize.py --start 2025-11-03 --end 2025-11-07 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251103_20251107_B_A22.txt

B_ref (24):
python scripts\run_range_and_summarize.py --start 2025-11-03 --end 2025-11-07 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251103_20251107_B_B24.txt

C_new (25):
python scripts\run_range_and_summarize.py --start 2025-11-03 --end 2025-11-07 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251103_20251107_B_C25.txt

Bug check:
Select-String -Path .\out\auto\B_runlog_20251103_20251107_B_C25.txt -Pattern "\[WARN\] \[POS_MGMT_MISMATCH\]"


8) Additional Monthly Ranges Required (New requirement)
In v0.8.1.25.0 we must also run these monthly ranges (A_ref / B_ref / C_new):
8.1 January 2025 (full month)


2025-01-02 → 2025-01-31


A_ref:
python scripts\run_range_and_summarize.py --start 2025-01-02 --end 2025-01-31 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20250102_20250131_B_A22.txt

B_ref:
python scripts\run_range_and_summarize.py --start 2025-01-02 --end 2025-01-31 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20250102_20250131_B_B24.txt

C_new:
python scripts\run_range_and_summarize.py --start 2025-01-02 --end 2025-01-31 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20250102_20250131_B_C25.txt

8.2 February 2025 (full month)


2025-02-03 → 2025-02-28


A_ref:
python scripts\run_range_and_summarize.py --start 2025-02-03 --end 2025-02-28 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20250203_20250228_B_A22.txt

B_ref:
python scripts\run_range_and_summarize.py --start 2025-02-03 --end 2025-02-28 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20250203_20250228_B_B24.txt

C_new:
python scripts\run_range_and_summarize.py --start 2025-02-03 --end 2025-02-28 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20250203_20250228_B_C25.txt

8.3 December 2025 (full month)


2025-12-01 → 2025-12-31


A_ref:
python scripts\run_range_and_summarize.py --start 2025-12-01 --end 2025-12-31 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251201_20251231_B_A22.txt

B_ref:
python scripts\run_range_and_summarize.py --start 2025-12-01 --end 2025-12-31 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251201_20251231_B_B24.txt

C_new:
python scripts\run_range_and_summarize.py --start 2025-12-01 --end 2025-12-31 --scenario B 2>&1 | Tee-Object .\out\auto\B_runlog_20251201_20251231_B_C25.txt


9) Acceptance Criteria for v0.8.1.25.0
Hard correctness acceptance


Zero POS_MGMT_MISMATCH on:


SLMT 2025-10-23


NFE 2025-11-04


All ranges run under C_new




Strategy regression acceptance


SLMT 2025-10-23:


C_new still re-admits healed winner




BKYI 2025-10-27:


C_new still blocks BKYI-class failure




Range-level expectations


C_new should remain:


much closer to B_ref on loss suppression than A_ref


not reintroduce BKYI-class loss clusters




Some PnL differences vs v0.8.1.24.0 are expected because previously contaminated trades may flip



10) Next Deliverable After This Handover
After user approves this handover spec:


generate Copilot Implementation Spec for v0.8.1.25.0


single change: canonicalize minute bars immediately after load (prepass + main loop)


re-use existing merge policy already used in pos_bar_by_ts



END HANDOVER SPEC — v0.8.1.25.0 (UPDATED)