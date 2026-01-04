from config.settings import CAPITAL_PER_TRADE_USDT, RISK_REWARD_RATIO


def calculate_trade_levels(entry_price, trend):
    """
    Calculates SL, target, RR, and quantity
    based on fixed USDT capital per trade.
    """

    if trend == "BULLISH":
        stop_loss = entry_price * 0.995   
        target = entry_price * (1 + RISK_REWARD_RATIO * 0.005)
    elif trend == "BEARISH":
        stop_loss = entry_price * 1.005
        target = entry_price * (1 - RISK_REWARD_RATIO * 0.005)
    else:
        return None

    rr = RISK_REWARD_RATIO

    
    quantity = CAPITAL_PER_TRADE_USDT / entry_price

    return {
        "entry": round(entry_price, 4),
        "stop_loss": round(stop_loss, 4),
        "target": round(target, 4),
        "rr": rr,
        "quantity": round(quantity, 6),
    }
