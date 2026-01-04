from data.websocket_client import BinanceWebSocketClient
from data.market_cache import MarketCache
from data.rest_client import fetch_klines
from config.timeframes import DEFAULT_TIMEFRAME
from config.symbols import SYMBOLS


cache = MarketCache()

for symbol in SYMBOLS:
    candles = fetch_klines(symbol, DEFAULT_TIMEFRAME)
    cache.initialize(symbol, DEFAULT_TIMEFRAME, candles)


def on_new_candle(candle):
    cache.update(candle["symbol"], candle["timeframe"], candle)
    print(f"Cache updated: {candle['symbol']} | candles = {len(cache.get(candle['symbol'], candle['timeframe']))}")


ws = BinanceWebSocketClient(on_candle_close=on_new_candle)
ws.start()

while True:
    pass
