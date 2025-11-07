"""
Config models for Midas_V2 (Pydantic v2)

Usage:
    from pathlib import Path
    from midas_v2.config_models import ScannerConfig, ScenariosConfig, merge_scanner

    scanner = ScannerConfig.model_validate_json(Path("config/scanner.json").read_text(encoding="utf-8"))
    scenarios = ScenariosConfig.model_validate_json(Path("config/scenarios.json").read_text(encoding="utf-8")).root

    scn = scenarios.get("B")
    scanner_for_B = merge_scanner(scanner, scn)
"""

from typing import Dict, Optional, Any

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator


class ScannerConfig(BaseModel):
    """Global or per-scenario scanner settings."""
    # Forbid unknown keys (typos cause immediate errors)
    model_config = ConfigDict(extra="forbid")

    price_min: float = Field(ge=0)
    price_max: float = Field(gt=0)
    min_gap_pct: float = Field(ge=0, le=100)
    max_gap_pct: float = Field(ge=0, le=100)

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


class ScenarioParams(BaseModel):
    """
    Free-form scenario parameters used by runners (tp_pct, sl_pct, gate_minutes, rise_bars, etc.).
    We allow extras here so your existing scenarios.json continues to work.
    """
    model_config = ConfigDict(extra="allow")


class Scenario(BaseModel):
    """Per-scenario overrides."""
    # Only allow known top-level keys; this keeps structure clean.
    model_config = ConfigDict(extra="forbid")

    scanner: Optional[ScannerConfig] = None
    params: Optional[ScenarioParams] = None


class ScenariosConfig(RootModel[Dict[str, Scenario]]):
    """Root model: scenario-name -> Scenario (e.g., {'B': {...}, 'D': {...}})."""
    pass


def merge_scanner(global_scanner: ScannerConfig, scenario: Optional[Scenario]) -> ScannerConfig:
    """
    Merge global scanner defaults with a scenario's scanner overrides (if any).
    Scenario values win on conflicts; result is re-validated.
    """
    if not scenario or not scenario.scanner:
        return global_scanner
    merged = {**global_scanner.model_dump(), **scenario.scanner.model_dump()}
    return ScannerConfig.model_validate(merged)