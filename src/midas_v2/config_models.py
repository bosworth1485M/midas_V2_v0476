"""
Config models for Midas_V2 (Pydantic v2)

Usage:
    from pathlib import Path
    from midas_v2.config_models import (
        ScannerConfig, ScenariosConfig, merge_scanner
    )

    scanner = ScannerConfig.model_validate_json(Path("config/scanner.json").read_text(encoding="utf-8"))
    scenarios = ScenariosConfig.model_validate_json(Path("config/scenarios.json").read_text(encoding="utf-8")).root

    scn = scenarios.get("B")
    scanner_for_B = merge_scanner(scanner, scn)
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from pydantic import ConfigDict, field_validator


from typing import Dict, Optional, Any

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator


class ScannerConfig(BaseModel):
    """Global scanner settings (complete schema)."""
    model_config = ConfigDict(extra="forbid")  # strict: no typos

    price_min: float = Field(ge=0)
    price_max: float = Field(gt=0)
    min_gap_pct: float = Field(ge=0, le=100)
    max_gap_pct: float = Field(ge=0, le=100)
    # v0.7.9.6.4: add top_n for per-scenario Top-N gappers
    top_n: int = Field(ge=1, default=10)

    @field_validator("price_max")
    @classmethod
    def _price_order(cls, v, info):
        pm = info.data.get("price_min")
        if pm is not None and v <= pm:
            raise ValueError("price_max must be > price_min")
        return v

    @field_validator("max_gap_pct")
    @classmethod
    def _gap_order(cls, v, info):
        mg = info.data.get("min_gap_pct")
        if mg is not None and v < mg:
            raise ValueError("max_gap_pct must be ≥ min_gap_pct")
        return v


class ScannerOverride(BaseModel):
    """
    Per-scenario scanner overrides (all fields optional).
    Allows partial keys like only min_gap_pct/max_gap_pct.
    """
    model_config = ConfigDict(extra="forbid")  # still forbid typos

    price_min: Optional[float] = Field(default=None, ge=0)
    price_max: Optional[float] = Field(default=None, gt=0)
    min_gap_pct: Optional[float] = Field(default=None, ge=0, le=100)
    max_gap_pct: Optional[float] = Field(default=None, ge=0, le=100)
    # v0.7.9.6.4: optional override for top_n
    top_n: Optional[int] = Field(default=None, ge=1)

    @field_validator("price_max")
    @classmethod
    def _price_order(cls, v, info):
        if v is None:
            return v
        pm = info.data.get("price_min")
        if pm is not None and v <= pm:
            raise ValueError("price_max must be > price_min")
        return v

    @field_validator("max_gap_pct")
    @classmethod
    def _gap_order(cls, v, info):
        if v is None:
            return v
        mg = info.data.get("min_gap_pct")
        if mg is not None and v < mg:
            raise ValueError("max_gap_pct must be ≥ min_gap_pct")
        return v


class Scenario(BaseModel):
    """Per-scenario configuration."""
    model_config = ConfigDict(extra="forbid")  # only known top-level keys

    # IMPORTANT: scanner is now a partial override model
    scanner: Optional[ScannerOverride] = None

    # Free-form params (tp_pct, sl_pct, gate_minutes, rise_bars, etc.)
    params: Dict[str, Any] = Field(default_factory=dict)


class ScenariosConfig(RootModel[Dict[str, Scenario]]):
    """Root model: scenario-name -> Scenario (e.g., {'B': {...}, 'D': {...}})."""
    pass


def merge_scanner(global_scanner: ScannerConfig, scenario: Optional[Scenario]) -> ScannerConfig:
    """
    Merge global scanner defaults with a scenario's partial scanner overrides (if any).
    Scenario values win on conflicts; result is re-validated as a full ScannerConfig.
    """
    base = global_scanner.model_dump()
    if scenario and scenario.scanner:
        overrides = scenario.scanner.model_dump(exclude_none=True)
        base.update(overrides)
    # v0.7.9.6.4: allow Scenario.params['top'] to override scanner top_n per scenario
    if scenario and isinstance(scenario.params, dict) and "top" in scenario.params:
        try:
            base["top_n"] = int(scenario.params.get("top"))
        except Exception:
            # ignore non-int convertible values
            pass
    return ScannerConfig.model_validate(base)