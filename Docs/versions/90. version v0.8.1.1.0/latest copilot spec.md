Copilot Pseudocode Spec — v0.8.1.1.0
Location Discipline: VWAP Extension Filter (single knob, A/B testable)
Version Goal

Add one location-based rule to reduce late/over-extended entries by blocking entries that are too far above VWAP at the moment an entry is attempted. Feature must be OFF by default. 

DOCUMENT 3 Copilot Pseudocode S…

0) Hard Scope Rules (STRICT)

Modify ONLY:

src/midas_v2/strategy.py

config/scenarios.json

DO NOT modify:

microstructure / 1-second logic

existing entry/exit rules

risk sizing / risk manager

TWCS snapshot/PNG code (but WHY logs must be visible in logs)

No new scripts. No new files.

Feature must be OFF by default.

Add inline version trace comments near new/modified code:

# v0.8.1.1.0

1) Config: Add Scenario Parameters (config/scenarios.json)

In Scenario B params, add:

"vwap_extension_gate": false,
"vwap_extension_max_pct": 1.5


Notes:

vwap_extension_gate defaults to false

vwap_extension_max_pct is a starting hypothesis threshold; we will A/B test and adjust modestly if needed.

Do not change other scenario defaults.

2) StrategyParams: Add Fields + Wiring (strategy.py)

In StrategyParams (or equivalent params container used in strategy), add:

vwap_extension_gate: bool

vwap_extension_max_pct: float

Defaults:

vwap_extension_gate = False

vwap_extension_max_pct = 1.5

Wire from scenario params the same way other knobs are wired.

Add inline comments:

# v0.8.1.1.0

3) Define “Entry Price” (IMPORTANT — must match real strategy)

When evaluating VWAP extension, entry_price MUST be the actual price used by the strategy to decide/execute entry on the attempted bar.

Implementation rule:

If the strategy has a computed variable like entry_price, trigger_price, breakout_price, limit_price, etc. for the entry attempt at bar index i, use that.

Do NOT blindly use close[i] unless that is already the actual decision price in the current strategy logic.

If the strategy currently uses close as the entry decision price, explicitly use bars[i].close (or equivalent).

Add inline comment near this choice:

# v0.8.1.1.0: entry_price uses the strategy’s actual entry decision price

4) VWAP Source (IMPORTANT — do not recompute)

Use the existing per-minute VWAP value already available in the pipeline (same source used for any VWAP confirm logic).

Rules:

Do not recompute VWAP from scratch

Use existing bar field or indicator dict (whatever the strategy already uses)

If VWAP is missing/None/NaN at index i, fail closed (BLOCK) with explicit WHY log

5) Add Helper: _vwap_extension_ok(...)

Add a helper method (names can vary but must be clearly isolated):

def _vwap_extension_ok(self, symbol: str, ts, entry_price: float, vwap: float, max_pct: float) -> tuple[bool, float]:
    """
    # v0.8.1.1.0
    Returns (ok, dist_pct)
    dist_pct = (entry_price - vwap) / vwap * 100
    """


Computation:

dist_pct = (entry_price - vwap) / vwap * 100.0

Decision:

If dist_pct > max_pct ⇒ BLOCK

Else ⇒ PASS

Extra rule:

If dist_pct <= 0 ⇒ PASS (not overextended)

Fail-closed:

If VWAP missing/<=0/NaN ⇒ BLOCK

Return dist_pct for logging.

6) Integration Point (where gate runs)

Insert the VWAP extension gate at the entry decision point:

Placement requirement:

After existing confirm gates (EMA/VWAP/MACD/green-streak, etc.)

Immediately before entry is accepted / order simulation / plugin hooks

Activation:

Gate runs only if params.vwap_extension_gate == True

If gate is OFF:

Do nothing and preserve exact prior behavior.

7) WHY Logging (Required, structured, versioned)

Add two log lines (CHECK and BLOCK) that are easy to grep.

On CHECK (when gate is enabled and VWAP exists)
[WHY] v0.8.1.1.0 VWAP_EXT: CHECK symbol=<sym> time=<ts> entry_price=<p> vwap=<v> dist_pct=<d> max_pct=<m>

On BLOCK (distance too large)
[WHY] v0.8.1.1.0 VWAP_EXT: BLOCKED symbol=<sym> time=<ts> entry_price=<p> vwap=<v> dist_pct=<d> max_pct=<m> reason=overextended

On BLOCK (missing/invalid VWAP)
[WHY] v0.8.1.1.0 VWAP_EXT: BLOCKED symbol=<sym> time=<ts> entry_price=<p> vwap=<v> dist_pct=NA max_pct=<m> reason=missing_vwap


Notes:

Use the same timestamp you already log for entries (bar time)

Keep formatting consistent with your existing [WHY] system

Do not remove or change existing WHY logs except where necessary to insert these.

8) Safety / Non-regression Requirements

If gate OFF (default): identical results to pre-change baseline.

No behavior changes outside Scenario B params addition.

No changes to microstructure code.

No changes to TWCS snapshot generation.

All new code paths must be robust against missing VWAP data.

9) Minimal A/B Test Plan (same day/universe)

Run the same date/universe twice:

A) Baseline

vwap_extension_gate = false

Record: trades, PnL, avg loss, expectancy, profit factor

B) Gate ON

vwap_extension_gate = true

Start with vwap_extension_max_pct = 1.5

Record same metrics

Validate with TWCS

For any blocked trade:

Confirm visually it was “too high / FOMO extension”
For any blocked winner:

Note it explicitly (we may need modest threshold adjustment)

Success criteria (qualitative + quantitative):

Blocks visually bad late entries

Preserves early clean winners

Improves at least one of: avg loss, expectancy, profit factor

If harmful after correctness is confirmed:

Try one modest threshold adjustment (example: 1.8 or 2.0)

If still harmful → reject feature cleanly (keep knob off by default)

10) Deliverables at end of implementation (what Copilot must ensure)

Code compiles / runs

Gate is OFF by default

Scenario B has new params

Logs show VWAP_EXT CHECK/BLOCK lines when enabled

No other file changes