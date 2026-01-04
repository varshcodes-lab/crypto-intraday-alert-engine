import json
import threading
import time
import websocket


class BinanceWebSocketClient:
    def __init__(self, stream_url, on_candle_close, timeframe):
        self.stream_url = stream_url
        self.on_candle_close = on_candle_close
        self.timeframe = timeframe
        self.ws = None
        self.connected = False
        self._should_run = True
        self._thread = None

    def start(self):
        if self.connected:
            return

        self.ws = websocket.WebSocketApp(
            self.stream_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        self._thread = threading.Thread(
            target=self.ws.run_forever,
            daemon=True
        )
        self._thread.start()

    def _on_open(self, ws):
        self.connected = True
        print("🟢 WebSocket connected.")

    def _on_message(self, ws, message):
        data = json.loads(message)

        # Expecting Binance kline event
        if data.get("e") != "kline":
            return

        k = data["k"]

        # Only process CLOSED candles
        if not k["x"]:
            return

        candle = {
            "symbol": data["s"],
            "timeframe": self.timeframe,
            "open": float(k["o"]),
            "high": float(k["h"]),
            "low": float(k["l"]),
            "close": float(k["c"]),
            "volume": float(k["v"]),
            "open_time": k["t"],
            "close_time": k["T"],
        }

        self.on_candle_close(candle)

    def _on_error(self, ws, error):
        print(f"WebSocket error: {error}")
        self.connected = False

    def _on_close(self, ws, code, msg):
        self.connected = False
        print(f"🔴 WebSocket closed | code={code}")

        if self._should_run:
            time.sleep(3)
            print("🔄 Reconnecting WebSocket...")
            self.start()

    def stop(self):
        self._should_run = False
        if self.ws:
            self.ws.close()
