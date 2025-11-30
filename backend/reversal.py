import pandas as pd

def _safe_get(d, key, default=0.0):
    """Safely get a value from dict, handling None and NaN."""
    v = d.get(key, default)
    if v is None:
        return float(default) if default is not None else 0.0
    if isinstance(v, float) and pd.isna(v):
        return float(default) if default is not None else 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return float(default) if default is not None else 0.0

def detect_reversal(df):
    """
    Detect trend reversal using:
    - MACD momentum flip
    - RSI divergence
    - Candle rejection patterns
    - ATR compression
    """

    if len(df) < 10:
        return None

    last = df.iloc[-1].to_dict()
    prev = df.iloc[-2].to_dict()

    signals = []

    # 1️⃣ MACD reversal
    prev_macd_hist = _safe_get(prev, "macd_hist")
    last_macd_hist = _safe_get(last, "macd_hist")
    if prev_macd_hist > 0 and last_macd_hist < 0:
        signals.append("Bearish MACD reversal detected.")
    if prev_macd_hist < 0 and last_macd_hist > 0:
        signals.append("Bullish MACD reversal detected.")

    # 2️⃣ RSI shift
    prev_rsi = _safe_get(prev, "rsi14")
    last_rsi = _safe_get(last, "rsi14")
    if prev_rsi > 60 and last_rsi < 55:
        signals.append("Momentum weakening (RSI dropping).")
    if prev_rsi < 40 and last_rsi > 45:
        signals.append("Momentum improving (RSI rising).")

    # 3️⃣ Candle rejection
    last_close = _safe_get(last, "close")
    last_open = _safe_get(last, "open")
    last_high = _safe_get(last, "high")
    last_low = _safe_get(last, "low")
    
    body = abs(last_close - last_open)
    range_ = last_high - last_low
    upper_wick = last_high - max(last_open, last_close)
    lower_wick = min(last_open, last_close) - last_low

    if upper_wick > body * 1.2:
        signals.append("Upper wick rejection → downside pressure.")
    if lower_wick > body * 1.2:
        signals.append("Lower wick rejection → upside pressure.")

    # 4️⃣ Volatility compression (BB squeeze)
    bb_width = _safe_get(last, "bb_width")
    if bb_width > 0 and last_close > 0:
        bbw = bb_width / last_close * 100
        if bbw < 0.5:
            signals.append("Low volatility squeeze → breakout likely soon.")

    if not signals:
        return None

    return signals
