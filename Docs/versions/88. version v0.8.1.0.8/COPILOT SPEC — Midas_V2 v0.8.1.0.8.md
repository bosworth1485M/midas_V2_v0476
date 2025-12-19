BEGIN COPILOT SPEC — Midas_V2 v0.8.1.0.8 — Microstructure Expansion Gate (Definition A) — Scenario B (Basic Breakout) ONLY
Goal
Implement a single, reversible, A/B-testable entry gate for Scenario B that blocks entries unless 1-second microstructure shows a breakout + hold in the last 30 seconds before the candidate entry time.
This is an experiment motivated by v0.8.1.0.7 findings (losses clustered in “worked/stalled/compressed” 1s tape).
Do NOT change anything else.

Hard Constraints


Modify ONLY these files:


src/midas_v2/strategy/strategy.py  # v0.8.1.0.8


config/scenarios.json             # v0.8.1.0.8




Do NOT change:


indicator calculations (EMA/MACD/VWAP logic)


risk sizing / RiskManager


stop/target logic (targets())


TWCS snapshot schema / TWCS plotter


runners (run_day_simple.py, run_range_and_summarize.py, etc.)


any network fetching code




Default behavior must remain identical to v0.8.1.0.7 when the gate is OFF.


Fail-safe behavior:


When gate is ON and required 1s data is missing/empty/unparseable → gate returns False (FAIL CLOSED) and blocks entry.


When gate is OFF → ignore completely.




Every new/modified line MUST include inline comment: # v0.8.1.0.8


Logging:


Log only when an entry is BLOCKED by this gate.


Do NOT spam “passed” logs.





Definition (Frozen) — Microstructure Expansion Gate (Definition A)
Given a candidate entry time T:
Use 1-second candles in window:


[T - window_s, T)  (strictly before T)


Compute:


prior_high = max(high) over candles in window


breakout_level = prior_high * (1 + breakout_bps/10000.0)  (bps → fraction)


Let:


last_close = close of the latest 1-second candle with timestamp <= T (prefer exactly at T if present, else nearest before)


Gate passes iff:


There exists at least one 1s candle in [T - window_s, T) with high >= breakout_level
AND


last_close >= breakout_level


If anything missing → gate fails.
Frozen parameters for v0.8.1.0.8:


window_s = 30


breakout_bps = 10



Data Source (Frozen)
No network calls. No new fetches.
Read 1-second candles from existing local CSVs already written by your Polygon seconds fetcher:


Directory: data/samples/


Filename pattern: sample_1s_{YYYY-MM-DD}_{SYMBOL}.csv


Example:


data/samples/sample_1s_2025-08-06_CYRX.csv


CSV columns (minimum):


t, o, h, l, c, v (t is ISO time)



Part A — Update Config (EXPLICIT)
MODIFY: config/scenarios.json  # v0.8.1.0.8
Under Scenario "B" → "params", add these fields (default OFF):
"micro_expansion_gate": false,
"micro_expansion_window_s": 30,
"micro_expansion_breakout_bps": 10

All added lines must be tagged with # v0.8.1.0.8 (use JSON comment style only if your repo already supports comments; otherwise omit comments in JSON and put the version marker in the commit message and in Python code. If JSON cannot contain comments, DO NOT add comments inside JSON.)

Part B — Update Strategy (EXPLICIT)
MODIFY: src/midas_v2/strategy/strategy.py  # v0.8.1.0.8
B1) Extend StrategyParams dataclass (ADD FIELDS)
Add these fields near other filters:


micro_expansion_gate: bool = False  # v0.8.1.0.8


micro_expansion_window_s: int = 30  # v0.8.1.0.8


micro_expansion_breakout_bps: float = 10.0  # v0.8.1.0.8


B2) Wire scenario config into params via create_strategy_params()
In create_strategy_params(), extend param_dict to include:


"micro_expansion_gate": _get_strategy_param("micro_expansion_gate", False)  # v0.8.1.0.8


"micro_expansion_window_s": _get_strategy_param("micro_expansion_window_s", 30)  # v0.8.1.0.8


"micro_expansion_breakout_bps": _get_strategy_param("micro_expansion_breakout_bps", 10)  # v0.8.1.0.8


B3) Add minimal helpers (private, in this same file)
Add imports if needed:


import os  # v0.8.1.0.8


import csv  # v0.8.1.0.8


from datetime import datetime, timedelta  # v0.8.1.0.8


Add helper: robust timestamp parsing
def _parse_iso_dt(s: str) -> Optional[datetime]:  # v0.8.1.0.8
    # Accept "YYYY-MM-DDTHH:MM:SS", optional "Z", optional space separator.
    # Return datetime or None; never raise.

Add helper: load 1s candles from local CSV
def _load_1s_candles(symbol: str, date_str: str) -> List[Dict[str, Any]]:  # v0.8.1.0.8
    """
    Load 1-second candles from:
      data/samples/sample_1s_{date_str}_{symbol}.csv
    Returns list of dicts with keys: "t_dt" (datetime), "h" (float), "c" (float)
    Fail-safe: return [] on missing file or parse failure. Never raise.
    """

Implementation rules:


Build path with os.path.join("data", "samples", f"sample_1s_{date_str}_{symbol}.csv")  # v0.8.1.0.8


