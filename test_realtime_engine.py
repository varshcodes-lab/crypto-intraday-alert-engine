from data.rest_client import fetch_klines
from engine.realtime_engine import process_new_candle
from config.symbols import SYMBOLS
from config.timeframes import DEFAULT_TIMEFRAME

symbol = SYMBOLS[0]
candles = fetch_klines(symbol, DEFAULT_TIMEFRAME)

signal = process_new_candle(symbol, candles)

print("Signal:", signal)
