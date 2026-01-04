from indicators.rsi import calculate_rsi

def rsi_regime(closes, trend):
    rsi = calculate_rsi(closes)

    if rsi is None:
        return False, rsi

    if trend == "BULLISH" and 40 <= rsi <= 50:
        return True, rsi

    if trend == "BEARISH" and 50 <= rsi <= 60:
        return True, rsi

    return False, rsi
