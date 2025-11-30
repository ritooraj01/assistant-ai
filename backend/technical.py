import pandas as pd
import numpy as np


# ---------------------- EMA ----------------------
def ema(series, period):
    if len(series) < period:
        return series.ewm(span=period, adjust=False).mean()
    return series.ewm(span=period, adjust=False).mean()


# ---------------------- RSI ----------------------
def rsi(close, period=14):
    # Return None for insufficient data instead of 0
    if len(close) < period:
        return pd.Series([None] * len(close))

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / (loss + 1e-9)
    rsi_vals = 100 - (100 / (1 + rs))
    
    # First 'period' values are NaN due to rolling window, set to None
    rsi_vals.iloc[:period] = None
    return rsi_vals


# ---------------------- ATR ----------------------
def atr(df, period=14):
    # Return None for insufficient data instead of 0
    if len(df) < period:
        return pd.Series([None] * len(df))

    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr_vals = tr.rolling(period).mean()
    
    # First 'period' values are NaN, keep as None
    atr_vals.iloc[:period] = None
    return atr_vals


# ---------------------- MACD ----------------------
def macd(close, fast=12, slow=26, signal=9):
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = ema_fast - ema_slow
    macd_signal = ema(macd_line, signal)
    hist = macd_line - macd_signal
    return macd_line, macd_signal, hist


# ---------------------- Bollinger Bands ----------------------
def bollinger(close, period=20, std=2):
    # Return None series for insufficient data
    if len(close) < period:
        none_series = pd.Series([None] * len(close))
        return (none_series, none_series, none_series, none_series, none_series)

    sma = close.rolling(period).mean()
    std_dev = close.rolling(period).std()
    upper = sma + std * std_dev
    lower = sma - std * std_dev
    width = (upper - lower) / sma
    percent_b = (close - lower) / (upper - lower)
    
    # Set first 'period' values to None
    sma.iloc[:period] = None
    upper.iloc[:period] = None
    lower.iloc[:period] = None
    width.iloc[:period] = None
    percent_b.iloc[:period] = None
    
    return sma, upper, lower, width, percent_b


# ---------------------- Supertrend ----------------------
def supertrend(df, period=10, multiplier=3):
    # Return None for insufficient data
    if len(df) < period:
        return pd.Series([None] * len(df))

    hl2 = (df["high"] + df["low"]) / 2
    atr_val = atr(df, period)

    upperband = hl2 + multiplier * atr_val
    lowerband = hl2 - multiplier * atr_val

    st = [None] * len(df)  # Initialize with None instead of 0
    for i in range(period, len(df)):  # Start from period, not 1
        if df["close"].iloc[i] > upperband.iloc[i - 1]:
            st[i] = lowerband.iloc[i]
        elif df["close"].iloc[i] < lowerband.iloc[i - 1]:
            st[i] = upperband.iloc[i]
        else:
            st[i] = st[i - 1] if st[i - 1] is not None else lowerband.iloc[i]
    return pd.Series(st)


# ---------------------- Master Function ----------------------
def compute_all_indicators(df):
    df["ema9"] = ema(df["close"], 9)
    df["ema21"] = ema(df["close"], 21)
    df["ema50"] = ema(df["close"], 50)
    df["ema200"] = ema(df["close"], 200)

    df["rsi14"] = rsi(df["close"])

    macd_line, signal_line, hist = macd(df["close"])
    df["macd"] = macd_line
    df["macd_signal"] = signal_line
    df["macd_hist"] = hist

    (
        df["bb_sma"],
        df["bb_upper"],
        df["bb_lower"],
        df["bb_width"],
        df["bb_percent"]
    ) = bollinger(df["close"])

    df["atr14"] = atr(df)

    df["supertrend"] = supertrend(df)

    return df
