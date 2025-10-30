from __future__ import annotations
import csv, os
from typing import List
from .base import DataProvider
from ..datamodel import Bar

class CsvLocalProvider(DataProvider):
    def __init__(self, root: str):
        self.root = root

    def load_minute_bars(self, symbol: str, date_str: str) -> List[Bar]:
        path = os.path.join(self.root, f"sample_{date_str}_{symbol}.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing sample file: {path}")
        out: List[Bar] = []
        with open(path, newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                out.append(Bar(
                    ts=row["time"],
                    o=float(row["open"]),
                    h=float(row["high"]),
                    l=float(row["low"]),
                    c=float(row["close"]),
                    v=int(float(row["volume"])),
                    vwap=float(row["vwap"]) if row.get("vwap") else None
                ))
        return out
