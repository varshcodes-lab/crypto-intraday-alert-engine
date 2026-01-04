from data.market_cache import MarketCache
from data.rest_client import fetch_klines
from config.symbols import SYMBOLS
from config.timeframes import DEFAULT_TIMEFRAME
from engine.strategy_engine import evaluate_strategies

cache = MarketCache()
symbol = SYMBOLS[1]

candles = fetch_klines(symbol, DEFAULT_TIMEFRAME)
cache.initialize(symbol, DEFAULT_TIMEFRAME, candles)

result = evaluate_strategies(candles)

print("Strategy Result:")
print(result)
