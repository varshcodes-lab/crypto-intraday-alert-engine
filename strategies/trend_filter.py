from indicators.ema import calculate_ema

def trend_filter(closes):
    ema50 = calculate_ema(closes, 50)
    ema100 = calculate_ema(closes, 100)

    if ema50 is None or ema100 is None:
        return None

    if ema50 > ema100:
        return "BULLISH"
    elif ema50 < ema100:
        return "BEARISH"
    else:
        return "SIDEWAYS"
