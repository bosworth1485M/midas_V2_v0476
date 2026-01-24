# COPILOT IMPLEMENTATION SPEC (FINAL — LOCKED)
# Midas_V2 v0.8.1.11.0
# Refine marginal-day VWAP acceptance from hard suppression → selective delay (windowed acceptance)
#
# IMPORTANT: Add inline comments with the version string "v0.8.1.11.0" next to any new/modified logic.

------------------------------------------------------------
GOAL (EXACT)
------------------------------------------------------------
On MARGINAL days (the existing “marginal day participation” regime in backtester.py),
refine the VWAP-acceptance requirement so that marginal entries are DELAYED until
VWAP acceptance is confirmed within a short recent window, instead of requiring
two strictly consecutive qualifying candles immediately before entry.

This must:
- Preserve removal of early 09:30 marginal junk trades (GRI/IBO/NAOV/BON/CNEY class).
- Restore legitimate delayed marginal continuations (JNVR-type).
- Preserve all previously correct behavior outside marginal days.

This is a surgical logic refinement, not a refactor.

------------------------------------------------------------
FILES ALLOWED TO CHANGE (ONLY)
------------------------------------------------------------
- src/midas_v2/engine/backtester.py

NO other files.
NO config changes.
NO new helpers.
NO new imports.
NO behavior changes outside the marginal-day path.

------------------------------------------------------------
NON-NEGOTIABLE CONSTRAINTS
------------------------------------------------------------
1) DO NOT refactor control flow, rename variables, or move blocks.
2) DO NOT change any existing day-gate logic or the meaning of:
   - day_gate_failed
   - effective_day_gate_failed
   - close_gt_vwap_count
3) DO NOT change how bars are selected/constructed.
4) Keep deterministic behavior and existing performance characteristics.
5) Keep “log once per symbol/day” behavior for marginal rejections.

------------------------------------------------------------
CURRENT CODE REALITY (DO NOT RE-IMPLEMENT)
------------------------------------------------------------
The marginal VWAP acceptance logic already exists in:
  src/midas_v2/engine/backtester.py

There is an existing block labeled exactly:

  "# v0.8.1.10.0: Marginal VWAP acceptance (2-bar pre-confirm)"

That block:
- Runs only on marginal-day conditions (A–D) already computed above it.
- Builds/uses vwap_map and checks “green + close > VWAP”.
- Currently REJECTS a bar’s entry attempt unless BOTH i-2 AND i-1 qualify.
- Logs once (using early_reject_logged + reject_key) and then continues.

v0.8.1.11.0 must REPLACE the acceptance rule inside that existing block.
Do NOT add a second gate elsewhere.

------------------------------------------------------------
INSERTION / PLACEMENT (CRITICAL)
------------------------------------------------------------
You MUST locate and edit the existing block:

  # v0.8.1.10.0: Marginal VWAP acceptance (2-bar pre-confirm)

This block is positioned immediately BEFORE the combined entry condition that looks like:

  if (not effective_day_gate_failed) and position is None and pending_entry is None and strat.should_enter(...):

Your change must remain in that location, and the block must still end with:
- a single “log once” (if not already logged) and
- `continue` to skip THIS BAR’s entry attempt when the acceptance rule fails.

------------------------------------------------------------
NEW RULE (v0.8.1.11.0) — WINDOWED VWAP ACCEPTANCE
------------------------------------------------------------
Replace the old “both i-2 and i-1 must qualify” rule with:

WINDOW = {i-1, i-2, i-3}
Compute, for each idx in WINDOW (only if idx >= 0):
  qualifies(idx) := (bar[idx] is green) AND (bar[idx].close > vwap(idx))

Let hits := count of indices in WINDOW that qualify.

ACCEPTANCE CONDITION:
  hits >= 2   (at least 2 of the last 3 bars qualify)

If hits >= 2:
  - PASS the gate for this bar (do nothing; allow the normal entry logic to proceed).

If hits < 2:
  - REJECT this bar’s entry attempt (DELAY behavior).
  - Preserve “log once per symbol/day” semantics using existing early_reject_logged + reject_key.
  - Then `continue` (skip this bar’s entry attempt).

IMPORTANT:
- This must behave like DELAY: early attempts are blocked until acceptance appears in-window;
  later attempts can proceed once hits>=2.

