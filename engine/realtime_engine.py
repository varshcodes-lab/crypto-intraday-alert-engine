from engine.strategy_engine import evaluate_strategies
from engine.risk_manager import calculate_trade_levels
from alerts.telegram import send_telegram_alert

from config.settings import MIN_CONFIDENCE_SCORE
from state_db import (
    get_active_trade,
    create_active_trade,
    close_active_trade,
    insert_alert,
    insert_confidence
)
from trade_logger import log_trade_entry, log_trade_exit


def process_new_candle(symbol, candles):
    last_price = candles[-1]["close"]

 

    active_trade = get_active_trade(symbol)

    if active_trade:
        entry = active_trade["entry"]
        target = active_trade["target"]
        stop_loss = active_trade["stop_loss"]
        qty = active_trade["quantity"]
        trend = active_trade["trend"]

        
        if trend == "BULLISH" and last_price >= target:
            pnl = (target - entry) * qty
            log_trade_exit(symbol, "TARGET", pnl)
            close_active_trade(symbol)

            send_telegram_alert({
                "symbol": symbol,
                "trend": trend,
                "score": "-",
                "reasons": ["Target hit"],
                "trade": active_trade
            })
            return

        
        if trend == "BULLISH" and last_price <= stop_loss:
            pnl = (stop_loss - entry) * qty
            log_trade_exit(symbol, "SL", pnl)
            close_active_trade(symbol)

            send_telegram_alert({
                "symbol": symbol,
                "trend": trend,
                "score": "-",
                "reasons": ["Stop loss hit"],
                "trade": active_trade
            })
            return

        return  

   

    result = evaluate_strategies(candles)
    score = result["score"]
    trend = result["trend"]

    insert_confidence(score)

    if score < MIN_CONFIDENCE_SCORE:
        return

    trade = calculate_trade_levels(last_price, trend)
    if not trade:
        return

    signal = {
        "symbol": symbol,
        "trend": trend,
        "score": score,
        "reasons": result["reasons"],
        "trade": trade
    }

    insert_alert(signal)
    create_active_trade(signal)
    log_trade_entry(signal)
    send_telegram_alert(signal)
