import json
import threading
import time
import websocket

from state_db import update_system_status


class BinanceWebSocketClient:
    def __init__(self, stream_url, timeframe, on_candle_close):
        self.stream_url = stream_url
        self.timeframe = timeframe
        self.on_candle_close = on_candle_close

        self.ws = None
        self.thread = None



    def _on_message(self, ws, message):
        data = json.loads(message)

      
        if "data" in data:
            data = data["data"]

        if "k" not in data:
            return

        k = data["k"]

       
        if not k["x"]:
            return

        candle = {
            "symbol": k["s"],
            "timeframe": self.timeframe,
            "open": float(k["o"]),
            "high": float(k["h"]),
            "low": float(k["l"]),
            "close": float(k["c"]),
            "volume": float(k["v"]),
            "close_time": k["T"],
        }

        self.on_candle_close(candle)

    def _on_error(self, ws, error):
        print("WebSocket error:", error)
        update_system_status("websocket", "ERROR")

    def _on_close(self, ws, code, msg):
        print("🔴 WebSocket closed")
        update_system_status("websocket", "DISCONNECTED")

        time.sleep(3)
        print("🔄 Reconnecting WebSocket...")
        self.start()

    def _on_open(self, ws):
        print("🟢 WebSocket connected.")
        update_system_status("websocket", "CONNECTED")

   

    def start(self):
        self.ws = websocket.WebSocketApp(
            self.stream_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open,
        )

        self.thread = threading.Thread(
            target=self.ws.run_forever,
            daemon=True
        )
        self.thread.start()
