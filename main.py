import time
from datetime import datetime

from data.websocket_client import BinanceWebSocketClient
from data.market_cache import MarketCache
from data.rest_client import fetch_klines

from config.symbols import SYMBOLS
from config.timeframes import DEFAULT_TIMEFRAME

from engine.realtime_engine import process_new_candle
from state_db import init_db, update_system_status
from trade_logger import init_trade_csv



# INITIALIZATION


print("🚀 Starting Crypto Trading Engine...")

# Initialize SQLite DB
init_db()

# Initialize CSV trade journal
init_trade_csv()

# Initial system status
update_system_status("websocket", "DISCONNECTED")
update_system_status("last_candle_time", "-")



cache = MarketCache()

print("📊 Preloading historical candles...")

for symbol in SYMBOLS:
    candles = fetch_klines(symbol, DEFAULT_TIMEFRAME)
    cache.initialize(symbol, DEFAULT_TIMEFRAME, candles)

print("✅ Market cache ready.")



def on_new_candle(candle):
    """
    Called whenever a candle CLOSES from Binance WebSocket.
    Candle schema is guaranteed by BinanceWebSocketClient.
    """

    symbol = candle["symbol"]
    timeframe = candle["timeframe"]

    
    cache.update(symbol, timeframe, candle)
    candles = cache.get(symbol, timeframe)

    
    readable_time = datetime.fromtimestamp(
        candle["close_time"] / 1000
    ).strftime("%Y-%m-%d %H:%M:%S")

    update_system_status("last_candle_time", readable_time)

    
    process_new_candle(symbol, candles)



stream_names = [
    f"{symbol.lower()}@kline_{DEFAULT_TIMEFRAME}"
    for symbol in SYMBOLS
]

STREAM_URL = "wss://stream.binance.com:9443/ws/" + "/".join(stream_names)

ws = BinanceWebSocketClient(
    stream_url=STREAM_URL,
    on_candle_close=on_new_candle,
    timeframe=DEFAULT_TIMEFRAME
)

ws.start()

update_system_status("websocket", "CONNECTED")

print("🟢 WebSocket connected. Engine is LIVE.")



try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("🛑 Shutting down engine...")
    ws.stop()
    update_system_status("websocket", "STOPPED")
