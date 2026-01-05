import time
from datetime import datetime

from data.websocket_client import BinanceWebSocketClient
from data.market_cache import MarketCache
from data.rest_client import fetch_klines

from config.symbols import SYMBOLS
from config.timeframes import DEFAULT_TIMEFRAME
from config.settings import STREAM_URL

from engine.realtime_engine import process_new_candle
from state_db import (
    init_db,
    update_system_status,
    update_last_price,
)
from trade_logger import init_trade_csv



print("📌 USING DB: state.db")
print("🚀 Starting Crypto Trading Engine...")

init_db()
print("✅ Database initialized")

init_trade_csv()

update_system_status("websocket", "DISCONNECTED")
update_system_status("last_candle_time", "-")
print("✅ SYSTEM STATUS WRITTEN")



cache = MarketCache()

print("📊 Preloading historical candles...")

for symbol in SYMBOLS:
    candles = fetch_klines(symbol, DEFAULT_TIMEFRAME)
    cache.initialize(symbol, DEFAULT_TIMEFRAME, candles)

print("✅ Market cache ready.")



def on_new_candle(candle):
    symbol = candle["symbol"]
    timeframe = candle["timeframe"]

    cache.update(symbol, timeframe, candle)
    candles = cache.get(symbol, timeframe)

    readable_time = datetime.fromtimestamp(
        candle["close_time"] / 1000
    ).strftime("%Y-%m-%d %H:%M:%S")

    update_last_price(symbol, candle["close"])
    update_system_status("last_candle_time", readable_time)

    process_new_candle(symbol, candles)



print("🟢 Connecting WebSocket...")

ws = BinanceWebSocketClient(
    stream_url=STREAM_URL,
    timeframe=DEFAULT_TIMEFRAME,
    on_candle_close=on_new_candle
)

ws.start()

print("🟢 WebSocket connected. Engine is LIVE.")




try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    update_system_status("websocket", "DISCONNECTED")
    print("🛑 Engine stopped")
