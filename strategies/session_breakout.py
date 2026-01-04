from datetime import datetime, timezone

def session_breakout(candles):
    now = datetime.now(timezone.utc).hour

    
    if now in range(7, 10) or now in range(13, 16):
        recent_high = max(c["high"] for c in candles[-10:])
        last_close = candles[-1]["close"]

        if last_close > recent_high:
            return True

    return False
