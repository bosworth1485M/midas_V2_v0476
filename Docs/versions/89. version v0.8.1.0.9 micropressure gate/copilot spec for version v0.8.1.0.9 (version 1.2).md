You are making changes for Midas_V2 version v0.8.1.0.9.

GOAL (v0.8.1.0.9):
Implement “Definition B” microstructure gate: Rising 1-second pressure at the minute-entry moment.
This is NOT a confirmation breakout rule. Do NOT modify or tune Definition A logic.

HARD SCOPE RULES:
- Modify ONLY these files:
  1) src/midas_v2/strategy.py
  2) config/scenarios.json
- Do NOT change any other files.
- Do NOT change baseline entry/exit logic when the new gate is OFF.
- Fail CLOSED: if 1-second data is missing/malformed/ambiguous -> gate returns False (BLOCK).

PART 1 — scenarios.json
In config/scenarios.json, under Scenario B params (and any shared defaults if you have them), add:
- "micro_pressure_gate": false
- "micro_pressure_window_s": 20
- "micro_pressure_min_rising": 3

Keep micro_pressure_gate default FALSE to avoid regressions.

PART 2 — StrategyParams wiring (strategy.py)
In src/midas_v2/strategy.py:
- Add StrategyParams fields:
  - micro_pressure_gate: bool
  - micro_pressure_window_s: int
  - micro_pressure_min_rising: int
- Wire these from scenario params with sensible defaults (False / 20 / 3).

PART 3 — Implement gate helper (strategy.py)
Add a helper method (name can match existing style):
- _micro_pressure_ok(bars, i) -> bool

Definition B1 (“Rising Highs Count”):
At minute entry index i for symbol S:
1) Normalize entry time T (reuse existing time normalization helpers).
2) Load 1-second candles for that symbol/date from the existing local sample path pattern:
   data/samples/sample_1s_YYYY-MM-DD_SYMBOL.csv
3) Select 1-second candles with timestamps in [T - micro_pressure_window_s, T).
4) If there are fewer than (micro_pressure_min_rising + 1) candles -> return False.
5) Count the maximum streak of consecutive higher highs in timestamp order:
   For sequential candles k: if high[k] > high[k-1], streak += 1 else streak = 0.
   Track max_streak across the window.
6) Pass if max_streak >= micro_pressure_min_rising, else fail.

Return False on any exception or parsing issue.

PART 4 — Integrate into should_enter (strategy.py)
In should_enter() (or equivalent entry decision function):
- Insert the new gate AFTER the MACD gate, and BEFORE any plugin hooks.
- Only apply if micro_pressure_gate is True.
- If the gate fails: block the entry and log a single-line WHY entry.

PART 5 — Logging (strategy.py)
Add minimal structured logs ONLY when:
- CHECK: when gate is evaluated
- BLOCKED: when gate fails

Example format:
[WHY] v0.8.1.0.9 MICRO_PRESSURE_GATE: CHECK symbol=... time=... window_s=... min_rising=...
[WHY] v0.8.1.0.9 MICRO_PRESSURE_GATE: BLOCKED symbol=... time=... max_streak=... required=...

No per-candle logs.

TRACEABILITY:
Add inline comments near any new/modified code that include the version label “v0.8.1.0.9”.

DELIVERABLE:
Return the final diffs for the two files only.
