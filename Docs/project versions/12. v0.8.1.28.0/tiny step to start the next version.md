# Session Summary for Midas_V2 v0.8.1.29.0
## Use this file at the start of the next session to restore context.

We are starting v0.8.1.29.0 as a single ALIGNMENT fix.
Hypothesis: Scenario B is misaligned because MARGINAL_VWAP_WINDOW_REJECT fires at 09:30 with hits=0 (empty window, i<3) and behaves as a hard reject, suppressing trades even in good August days. Dedupe hides later meaningful rejects.
Goal: Treat i<3 as insufficient history and bypass the marginal VWAP window reject without logging as a reject or incrementing gate-block telemetry; keep all later behavior unchanged.
Guardrails: One-file change (backtester.py only). No refactors. No runs by Copilot. Validate on Nov 18–22, Dec 2–6, Aug 5–15, Jul 14–18.