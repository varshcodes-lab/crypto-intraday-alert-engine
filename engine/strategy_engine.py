from strategies.trend_filter import trend_filter
from strategies.rsi_regime import rsi_regime
from strategies.vwap_bounce import vwap_bounce
from strategies.ema_expansion import ema_expansion
from strategies.liquidity_sweep import liquidity_sweep
from strategies.session_breakout import session_breakout


def evaluate_strategies(candles):
    closes = [c["close"] for c in candles]
    last_close = closes[-1]

    score = 0
    reasons = []

    trend = trend_filter(closes)
    if trend in ["BULLISH", "BEARISH"]:
        score += 2
        reasons.append(f"Trend: {trend}")

    rsi_ok, rsi_val = rsi_regime(closes, trend)
    if rsi_ok:
        score += 2
        reasons.append(f"RSI Regime OK ({rsi_val})")

    vwap_ok, vwap = vwap_bounce(candles, last_close)
    if vwap_ok:
        score += 2
        reasons.append("VWAP Bounce")

    if ema_expansion(closes):
        score += 2
        reasons.append("EMA Compression")

    if liquidity_sweep(candles):
        score += 1
        reasons.append("Liquidity Sweep")

    if session_breakout(candles):
        score += 1
        reasons.append("Session Breakout")

    return {
        "score": score,
        "trend": trend,
        "reasons": reasons
    }
