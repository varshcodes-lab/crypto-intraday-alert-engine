from data.websocket_client import BinanceWebSocketClient


def print_candle(candle):
    print(candle)


ws = BinanceWebSocketClient(on_candle_close=print_candle)
ws.start()


while True:
    pass
