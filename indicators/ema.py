def calculate_ema(prices, period):
    if len(prices) < period:
        return None

    k = 2 / (period + 1)
    ema = sum(prices[:period]) / period

    for price in prices[period:]:
        ema = price * k + ema * (1 - k)

    return round(ema, 2)