------------------------------------------------------------
EDGE CASES / DATA AVAILABILITY (KEEP SIMPLE)
------------------------------------------------------------
1) idx bounds:
   - Only evaluate indices that exist (idx >= 0).
   - If i < 1 (no i-1) the window will be sparse; hits will likely be 0; that is OK.

2) VWAP availability:
   - If VWAP is missing for a checked idx, treat qualifies(idx)=False for that idx.
   - Do NOT throw exceptions; do NOT change vwap_map creation.

3) “Meaningful logging” improvement (allowed, minimal):
   - If a failure is due to VWAP missing at the most relevant idx,
     make sure the WHY log does NOT print 0.00 close/vwap misleadingly.
   - It is OK to track a representative failing close/vwap for logging only.
   - Do NOT add complex “which bar failed” logic.

------------------------------------------------------------
LOGGING REQUIREMENTS
------------------------------------------------------------
A) Keep the existing “enabled=True” one-liner for the marginal gate
(if it exists already). If it does not exist, add ONE info line:

  MARGINAL_VWAP_GATE v0.8.1.11.0: enabled=True

B) On rejection (hits < 2), log ONCE per symbol/day using the existing latch mechanism.
Add/replace the existing warning log with this structure (same reject_key behavior):

  [WHY] v0.8.1.11.0 MARGINAL_VWAP_WINDOW_REJECT symbol=SYMBOL ts=HH:MM hits=H window=i-1,i-2,i-3

Optionally include representative values for debugging (close/vwap of one checked bar),
but do not spam per-bar logs. The “log once” latch must remain.

------------------------------------------------------------
WHAT MUST NOT CHANGE
------------------------------------------------------------
- Any behavior on non-marginal days.
- Any behavior when day gate fails normally (non-marginal logic).
- Any entry/exit logic, position sizing, risk manager behavior, stops, TP, etc.
- The combined entry condition and its ordering.
- Bar selection / candle construction / wick correctness.
- Any other guards (confirm-bar stop violation, post-expansion, structural damage, etc.).

------------------------------------------------------------
IMPLEMENTATION STEPS (DO EXACTLY)
------------------------------------------------------------
1) Open src/midas_v2/engine/backtester.py
2) Find the block:
     # v0.8.1.10.0: Marginal VWAP acceptance (2-bar pre-confirm)
3) Within that block, locate the existing check that enforces:
     i-2 qualifies AND i-1 qualifies
4) Replace ONLY that acceptance check with the windowed rule:
     hits over {i-1,i-2,i-3} must be >= 2
5) Preserve:
   - existing vwap_map usage
   - existing early_reject_logged + reject_key “log once” behavior
   - the final `continue` when failing (skip this bar)
6) Update the rejection log message to:
     [WHY] v0.8.1.11.0 MARGINAL_VWAP_WINDOW_REJECT ... hits=... window=...
7) Add minimal inline comments with "v0.8.1.11.0" adjacent to the new logic.

------------------------------------------------------------
VALIDATION / TEST PLAN (MANDATORY)
------------------------------------------------------------
Run tests using your standard workflow (range runner + logs to files).

A) FAST SANITY DAYS (step 1 of your workflow)
Run BOTH:
- One hostile / junk-prone day where early marginal trades used to lose
- One delayed-continuation day (JNVR-type) where v0.8.1.10.0 incorrectly suppressed

You must confirm from logs:
- Early marginal attempts are rejected until window acceptance forms.
- The rejection is logged once (not per bar).
- A later entry is allowed when hits>=2.

B) RANGE TEST (step 2)
Run the same multi-day range you use for A/B comparisons (e.g., a cluster like Aug 1–31),
and compare v0.8.1.10.0 vs v0.8.1.11.0 outputs.

Acceptance criteria:
1) Early-loss removal is preserved (no regression back to v0.8.1.9.0-like early junk).
2) At least one previously suppressed delayed continuation is restored (when present).
3) No unexpected behavior drift outside marginal days (spot-check logs).
4) Logging remains clean: one “enabled” line; one rejection line max per symbol/day.

If any criterion fails, revert the change.

------------------------------------------------------------
END OF SPEC (LOCKED)
------------------------------------------------------------