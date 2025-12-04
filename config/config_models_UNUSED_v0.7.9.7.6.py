# =============================================================================
# Midas_V2 config models (Pydantic v2) — v0.4.8 changes
# PURPOSE: enable the Green-Streak + MACD “momentum bundle” as FLAT top-level
#          fields in each scenario and make the Scenario model accept existing
#          flat keys from scenarios.json without validation errors.
# CHANGES (all lines tagged with `# v0.4.8`):
#   • Scenario.model_config: extra="allow" (was "forbid")  # v0.4.8
#   • Add four top-level fields with default OFF:
#       rise_bars, green_body_min, require_macd_rise, macd_rise_bars          # v0.4.8
#   • (Optional safety) ScenariosConfig.model_config: extra="ignore"          # v0.4.8
# Everything else is unchanged.
# =============================================================================

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
    # model_config = ConfigDict(extra="forbid")
    model_config = ConfigDict(extra="allow")  # v0.4.8 — allow flat keys (min_price, tp_pct, etc.) + momentum fields

    scanner: Optional[ScannerConfig] = None
    params: Optional[ScenarioParams] = None

    # ---- v0.4.8: Green-Streak (price action) & MACD-Rising (momentum) — default OFF
    rise_bars: int = Field(0, ge=0)                 # v0.4.8
    green_body_min: float = Field(0.0, ge=0.0, le=1.0)  # v0.4.8
    require_macd_rise: bool = False                 # v0.4.8
    macd_rise_bars: int = Field(0, ge=0)            # v0.4.8


class ScenariosConfig(RootModel[Dict[str, Scenario]]):
    """Root model: scenario-name -> Scenario (e.g., {'B': {...}, 'D': {...}})."""
    # (Optional safety) tolerate unknown extras at the root wrapper               # v0.4.8
    model_config = ConfigDict(extra="ignore")                                     # v0.4.8


def merge_scanner(global_scanner: ScannerConfig, scenario: Optional[Scenario]) -> ScannerConfig:
    """
    Merge global scanner defaults with a scenario's scanner overrides (if any).
    Scenario values win on conflicts; result is re-validated.
    """
    if not scenario or not scenario.scanner:
        return global_scanner
    merged = {**global_scanner.model_dump(), **scenario.scanner.model_dump()}
    return ScannerConfig.model_validate(merged)