Use csv.DictReader


Parse t via _parse_iso_dt


Parse h and c as floats


Store parsed datetime in key "t_dt" to avoid re-parsing repeatedly


Sort by "t_dt" ascending before returning


Never raise exceptions (wrap file open/parse in try/except)


Add helper: compute expansion gate + debug values
def _micro_expansion_ok(  # v0.8.1.0.8
    candles_1s: List[Dict[str, Any]],
    entry_dt: datetime,
    window_s: int,
    breakout_bps: float,
) -> (bool, Dict[str, Any]):  # v0.8.1.0.8
    """
    Implements Definition A exactly.
    Returns (ok, dbg) where dbg includes:
      prior_high, breakout_level, last_close, n_window
    Fail-safe: returns (False, dbg) if missing data.
    Never raises.
    """

Rules:


win_start = entry_dt - timedelta(seconds=window_s)  # v0.8.1.0.8


window = [c for c in candles_1s if win_start <= c["t_dt"] < entry_dt]  # v0.8.1.0.8


prior_high = max(c["h"] for c in window)


breakout_level = prior_high * (1 + breakout_bps/10000.0)


last candle: max(c for c in candles_1s if c["t_dt"] <= entry_dt)  (or None)


last_close = that candle["c"]


condition1 = any(c["h"] >= breakout_level for c in window)


condition2 = last_close >= breakout_level


ok = condition1 and condition2


Debug dict (always returned):


"prior_high" float or None


"breakout_level" float or None


"last_close" float or None


"n_window" int


Fail-safe:


If no window candles or no last candle → ok=False.


B4) Apply the gate ONLY in Scenario B Basic Breakout flow (exact insertion point)
In SimpleBreakoutStrategy.should_enter() basic breakout mode (the path where dip_reclaim is False):
Locate this existing block:
# Gate 4: MACD rising momentum filter (when enabled)
closes = [b.c for b in bars]
if not self._passes_macd_gate(closes, i):
    return False

Immediately AFTER it, insert:


Check enabled:


if bool(getattr(self.p, "micro_expansion_gate", False)):  # v0.8.1.0.8



Determine entry_dt:




bars[i].t may already be a datetime. If not, attempt parse via _parse_iso_dt(str(bars[i].t)).


If entry_dt is None → treat as blocked (ok=False).




Determine symbol/date:




symbol = getattr(self, "symbol", "")  # v0.8.1.0.8


date_str:


If entry_dt is not None → entry_dt.strftime("%Y-%m-%d")  # v0.8.1.0.8


Else fallback to getattr(self, "date", "") if present  # v0.8.1.0.8




If symbol is empty OR date_str empty → treat as blocked (ok=False).




Load 1s candles:


candles_1s = _load_1s_candles(symbol, date_str)  # v0.8.1.0.8



Compute:


window_s = int(getattr(self.p, "micro_expansion_window_s", 30))  # v0.8.1.0.8
breakout_bps = float(getattr(self.p, "micro_expansion_breakout_bps", 10))  # v0.8.1.0.8
ok, dbg = _micro_expansion_ok(candles_1s, entry_dt, window_s, breakout_bps)  # v0.8.1.0.8



If blocked, log one line and return False:
Log format (exact, single line):


[WHY] v0.8.1.0.8 MICRO_EXPANSION_GATE: BLOCKED symbol={symbol} time={entry_dt_iso} prior_high={prior_high} breakout_level={breakout_level} last_close={last_close} n_window={n_window}



entry_dt_iso = entry_dt.isoformat() if entry_dt else "n/a"


Use "n/a" for missing dbg values


Do NOT raise from logging


Then:
return False  # v0.8.1.0.8

Important:


Do NOT move, remove, or change the v0.4.8 external plug-in hook block.


The gate must run before that hook.


Do not apply this gate to dip reclaim mode in v0.8.1.0.8.



Acceptance Tests (Manual A/B)
Test A (Baseline — gate OFF)
In config/scenarios.json Scenario B:


"micro_expansion_gate": false


Run:
python scripts/run_range_and_summarize.py --start 2025-08-06 --end 2025-08-06 --scenario B
Expected:


Same trades as v0.8.1.0.7 baseline for 2025-08-06 (PHGE, MYGN, AIMD, CYRX)


Test B (Experiment — gate ON)
Set:


"micro_expansion_gate": true


Run the same command.
Expected:


Fewer trades (or same if all pass)


Logs include one or more:
MICRO_EXPANSION_GATE: BLOCKED ...


No crashes even if 1s CSV is missing for any symbol/date.


Do NOT tune parameters in v0.8.1.0.8.

Deliverables


config/scenarios.json updated (Scenario B params only; default OFF).  # v0.8.1.0.8


StrategyParams extended with micro_expansion fields.  # v0.8.1.0.8


create_strategy_params() reads the new params.  # v0.8.1.0.8


Local CSV loader + expansion gate helper implemented in strategy.py.  # v0.8.1.0.8


Gate applied in SimpleBreakoutStrategy.should_enter() after MACD gate and before plugin hook.  # v0.8.1.0.8


Blocked-entry logging line implemented.  # v0.8.1.0.8


END COPILOT SPEC — Midas_V2 v0.8.1.0.8 — Microstructure Expansion Gate (Definition A) — Scenario B ONLY