# src/midas_v2/utils/epoch_tools.py  # v0.4.8
from __future__ import annotations  # v0.4.8
from typing import Optional  # v0.4.8
from datetime import datetime, timezone  # v0.4.8

try:  # v0.4.8
    from zoneinfo import ZoneInfo  # Python 3.9+  # v0.4.8
except Exception:  # v0.4.8
    ZoneInfo = None  # v0.4.8

def minute_close_epoch_from_bar(
    bar: object,
    session_date: str,                 # 'YYYY-MM-DD'  # v0.4.8
    session_tz: str = "America/New_York"  # exchange session TZ  # v0.4.8
) -> Optional[int]:
    """
    Return minute-close epoch seconds (UTC) from a bar that may expose:
      - bar.ts (int/float epoch seconds) OR
      - bar.t  (string 'HH:MM' or 'HH:MM:SS' in session local time)

    If conversion isn't possible, returns None (safe to skip micro checks).  # v0.4.8
    """  # v0.4.8
    # Numeric epoch on .ts?  # v0.4.8
    ts_attr = getattr(bar, "ts", None)  # v0.4.8
    if isinstance(ts_attr, (int, float)):  # v0.4.8
        return int(ts_attr)  # v0.4.8

    # String time on .t? e.g., '13:38' or '13:38:00'  # v0.4.8
    t_attr = getattr(bar, "t", None)  # v0.4.8
    if isinstance(t_attr, str) and session_date:  # v0.4.8
        parts = t_attr.split(":")  # v0.4.8
        if 2 <= len(parts) <= 3:  # v0.4.8
            try:  # v0.4.8
                hh, mm = int(parts[0]), int(parts[1])  # v0.4.8
                ss = int(parts[2]) if len(parts) == 3 else 0  # v0.4.8
                if ZoneInfo is not None:  # v0.4.8
                    local = datetime.fromisoformat(f"{session_date}T{hh:02d}:{mm:02d}:{ss:02d}")  # v0.4.8
                    local = local.replace(tzinfo=ZoneInfo(session_tz))  # v0.4.8
                    utc = local.astimezone(timezone.utc)  # v0.4.8
                else:
                    # Fallback: assume input is already UTC if zoneinfo missing  # v0.4.8
                    utc = datetime.fromisoformat(f"{session_date}T{hh:02d}:{mm:02d}:{ss:02d}").replace(tzinfo=timezone.utc)  # v0.4.8
                return int(utc.timestamp())  # v0.4.8
            except Exception:  # v0.4.8
                return None  # v0.4.8
    return None  # v0.4.8