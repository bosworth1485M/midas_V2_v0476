from dataclasses import dataclass

@dataclass
class Bar:
    ts: str
    o: float
    h: float
    l: float
    c: float
    v: int
    vwap: float | None = None
