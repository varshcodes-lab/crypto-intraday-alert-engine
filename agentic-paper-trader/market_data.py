"""Public Binance Spot data only. This module has no authenticated/private API calls."""
import ccxt
import pandas as pd

STABLE_BASES = {"USDC", "FDUSD", "TUSD", "USDP", "DAI", "USDE", "USDS", "EUR"}

class MarketData:
    def __init__(self):
        self.exchange = ccxt.binance({
            "enableRateLimit": True,
            "timeout": 20000,
            "options": {"defaultType": "spot"},
        })
        self.exchange.load_markets()

    def liquid_usdt_symbols(self, min_quote_volume: float, limit: int) -> list[str]:
        tickers = self.exchange.fetch_tickers()
        ranked = []
        for symbol, ticker in tickers.items():
            market = self.exchange.markets.get(symbol, {})
            if not market or not market.get("spot") or not market.get("active", True):
                continue
            if not symbol.endswith("/USDT"):
                continue
            base = symbol.split("/")[0]
            if base in STABLE_BASES or base == "USDT":
                continue
            qv = ticker.get("quoteVolume")
            if qv is None:
                continue
            try: qv = float(qv)
            except (TypeError, ValueError): continue
            if qv >= min_quote_volume:
                ranked.append((symbol, qv))
        ranked.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in ranked[:limit]]

    def candles(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        raw = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not raw or len(raw) < 40:
            return pd.DataFrame()
        df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        # Last OHLCV row can be incomplete; only completed candles are exposed.
        df = df.iloc[:-1].dropna().drop_duplicates("timestamp").reset_index(drop=True)
        return df
