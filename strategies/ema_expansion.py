from indicators.ema import calculate_ema

def ema_expansion(closes):
    ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)

    if ema20 is None or ema50 is None:
        return False

    compression = abs(ema20 - ema50) / ema50 < 0.001  # tight EMAs

    return compression
