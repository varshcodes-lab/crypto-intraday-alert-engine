def calculate_vwap(candles):
    total_pv = 0
    total_volume = 0

    for c in candles:
        typical_price = (c["high"] + c["low"] + c["close"]) / 3
        total_pv += typical_price * c["volume"]
        total_volume += c["volume"]

    if total_volume == 0:
        return None

    return round(total_pv / total_volume, 2)
