from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Order:
    symbol: str
    side: str
    qty: int
    type: str = "market"

class Broker:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def submit(self, order: Order):
        if self.dry_run:
            return {"status":"DRY_RUN", "order":order}
        raise NotImplementedError("Live trading not enabled in starter.")
