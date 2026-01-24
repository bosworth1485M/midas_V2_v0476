Searched for text `MARGINAL_VWAP_WINDOW_REJECT` (`**/src/midas_v2/engine/backtester.py`), 2 results

Summary diagnosis (short)

- Location: the gate is in backtester.py (v0.8.1.11.0 MARGINAL_VWAP_WINDOW_REJECT).  
- Root cause: the code builds `window = [i-1, i-2, i-3]` and skips any negative indices. When i < 3 (first 0–2 minutes, commonly the 09:30 bar), all three check indices are out-of-bounds so the loop never finds qualifying bars; `hits` remains 0 and the code treats that as a rejection (hits < 2) and emits the warning with ts=09:30 hits=0. Thus many symbols log hits=0 at market open — this is intentional by the current logic, not a logging bug.  
- Dedupe effect: the code adds a dedupe key `reject_key = f"{date_str}:{sym}:MARGINAL_VWAP_WINDOW_REJECT"` into `early_reject_logged`. Because the key is only per (date,symbol,reject-type), the first open-time reject (hits=0) will suppress further MARGINAL_VWAP_WINDOW_REJECT logs for that symbol/day. That means later bars that would have produced a different reject message (e.g., hits=1) are not logged, hiding useful later diagnostics.

Why i<3 produces unavoidable early rejections
- The logic requires >=2 hits in the 3-bar window but does not special-case insufficient history. For i in {0,1,2}:
  - check_idx < 0 for every element → loop skips → hits == 0 → hits < 2 → reject.
- Many symbols’ first minute is 09:30 with i==0 (or small i), so they all get an immediate reject.

Smallest safe fix options (ordered by minimal invasiveness)

1) Skip the gate until the window is available (recommended minimal safe fix)
   - Add a guard before the window check:
     - if i < 3: skip the MARGINAL_VWAP_WINDOW_REJECT logic (treat as insufficient window), i.e. do not `log.warning` or `early_reject_logged.add(...)`, and do not increment telemetry for this gate.
   - Rationale: avoids spurious open-bar rejects; behavior for later bars is unchanged. Minimal and low-risk.

2) Treat insufficient window as an explicit non-blocking outcome (logged differently)
   - If start of window < 0, set reason='insufficient_window' and do NOT treat as fail (do not count as `hits<2` reject). Optionally log at DEBUG/INFO (not WARNING).
   - Rationale: preserves explicit observability without adding a blocking warning at open.

3) Keep current blocking semantics but change dedupe key granularity
   - Include the candidate timestamp or window-start in the dedupe key, e.g. `f"{date_str}:{sym}:MARGINAL_VWAP_WINDOW_REJECT:{candidate_ts}"`.
   - Rationale: will surface later rejects with different contexts; downside — can increase log volume. Use if you want full traceability instead of suppression.

4) Hybrid: skip check when i<3 AND change dedupe key to include reason or ts
   - Best for both correctness and observability: avoid spurious open rejects and still allow meaningful later rejects to be logged.

Notes on telemetry vs logging
- The current code increments telemetry["count_marginal_vwap_gate_blocks"] even when the window is empty; that can distort daily block counts. If preserving accuracy, pair Option 1/2 with not incrementing telemetry when i<3.

Minimal example (non-applied) of the recommended change (Option 1):
- Insert before the window loop (conceptual):
  if i < 3:
      # skip marginal VWAP window check at market open (insufficient history)
      continue  # or skip only the reject branch, depending on flow

Why I recommend Option 1
- It's the smallest, safest change: it avoids predictable false positive rejects at market open without touching thresholds, scenario logic, or throttles. It keeps the current gate for times when there is enough history and requires only a single index check.

If you want, I can propose the exact 1–3 line patch (no file edits unless you ask), or prepare a short PR-style diff for review. Which would you prefer?