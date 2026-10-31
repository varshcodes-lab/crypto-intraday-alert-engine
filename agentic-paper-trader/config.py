from dataclasses import dataclass
import os
from dotenv import load_dotenv
load_dotenv()

def _f(name, default): return float(os.getenv(name, default))
def _i(name, default): return int(os.getenv(name, default))

@dataclass(frozen=True)
class Config:
    # Safety invariant: this build refuses any mode other than paper.
    trading_mode: str = os.getenv("TRADING_MODE", "paper").strip().lower()
    initial_cash: float = _f("INITIAL_CASH_USDT", 100.0)
    scan_interval: int = _i("SCAN_INTERVAL_SECONDS", 60)
    timeframe: str = os.getenv("TIMEFRAME", "5m")
    candle_limit: int = _i("CANDLE_LIMIT", 200)
    max_symbols: int = _i("MAX_SYMBOLS", 15)
    max_open_positions: int = _i("MAX_OPEN_POSITIONS", 3)
    risk_per_trade: float = _f("RISK_PER_TRADE", 0.005)
    max_daily_loss: float = _f("MAX_DAILY_LOSS", 0.02)
    max_position_fraction: float = _f("MAX_POSITION_FRACTION", 0.25)
    stop_loss_pct: float = _f("STOP_LOSS_PCT", 0.012)
    take_profit_pct: float = _f("TAKE_PROFIT_PCT", 0.024)
    fee_rate: float = _f("FEE_RATE", 0.001)
    slippage_rate: float = _f("SLIPPAGE_RATE", 0.0005)
    min_quote_volume: float = _f("MIN_QUOTE_VOLUME_USDT", 5_000_000.0)
    database_path: str = os.getenv("DATABASE_PATH", "trader.db")
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()

    def validate(self):
        if self.trading_mode != "paper":
            raise ValueError("Safety lock: this distribution supports TRADING_MODE=paper only.")
        if self.initial_cash <= 0: raise ValueError("INITIAL_CASH_USDT must be positive")
        if self.scan_interval < 10: raise ValueError("SCAN_INTERVAL_SECONDS must be >= 10")
        if not 0 < self.risk_per_trade <= 0.02: raise ValueError("RISK_PER_TRADE must be in (0, 0.02]")
        if not 0 < self.max_daily_loss <= 0.10: raise ValueError("MAX_DAILY_LOSS must be in (0, 0.10]")
        if not 0 < self.max_position_fraction <= 1: raise ValueError("MAX_POSITION_FRACTION must be in (0, 1]")
        if not 0 < self.stop_loss_pct < 1: raise ValueError("STOP_LOSS_PCT must be in (0, 1)")
        if not 0 < self.take_profit_pct < 1: raise ValueError("TAKE_PROFIT_PCT must be in (0, 1)")

CFG = Config()
