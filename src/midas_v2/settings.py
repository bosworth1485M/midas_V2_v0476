from __future__ import annotations
import tomli, os
from dataclasses import dataclass

@dataclass
class RiskConfig:
    max_daily_loss: float
    max_r_per_trade: float
    halt_after_consec_losses: int
    cooldown_minutes_after_loss: int

@dataclass
class ExecConfig:
    dry_run: bool
    slippage_bps: int
    commission_per_share: float

@dataclass
class DataConfig:
    provider: str
    data_root: str

@dataclass
class LogConfig:
    level: str
    log_dir: str
    rotate_bytes: int
    backup_count: int

@dataclass
class Settings:
    mode: str
    env_file: str
    out_root: str
    risk: RiskConfig
    execution: ExecConfig
    data: DataConfig
    logging: LogConfig

def load_settings(path: str = "config/midas.toml") -> Settings:
    with open(path, "rb") as f:
        obj = tomli.load(f)
    return Settings(
        mode=obj.get("mode","backtest"),
        env_file=obj.get("env_file",".env"),
        out_root=obj.get("out_root","out"),
        risk=RiskConfig(**obj["risk"]),
        execution=ExecConfig(**obj["execution"]),
        data=DataConfig(**obj["data"]),
        logging=LogConfig(**obj["logging"]),
    )
