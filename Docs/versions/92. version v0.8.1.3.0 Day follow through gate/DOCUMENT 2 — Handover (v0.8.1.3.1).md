DOCUMENT 2 — Handover (v0.8.1.3.1)
Use this at the start of the next thread
What is now frozen (baseline going into v0.8.1.3.1)

Scenario B trade logic unchanged (entries/exits/SL/TP unchanged)

Day gate remains in place with:

late-window follow-through

VWAP extension cap (1.5%) applied to both branches

liquidity floor cum_v >= 50,000

min_symbols currently set to 2

Keep the logging (it’s essential for diagnosing new changes)

What the new version must focus on (single objective)

Target the Aug-08 failure mode: “false PASS day that later trades red.”

We confirmed:

Raising day_follow_through_min_symbols to 3 is too strict (breaks Aug-06).

The failure case needs a different criterion, not a higher count.

Recommended next single knob: “Tape Health — require at least one ABOVE-VWAP qualifier”

Rationale:

On Aug-08, one of the two qualifiers is green_body below VWAP (still within cap).

We want to distinguish “two names kinda OK” from “real momentum day”.

Proposed rule:

Day gate passes only if:

total qualifiers ≥ day_follow_through_min_symbols (still 2), AND

at least one qualifier used close_gt_vwap (i.e., held above VWAP within cap and liquidity).

This should:

Preserve Aug-06 (AIMD qualifies via close_gt_vwap)

Preserve many genuine momentum days

Potentially fail days where only “green-body below VWAP” names qualify.

Success criteria for v0.8.1.3.1

Keep Aug-06 passing and trading

Keep Aug-07 failing (stand down)

Improve Aug-08 (either FAIL day or materially fewer trades / reduced loss)

Must remain explainable in logs (why pass/fail)

Forbidden (stay disciplined)

No SL/TP tuning

No entry logic changes

No sizing changes

No catalysts

No microstructure additions

No “multi-knob” tuning