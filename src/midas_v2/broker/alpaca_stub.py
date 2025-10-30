from .base import Broker, Order

class AlpacaBrokerStub(Broker):
    def __init__(self, dry_run: bool = True):
        super().__init__(dry_run=dry_run)
