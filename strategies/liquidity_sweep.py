def liquidity_sweep(candles):
    if len(candles) < 3:
        return False

    prev = candles[-2]
    last = candles[-1]

    sweep_high = last["high"] > prev["high"] and last["close"] < prev["high"]
    sweep_low = last["low"] < prev["low"] and last["close"] > prev["low"]

    return sweep_high or sweep_low
