from collections import defaultdict
from typing import Dict, List

class MarketCache:
    def __init__(self):
        self.data: Dict[str, Dict[str, List]] = defaultdict(dict)

    def initialize(self, symbol: str, timeframe: str, candles: List):
        self.data[symbol][timeframe] = candles

    def update(self, symbol: str, timeframe: str, new_candle: Dict):
        self.data[symbol][timeframe].append(new_candle)
        if len(self.data[symbol][timeframe]) > 300:
            self.data[symbol][timeframe].pop(0)

    def get(self, symbol: str, timeframe: str):
        return self.data[symbol].get(timeframe, [])
