

import requests
from typing import List, Dict

BINANCE_REST_BASE = "https://api.binance.com/api/v3/klines"


def fetch_klines(
    symbol: str,
    interval: str,
    limit: int = 200
) -> List[Dict]:
    """
    Fetch historical candle data from Binance REST API.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    response = requests.get(BINANCE_REST_BASE, params=params, timeout=10)
    response.raise_for_status()

    raw_klines = response.json()
    candles = []

    for k in raw_klines:
        candles.append({
            "open_time": k[0],
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
            "close_time": k[6]
        })

    return candles
