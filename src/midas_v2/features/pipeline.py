# v0.4.8
from __future__ import annotations
from typing import Callable, Dict, List, Any
from pathlib import Path

# Simple registry of callables by stage name
_STAGES: Dict[str, List[Callable[..., bool]]] = {
    "before_enter": [],  # each returns True to BLOCK, False to ALLOW
}

def register(stage: str, fn: Callable[..., bool]) -> None:
    _STAGES.setdefault(stage, []).append(fn)

def run(stage: str, **ctx: Any) -> bool:
    """
    Return True to BLOCK entry if any enabled feature says 'block', else False to ALLOW.
    If no function is registered/enabled, returns False (allow).
    """
    for fn in _STAGES.get(stage, []):
        try:
            if fn(**ctx):
                return True  # block
        except Exception:
            # Fail-open by design: ignore feature errors in baseline
            pass
    return False