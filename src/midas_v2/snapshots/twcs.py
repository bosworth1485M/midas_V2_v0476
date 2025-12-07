"""
v0.8.1.0.0: Trade-Window Candle Snapshot System (TWCS).

Core module for building trade snapshots: pre-trade and post-trade candle
windows with indicators, metadata, and (future) PNG rendering.

Does NOT fetch data; accepts candle/indicator data from backtester.
Snapshot failures do not stop backtest execution.
"""

# v0.8.1.0.0: Standard imports
import json
import sys
from pathlib import Path
from typing import Any, Dict


# v0.8.1.0.0: Build TWCS snapshot directory structure.
def build_snapshot_dir(root_out: Path, date_str: str, scenario: str, symbol: str, trade_id: str) -> Path:
    """
    v0.8.1.0.0: Return snapshot directory path:
    out/<YYYYMMDD>/<SCENARIO>/<SYMBOL>/snapshots/<TRADE_ID>/
    
    Creates all parent directories as needed.
    """
    # Convert date_str (YYYY-MM-DD) to YYYYMMDD
    yyyymmdd = date_str.replace("-", "")
    
    # Build path: out/<YYYYMMDD>/<SCENARIO>/<SYMBOL>/snapshots/<TRADE_ID>/
    snapshot_dir = (
        root_out
        / yyyymmdd
        / scenario
        / symbol
        / "snapshots"
        / trade_id
    )
    
    # v0.8.1.0.0: Create directories with parents and exist_ok
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    return snapshot_dir


# v0.8.1.0.0: Internal JSON write helper
def _write_json(path: Path, data: Dict[str, Any]) -> None:
    """
    v0.8.1.0.0: Write JSON to the given path (UTF-8, indent=2).
    Catches and logs exceptions but does not raise.
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERR] v0.8.1.0.0: Failed to write JSON to {path}: {e}", file=sys.stderr)


# v0.8.1.0.0: Placeholder for entry PNG rendering
def _render_entry_png(snapshot_dir: Path, meta: Dict[str, Any]) -> None:
    """
    v0.8.1.0.0: Placeholder for entry_snapshot.png rendering.
    Not yet implemented; to be filled in later.
    """
    # v0.8.1.0.0: PNG rendering stub – no-op for now
    pass


# v0.8.1.0.0: Placeholder for exit PNG rendering
def _render_exit_png(snapshot_dir: Path, meta: Dict[str, Any]) -> None:
    """
    v0.8.1.0.0: Placeholder for exit_snapshot.png rendering.
    Not yet implemented; to be filled in later.
    """
    # v0.8.1.0.0: PNG rendering stub – no-op for now
    pass


# v0.8.1.0.0: Save pre-trade snapshot metadata
def save_entry_snapshot(snapshot_dir: Path, meta: Dict[str, Any]) -> None:
    """
    v0.8.1.0.0: Save pre-trade snapshot metadata (JSON) and call PNG stub.
    
    Writes to: snapshot_dir / "trade_snapshot_entry_meta.json"
    Snapshot failures do not raise; they are logged and the backtest continues.
    """
    try:
        # v0.8.1.0.0: Ensure snapshot directory exists
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # v0.8.1.0.0: Write entry metadata JSON
        entry_meta_path = snapshot_dir / "trade_snapshot_entry_meta.json"
        _write_json(entry_meta_path, meta)
        
        # v0.8.1.0.0: Call PNG rendering stub
        _render_entry_png(snapshot_dir, meta)
        
    except Exception as e:
        print(f"[WARN] v0.8.1.0.0: Failed to save entry snapshot for {snapshot_dir}: {e}", file=sys.stderr)


# v0.8.1.0.0: Save post-trade snapshot metadata
def save_exit_snapshot(snapshot_dir: Path, meta: Dict[str, Any]) -> None:
    """
    v0.8.1.0.0: Save post-trade snapshot metadata (JSON) and call PNG stub.
    
    Writes to: snapshot_dir / "trade_snapshot_exit_meta.json"
    Snapshot failures do not raise; they are logged and the backtest continues.
    """
    try:
        # v0.8.1.0.0: Ensure snapshot directory exists
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # v0.8.1.0.0: Write exit metadata JSON
        exit_meta_path = snapshot_dir / "trade_snapshot_exit_meta.json"
        _write_json(exit_meta_path, meta)
        
        # v0.8.1.0.0: Call PNG rendering stub
        _render_exit_png(snapshot_dir, meta)
        
    except Exception as e:
        print(f"[WARN] v0.8.1.0.0: Failed to save exit snapshot for {snapshot_dir}: {e}", file=sys.stderr)


# v0.8.1.0.0: Public API
__all__ = [
    "build_snapshot_dir",
    "save_entry_snapshot",
    "save_exit_snapshot",
]