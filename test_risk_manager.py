from engine.risk_manager import calculate_trade_levels

entry = 42000

bullish_trade = calculate_trade_levels(entry, "BULLISH")
bearish_trade = calculate_trade_levels(entry, "BEARISH")

print("Bullish Trade:", bullish_trade)
print("Bearish Trade:", bearish_trade)
