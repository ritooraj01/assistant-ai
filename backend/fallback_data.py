"""Fallback datasets for live endpoints when real-time sources fail."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Map supported symbols to sample CSV files.
_SAMPLE_FILES: Dict[str, Path] = {
    "NIFTY": DATA_DIR / "nifty_5m.csv",
    # Use NIFTY sample as a generic fallback for BANKNIFTY as well.
    "BANKNIFTY": DATA_DIR / "nifty_5m.csv",
}


def _normalise_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["start_ts"] = (df["timestamp"].astype("int64") // 10**9).astype(float)
    elif "start_ts" in df.columns:
        df["start_ts"] = pd.to_numeric(df["start_ts"], errors="coerce")
    else:
        df["start_ts"] = (pd.RangeIndex(len(df)) * 300).astype(float)

    numeric_cols = ["open", "high", "low", "close", "volume"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = 0.0

    df = df.dropna(subset=["open", "high", "low", "close", "start_ts"])
    df.sort_values("start_ts", inplace=True)
    return df


@lru_cache(maxsize=None)
def _load_sample_df(symbol: str) -> pd.DataFrame:
    path = _sample_path(symbol)
    if not path or not path.exists():
        return pd.DataFrame()

    raw = pd.read_csv(path)
    return _normalise_dataframe(raw)


def _sample_path(symbol: str) -> Path | None:
    return _SAMPLE_FILES.get(symbol.upper())


def load_sample_dataframe(symbol: str, limit: int = 80) -> pd.DataFrame:
    df = _load_sample_df(symbol)
    if df.empty:
        return pd.DataFrame()
    return df.tail(limit).copy()


def generate_synthetic_candles(base_price: float, limit: int = 80, interval_sec: int = 300) -> List[Dict[str, float]]:
    """Generate synthetic candles for symbols without sample data."""
    import time
    import random
    
    current_time = time.time()
    candles = []
    
    # Generate candles going backwards in time
    for i in range(limit -1, -1, -1):
        start_ts = current_time - (i * interval_sec)
        
        # Add random walk around base price (±2%)
        volatility = base_price * 0.02
        price_change = random.uniform(-volatility, volatility)
        open_price = base_price + price_change
        
        # Generate realistic OHLC
        high_range = abs(random.gauss(0, volatility * 0.5))
        low_range = abs(random.gauss(0, volatility * 0.5))
        
        close_change = random.uniform(-volatility, volatility)
        close_price = open_price + close_change
        
        high_price = max(open_price, close_price) + high_range
        low_price = min(open_price, close_price) - low_range
        
        candles.append({
            "start_ts": start_ts,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
        })
        
        # Update base price for next candle (drift)
        base_price = close_price
    
    return candles


def load_sample_candles(symbol: str, limit: int = 80) -> List[Dict[str, float]]:
    df = load_sample_dataframe(symbol, limit)
    if df.empty:
        return []

    required_cols = {"open", "high", "low", "close", "start_ts"}
    missing = required_cols - set(df.columns)
    if missing:
        return []

    candles: List[Dict[str, float]] = []
    for row in df.itertuples(index=False):
        candles.append(
            {
                "start_ts": float(getattr(row, "start_ts")),
                "open": float(getattr(row, "open")),
                "high": float(getattr(row, "high")),
                "low": float(getattr(row, "low")),
                "close": float(getattr(row, "close")),
                "volume": float(getattr(row, "volume", 0.0) or 0.0),
            }
        )
    return candles


def load_sample_price(symbol: str) -> float | None:
    df = _load_sample_df(symbol)
    if df.empty:
        return None
    return float(df["close"].iloc[-1])


def load_sample_candles_with_time(symbol: str, limit: int = 80) -> List[Dict[str, float]]:
    """Load sample candles and convert to frontend format with 'time' field."""
    candles = load_sample_candles(symbol, limit)
    if not candles:
        return []
    
    # Convert start_ts to time
    result = []
    for c in candles:
        result.append({
            "time": int(c["start_ts"]),
            "open": float(c["open"]),
            "high": float(c["high"]),
            "low": float(c["low"]),
            "close": float(c["close"]),
        })
    return result
