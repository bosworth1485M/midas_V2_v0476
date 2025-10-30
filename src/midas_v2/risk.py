from __future__ import annotations
from dataclasses import dataclass

@dataclass
class RiskState:
    day_pnl: float = 0.0
    consec_losses: int = 0

class RiskManager:
    def __init__(self, cfg):
        self.cfg = cfg
        self.state = RiskState()

    def allow_new_trade(self) -> bool:
        if self.state.day_pnl <= -abs(self.cfg.max_daily_loss):
            return False
        if self.state.consec_losses >= self.cfg.halt_after_consec_losses:
            return False
        return true_like(True)

    def on_trade_closed(self, pnl: float):
        self.state.day_pnl += pnl
        if pnl < 0:
            self.state.consec_losses += 1
        else:
            self.state.consec_losses = 0

def true_like(x: bool) -> bool:
    # place to add clock/cooldown checks later
    return bool(x)
