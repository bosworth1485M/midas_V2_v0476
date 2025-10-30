"""
Adaptive position sizing (confidence-weighted) with guardrails.

Drop-in module: safe to include without wiring; nothing changes until you call it.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class TierRule:
    news_min_score: float = 0.0
    min_rvol_open: float = 0.0


@dataclass
class SizingSettings:
    enabled: bool = False
    base_risk_usd: float = 50.0
    max_per_trade_risk_usd: float = 120.0
    max_daily_risk_usd: float = 300.0
    drawdown_throttle_after_losses: int = 3
    throttled_risk_factor: float = 0.5
    confidence_map: Dict[str, float] = None
    tier_rules: Dict[str, TierRule] = None

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "SizingSettings":
        d = d or {}
        cm = d.get("confidence_map") or {"A": 1.8, "B": 1.0, "C": 0.5}
        tr = d.get("tier_rules") or {
            "A": {"news_min_score": 3, "min_rvol_open": 2.4},
            "B": {"news_min_score": 2, "min_rvol_open": 2.0},
            "C": {"news_min_score": 1, "min_rvol_open": 1.5},
        }
        return SizingSettings(
            enabled=bool(d.get("enabled", False)),
            base_risk_usd=float(d.get("base_risk_usd", 50.0)),
            max_per_trade_risk_usd=float(d.get("max_per_trade_risk_usd", 120.0)),
            max_daily_risk_usd=float(d.get("max_daily_risk_usd", 300.0)),
            drawdown_throttle_after_losses=int(d.get("drawdown_throttle_after_losses", 3)),
            throttled_risk_factor=float(d.get("throttled_risk_factor", 0.5)),
            confidence_map={k: float(v) for k, v in cm.items()},
            tier_rules={k: TierRule(**v) for k, v in tr.items()},
        )


class AdaptiveSizer:
    """
    Stateless decisions from config + a tiny bit of state (loss streak, daily risk).
    - Call `pick_tier(ctx)` to choose A/B/C.
    - Call `per_trade_risk_usd(tier)` to get risk budget for the next trade.
    - Call `shares_for(entry, stop, risk_usd)` to compute quantity.
    - Call `on_exit(realized_pnl_usd)` after each trade to update streak/risk.
    - Call `reset_daily()` at the start of a new session.
    """

    def __init__(self, settings: SizingSettings):
        self.s = settings
        self.daily_risk_used = 0.0  # realized losses only
        self.loss_streak = 0

    @staticmethod
    def _tick_floor(price_diff: float) -> float:
        # Prevent div-by-zero; $0.01 is fine for small-cap US stocks.
        return max(0.01, abs(price_diff))

    def reset_daily(self) -> None:
        self.daily_risk_used = 0.0
        self.loss_streak = 0

    def pick_tier(self, ctx: Dict[str, Any]) -> str:
        """
        ctx should provide at least:
          - ctx['news_score']: float
          - ctx['min_rvol_open']: float
        We choose the highest tier that satisfies rules (A -> B -> C).
        """
        ns = float(ctx.get("news_score", 0.0))
        rv = float(ctx.get("min_rvol_open", 0.0))
        for tier in ("A", "B", "C"):
            rule = self.s.tier_rules.get(tier, TierRule())
            if ns >= rule.news_min_score and rv >= rule.min_rvol_open:
                return tier
        return "C"

    def per_trade_risk_usd(self, tier: str) -> float:
        """
        Computes the allowed risk for the next trade, honoring:
          - base_risk_usd scaled by confidence_map[tier]
          - max_per_trade_risk_usd cap
          - drawdown throttle after N consecutive losses
          - max_daily_risk_usd remaining budget
        """
        if not self.s.enabled:
            return 0.0  # caller can interpret 0 as "use legacy sizing"

        # Base × tier multiplier
        mult = float(self.s.confidence_map.get(tier, 1.0))
        risk = float(self.s.base_risk_usd) * mult

        # Per-trade cap
        risk = min(risk, float(self.s.max_per_trade_risk_usd))

        # Drawdown throttle
        if self.loss_streak >= int(self.s.drawdown_throttle_after_losses):
            risk *= float(self.s.throttled_risk_factor)

        # Remaining daily budget
        remaining = max(0.0, float(self.s.max_daily_risk_usd) - float(self.daily_risk_used))
        return max(0.0, min(risk, remaining))

    def shares_for(self, entry_price: float, stop_price: float, risk_usd: float) -> int:
        """
        Convert USD risk into integer share quantity using stop distance.
        """
        sl_dist = self._tick_floor(entry_price - stop_price)
        qty = int(max(1.0, risk_usd / sl_dist))
        return qty

    def on_exit(self, realized_pnl_usd: float) -> None:
        """
        Update loss streak and daily risk usage (count realized losses only).
        """
        if realized_pnl_usd < 0:
            self.loss_streak += 1
            self.daily_risk_used += abs(float(realized_pnl_usd))
        else:
            self.loss_streak = 0


def build_sizer_from_config(scenario_params: Dict[str, Any]) -> AdaptiveSizer:
    """
    Convenience factory: pass your scenario params dict (from scenarios.json).
    """
    sizing_cfg = (scenario_params or {}).get("sizing", {})
    settings = SizingSettings.from_dict(sizing_cfg)
    return AdaptiveSizer(settings)