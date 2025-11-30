# backend/reversal_ai.py
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

def reversal_probability(df):
    """
    Approximate chance of near-term reversal using:
    - MACD hist flip
    - RSI turn
    - Wicks
    - BB squeeze
    """
    if len(df) < 3:
        return {"prob": 0.0, "reasons": ["Not enough data."]}

    last = df.iloc[-1].to_dict()
    prev = df.iloc[-2].to_dict()

    score = 0.0
    reasons = []

    # MACD flip
    prev_macd_hist = _safe_get(prev, "macd_hist")
    last_macd_hist = _safe_get(last, "macd_hist")
    if prev_macd_hist > 0 and last_macd_hist < 0:
        score += 0.3
        reasons.append("MACD histogram flipped from positive to negative.")
    if prev_macd_hist < 0 and last_macd_hist > 0:
        score += 0.3
        reasons.append("MACD histogram flipped from negative to positive.")

    # RSI turning
    prev_rsi = _safe_get(prev, "rsi14")
    last_rsi = _safe_get(last, "rsi14")
    if prev_rsi > 60 and last_rsi < 55:
        score += 0.2
        reasons.append("RSI falling from high area (possible top).")
    if prev_rsi < 40 and last_rsi > 45:
        score += 0.2
        reasons.append("RSI rising from low area (possible bottom).")

    # Candle wicks
    last_close = _safe_get(last, "close")
    last_open = _safe_get(last, "open")
    last_high = _safe_get(last, "high")
    last_low = _safe_get(last, "low")
    
    body = abs(last_close - last_open)
    rng = last_high - last_low + 1e-6
    upper_wick = last_high - max(last_open, last_close)
    lower_wick = min(last_open, last_close) - last_low

    if upper_wick > body * 1.5:
        score += 0.15
        reasons.append("Strong upper wick (rejection of higher prices).")
    if lower_wick > body * 1.5:
        score += 0.15
        reasons.append("Strong lower wick (rejection of lower prices).")

    # BB squeeze
    bb_width = _safe_get(last, "bb_width")
    if bb_width > 0 and last_close > 0:
        bbw_pct = (bb_width / last_close) * 100
        if bbw_pct < 0.5:
            score += 0.1
            reasons.append("Tight Bollinger Bands (squeeze → breakout risk).")

    # Clamp and convert to %
    score = max(0.0, min(score, 1.0))
    prob = round(score * 100)

    return {
        "prob": prob,
        "reasons": reasons
    }
