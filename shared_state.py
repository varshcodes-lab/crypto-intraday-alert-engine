from datetime import datetime


system_status = {
    "websocket": "DISCONNECTED",
    "last_candle_time": None,
}


alerts = []          


strategy_stats = {
    "total_alerts": 0,
    "high_confidence_alerts": 0,
}


settings = {
    "min_confidence": 8,
    "enabled_symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"],
    "enable_liquidity_sweep": True,
    "enable_session_breakout": True,
}


confidence_history = []   