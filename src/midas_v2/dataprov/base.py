from abc import ABC, abstractmethod
from typing import List
from ..datamodel import Bar

class DataProvider(ABC):
    @abstractmethod
    def load_minute_bars(self, symbol: str, date_str: str) -> List[Bar]:
        ...
