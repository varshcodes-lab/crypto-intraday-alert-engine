from indicators.vwap import calculate_vwap

def vwap_bounce(candles, close_price):
    vwap = calculate_vwap(candles)

    if vwap is None:
        return False, vwap

    
    if close_price > vwap:
        return True, vwap

    return False, vwap
