from __future__ import annotations
from typing import Tuple, Dict
import pandas as pd

DEFAULTS = dict(
    seconds_window=4,
    min_green_count=3,
    min_last_close_delta_bps=5,   # last close must exceed prior close by >= 0.05%
    max_red_body_bps=10,          # any red 1s body worse than 0.10% is a fail
    min_avg_body_bps=15,          # avg(|body|) across kept seconds >= 0.15%
    min_required_rows=3           # tolerate one missing second in illiquid moments
)

def _bps(a: float, b: float) -> float:
    """(a vs b) delta in basis points."""
    if b == 0 or b is None or a is None:
        return 0.0
    return (a / b - 1.0) * 10_000.0

def _fmt_bps(x: float) -> str:
    sign = "+" if x >= 0 else ""
    return f"{sign}{x:.0f}bps"

def _slice_last_seconds(df_seconds: pd.DataFrame, minute_close_ms: int, seconds_window: int) -> pd.DataFrame:
    """
    Keep strictly the last `seconds_window` seconds of the CURRENT minute ending at `minute_close_ms`.
    Example: minute close at 09:30 -> keep :30:56..:30:59 for window=4. Explicitly DROP :31:00.
    """
    if df_seconds is None or df_seconds.empty:
        return df_seconds

    start_keep = minute_close_ms - seconds_window * 1000
    end_keep   = minute_close_ms - 1  # do NOT include the next minute's :00

    df = df_seconds[(df_seconds["t"] >= start_keep) & (df_seconds["t"] <= end_keep)]
    if len(df) > seconds_window:
        df = df.tail(seconds_window)
    return df

def one_sec_continuation_ok(
    df_seconds: pd.DataFrame,
    minute_close_ms: int,
    seconds_window: int = DEFAULTS["seconds_window"],
    min_green_count: int = DEFAULTS["min_green_count"],
    min_last_close_delta_bps: int = DEFAULTS["min_last_close_delta_bps"],
    max_red_body_bps: int = DEFAULTS["max_red_body_bps"],
    min_avg_body_bps: int = DEFAULTS["min_avg_body_bps"],
    min_required_rows: int = DEFAULTS["min_required_rows"],
) -> Tuple[bool, str, Dict[str, float]]:
    """
    Return (ok, reason, metrics) for a 1-second micro-confirmation gate.
    Expects df_seconds columns: ['t','open','high','low','close','volume'] with 't' in epoch-ms UTC.
    """
    if df_seconds is None or df_seconds.empty:
        return False, "[MICRO] no_seconds_data", {"rows": 0}

    win = _slice_last_seconds(df_seconds, minute_close_ms, seconds_window)
    rows = int(len(win))

    if rows < min_required_rows:
        return (
            False,
            f"[MICRO] insufficient_rows {rows}/{seconds_window} (min_required={min_required_rows})",
            {"rows": rows, "need": min_required_rows}
        )

    greens = 0
    bodies_abs = []
    worst_red_bps = 0.0

    for _, r in win.iterrows():
        o = float(r["open"]); c = float(r["close"])
        body_bps = _bps(c, o)
        bodies_abs.append(abs(body_bps))
        if c > o:
            greens += 1
        else:
            worst_red_bps = max(worst_red_bps, abs(body_bps))

    last_close  = float(win.iloc[-1]["close"])
    prior_close = float(win.iloc[-2]["close"]) if rows >= 2 else last_close
    last_delta  = _bps(last_close, prior_close) if rows >= 2 else 0.0
    avg_body    = (sum(bodies_abs) / len(bodies_abs)) if bodies_abs else 0.0

    fails = []
    if greens < min_green_count:
        fails.append(f"green={greens}/{rows}<{min_green_count}")
    if rows >= 2 and last_delta < min_last_close_delta_bps:
        fails.append(f"last_delta={_fmt_bps(last_delta)}<{min_last_close_delta_bps}bps")
    if worst_red_bps > max_red_body_bps:
        fails.append(f"worst_red={int(worst_red_bps)}bps>{max_red_body_bps}bps")
    if avg_body < min_avg_body_bps:
        fails.append(f"avg_body={int(avg_body)}bps<{min_avg_body_bps}bps")

    metrics = {
        "rows": rows,
        "greens": greens,
        "last_delta_bps": round(last_delta, 2),
        "worst_red_bps": round(worst_red_bps, 2),
        "avg_body_bps": round(avg_body, 2),
        "seconds_window": seconds_window,
        "min_required_rows": min_required_rows,
    }

    if fails:
        reason = "[MICRO] " + ", ".join(fails)
        return False, reason, metrics

    reason = "[MICRO] ok " + f"green={greens}/{rows}, last_delta={_fmt_bps(last_delta)}, avg_body={int(avg_body)}bps"
    return True, reason, metrics

def one_sec_continuation_bool(
    df_seconds: pd.DataFrame,
    minute_close_ms: int,
    **kwargs
) -> bool:
    ok, _, _ = one_sec_continuation_ok(df_seconds, minute_close_ms, **kwargs)
    return ok