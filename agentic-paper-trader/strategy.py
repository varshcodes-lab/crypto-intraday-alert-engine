"""Deterministic strategy baseline. Not a claim of predictive edge."""
import pandas as pd

def enrich_candles(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df.copy()
    out = df.copy()
    out["ema_fast"] = out["close"].ewm(span=9, adjust=False).mean()
    out["ema_slow"] = out["close"].ewm(span=21, adjust=False).mean()
    delta = out["close"].diff()
    gain = delta.clip(lower=0).rolling(14, min_periods=14).mean()
    loss = (-delta.clip(upper=0)).rolling(14, min_periods=14).mean()
    rs = gain / loss.replace(0, float("nan"))
    out["rsi"] = 100 - (100 / (1 + rs))
    # Session VWAP resets at midnight UTC when valid timestamps are available.
    typical = (out["high"] + out["low"] + out["close"]) / 3
    volume = pd.to_numeric(out["volume"], errors="coerce")

    timestamps = None
    if "timestamp" in out.columns:
        raw_ts = out["timestamp"]

        if pd.api.types.is_numeric_dtype(raw_ts):
            numeric_ts = pd.to_numeric(raw_ts, errors="coerce")
            median_ts = numeric_ts.dropna().abs().median()

            if pd.notna(median_ts) and median_ts > 1e11:
                timestamps = pd.to_datetime(
                    numeric_ts, unit="ms", utc=True, errors="coerce"
                )
            elif pd.notna(median_ts) and median_ts > 1e9:
                timestamps = pd.to_datetime(
                    numeric_ts, unit="s", utc=True, errors="coerce"
                )
        else:
            timestamps = pd.to_datetime(raw_ts, utc=True, errors="coerce")

    if timestamps is not None and timestamps.notna().all():
        session = timestamps.dt.floor("D")
        cumulative_volume = volume.groupby(session, sort=False).cumsum()
        cumulative_value = (typical * volume).groupby(
            session, sort=False
        ).cumsum()
        out["vwap"] = cumulative_value / cumulative_volume.replace(
            0, float("nan")
        )
    else:
        # Preserve compatibility with data that has no usable timestamps.
        cumulative_volume = volume.cumsum()
        cumulative_value = (typical * volume).cumsum()
        out["vwap"] = cumulative_value / cumulative_volume.replace(
            0, float("nan")
        )
    out["volume_avg20"] = out["volume"].rolling(20, min_periods=20).mean()
    return out

def buy_signal(df: pd.DataFrame, volume_multiplier: float = 1.2) -> tuple[bool, str]:
    data = enrich_candles(df)
    if len(data) < 30: return False, "insufficient_candles"
    row = data.iloc[-1]
    checks = {
        "ema_trend": pd.notna(row["ema_fast"]) and row["ema_fast"] > row["ema_slow"],
        "rsi_range": pd.notna(row["rsi"]) and 50 <= row["rsi"] <= 68,
        "above_vwap": pd.notna(row["vwap"]) and row["close"] > row["vwap"],
        "volume_confirm": pd.notna(row["volume_avg20"]) and row["volume"] > volume_multiplier * row["volume_avg20"],
    }
    if all(bool(v) for v in checks.values()):
        return True, "EMA9>EMA21; RSI 50-68; close>VWAP; volume>1.2x avg20"
    return False, "filters_not_met:" + ",".join(k for k, v in checks.items() if not bool(v))
