Here’s my full understanding—clean, step-by-step, with ownership and acceptance checks. No code, just the plan.

Where we are

Phase 1 (UI acceptance) is done: the page builds a standard range-runner command; you verified it by running August.

We are now executing Phase 2 from your roadmap: introduce a tiny parameter helper tied to the UI. (Phase 2 precedes Phase 3 and Phase 4 feature modules.)

Phase 2a — Read-only helper (this version)

Goal: UI can read parameters from scenarios.json; editing controls are visible but “Apply” is disabled.

Helper behavior:

GET /current returns allowed fields for the active scenario (initially: top, later price_min, price_max).

No write endpoints yet; no files change.

UI changes:

Add a Parameters panel with three columns: Current (from /current), Proposed (inputs), Preview After (computed client-side).

Buttons: Load Current (calls /current), Preview (local validation), Apply (disabled with tooltip).

Keep the existing Copy Run flow unchanged (dates on CLI).

Ownership:

Claude: implement the panel + wire GET /current; show Apply as disabled.

ChatGPT: guardrails and review.

Copilot: small type/import fixes if any.

Acceptance: Page shows Current → Proposed → Preview accurately; no file writes occur.

Version tag suggestion: v0.7.9.5-ui-readOnlyHelper.

Phase 2b — Enable writes (start with ONE field: top)

Goal: Safely apply a single parameter change with automatic backup; then run the same August range to confirm plumbing.

Allow-list (first write): top only.

Helper behavior:

POST /patch?dry_run=1 validates and returns “After” (no disk write).

POST /patch?apply=1 performs atomic write to config/scenarios.json and creates a timestamped backup (e.g., scenarios.YYYY-MM-DDTHH-mm-ss.bak.json). (This backup behavior is explicitly called for in Phase 2.)

UI changes:

Enable Apply only for top; others remain disabled/greyed.

Show the backup filename after a successful Apply.

Keep Copy Run as is.

Test loop:

Load Current; Preview a small top change (e.g., 3).

Apply → confirm backup notice → Copy Run → run August again.

Optionally try top=5, repeat. Save each summary CSV.

Acceptance: No crashes; JSON shows the new top; runs complete; summaries written. (This step’s goal is plumbing, not profit lift.)

Version tag suggestion: v0.7.9.5 (or v0.7.9.6 if you prefer to keep the read-only tag separate).

Phase 3 — Add more standard params (incrementally)

Goal: Expand the same helper/UI to a few more simple parameters—one at a time, each with its own run + tag.

Order (recommendation):

price_min, then price_max (validate price_min ≤ price_max)

gap_min, then gap_max

min_rvol_open

Process (repeat per field):

Enable that single field in the allow-list and UI.

Preview → Apply (backup) → Run the same August window → archive summary CSV → tag.

Roadmap alignment: This is exactly Phase 3’s mandate—extend to gap_min, gap_max, min_rvol_open, each verified with the same range.

Phase 4 — Feature modules (only after Phase 2/3 are solid)

Goal: Begin feature toggles behind config flags (default OFF), with tiny guarded checks in strategy.py.

First up: Green-Streak (minute), then Micro-Continuation (1s), etc.

Acceptance rule: keep only if a feature achieves ≥ +3 pp win-rate or ≥ +0.2R expectancy, or PF ≥ 1.2 with positive PnL lift, measured on the fixed date window.

Roadmap reference: Feature Modules list and Profit-Tuning Loop.

Roles (re-confirmed)

ChatGPT: architecture, guardrails, acceptance criteria, version discipline.

Claude: UI components + (later) helper wiring, following the spec; readability-only passes when asked.

Copilot: tiny IDE completions/fixes; repetitive refactors.

Minimal artifacts to save each step

Updated scenarios.json (with backup file auto-created on each Apply).

Range summary CSV (copy to Docs\\baselines\\...).

A short note in your version doc: what changed, command used, summary metrics.

The very next action (today)

Proceed with Phase 2a (read-only): Claude adds the Parameters panel with GET /current, Apply disabled.

You confirm the panel displays Current, accepts Proposed, shows Preview (client-side), and leaves files untouched.

Once that’s confirmed, we enable writes for top only (Phase 2b) and run the August window again to validate the plumbing—then proceed parameter-by-parameter.