BEGIN COPILOT SPEC — v0.8.1.0.7 “COMPLIANCE CLEANUP” (NO LOGIC CHANGES)

Goal:
Bring the current twcs_plotter.py changes into strict compliance with the v0.8.1.0.7 spec, BEFORE running run_range_and_summarize. This is a SMALL, SAFE cleanup pass.

Hard constraints (must follow):

MODIFY ONLY this file:
src/midas_v2/plotting/twcs_plotter.py

DO NOT change trading logic, indicators, sizing, risk, snapshot schema, or runner behavior.
This is visualization-only cleanup.

Keep the current overlay features exactly as they already exist:

Title block (figure-level)

VWAP overlay line (scalar from snapshot indicators)

Entry/Exit price overlay line (best-effort)

Indicator/context box (with n/a handling)

Exit-only outcome box (best-effort)

1s window legend

Try/except safety so plotter never crashes the run

What to change (required):

A) INLINE VERSION COMMENTS — STRICT
The v0.8.1.0.7 spec requires:
“All new/modified lines MUST include inline comment: # v0.8.1.0.7”.

Action:

Add # v0.8.1.0.7 to EVERY line that was added or modified for v0.8.1.0.7.

This includes:

helper function definitions AND their bodies

any new imports

any new constants

any new/changed plotting lines

any new/changed try/except blocks

any changed savefig arguments

Do not add the comment to untouched pre-existing lines.

B) OUTPUT FORMAT STABILITY — RESTORE ORIGINAL FRAMING
The v0.8.1.0.7 spec says: “Keep output format identical”.

Action:

Remove bbox_inches="tight" from plt.savefig(...) if present.

Keep the existing output path, DPI, and format unchanged.

Keep tight_layout(...) usage if already present.

Revert any NEW figure sizing changes that were introduced only to “make room for overlays”.

If the v0.8.1.0.7 patch explicitly set a new figsize=(...) that did not exist before, remove that change and return to the prior/default sizing behavior for this plotter.

The overlays must adapt via layout/text placement rather than changing figure size.

Quality / safety requirements:

Do not introduce new dependencies.

Do not add a third panel.

Must remain null-safe and must never crash if:

indicators dict missing keys

candles_1s empty

outcome/pnl fields missing on entry snapshots

Ensure overlays remain readable without changing overall output framing.

Deliverable:

A single updated src/midas_v2/plotting/twcs_plotter.py that:

still renders PNGs with the overlays,

removes bbox_inches tight and any new figsize change,

has # v0.8.1.0.7 inline comments on all new/modified lines,

contains no other behavioral changes.

After making changes:

Do NOT run anything automatically.

I will run:
python scripts/run_range_and_summarize.py --start 2025-08-06 --end 2025-08-06 --scenario B
and visually inspect the resulting TWCS entry/exit PNGs.

END COPILOT SPEC — v0.8.1.0.7 “COMPLIANCE CLEANUP”