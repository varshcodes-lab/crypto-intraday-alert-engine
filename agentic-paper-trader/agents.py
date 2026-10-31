"""Lightweight agent orchestration. Agents are deterministic and auditable in this build."""
from dataclasses import dataclass
from strategy import buy_signal

@dataclass
class Signal:
    symbol: str
    should_buy: bool
    reason: str
    price: float
    candle_time: str

class MarketScannerAgent:
    def __init__(self, market_data, min_quote_volume, max_symbols):
        self.market_data, self.min_quote_volume, self.max_symbols = market_data, min_quote_volume, max_symbols
    def run(self):
        return self.market_data.liquid_usdt_symbols(self.min_quote_volume, self.max_symbols)

class StrategyAnalystAgent:
    def __init__(self, market_data, timeframe, candle_limit):
        self.market_data, self.timeframe, self.candle_limit = market_data, timeframe, candle_limit
    def analyze(self, symbol):
        df = self.market_data.candles(symbol, self.timeframe, self.candle_limit)
        if df.empty: return None, df
        row = df.iloc[-1]
        ok, reason = buy_signal(df)
        return Signal(symbol, ok, reason, float(row.close), str(row.timestamp)), df

class RiskSupervisorAgent:
    """Deterministic risk veto; cannot be overridden by the strategy analyst."""
    def __init__(self, risk_manager): self.risk_manager = risk_manager
    def approve(self, **kwargs): return self.risk_manager.position_quantity(**kwargs)

class PerformanceAgent:
    def summary(self, broker):
        return {
            "cash": broker.cash,
            "open_positions": len(broker.positions),
            "realized_pnl": broker.realized_pnl,
            "closed_trades": broker.closed_trades,
            "wins": broker.wins,
            "losses": broker.losses,
        }
