import math
import pandas as pd

def _safe_get(d, key, default=0.0):
    v = d.get(key, default)
    # Handle None values
    if v is None:
        return float(default) if default is not None else 0.0
    # Handle NaN values
    if isinstance(v, float) and pd.isna(v):
        return float(default) if default is not None else 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return float(default) if default is not None else 0.0


def _trend_score(row):
    """
    Score overall trend strength in [-1, 1].
    +1 = strong uptrend, -1 = strong downtrend
    """
    close = _safe_get(row, "close")
    ema9 = _safe_get(row, "ema9", close)
    ema21 = _safe_get(row, "ema21", close)
    ema50 = _safe_get(row, "ema50", close)
    ema200 = _safe_get(row, "ema200", ema50)
    supertrend = _safe_get(row, "supertrend", close)

    score = 0.0
    reasons = []

    # EMA alignment
    if close > ema9 > ema21 > ema50 > ema200:
        score += 0.7
        reasons.append("Strong EMA uptrend (close > EMA9 > EMA21 > EMA50 > EMA200).")
    elif close < ema9 < ema21 < ema50 < ema200:
        score -= 0.7
        reasons.append("Strong EMA downtrend (close < EMA9 < EMA21 < EMA50 < EMA200).")
    else:
        if close > ema21 and ema21 > ema50:
            score += 0.3
            reasons.append("Price above EMA21 and EMA21 > EMA50 (moderate uptrend).")
        elif close < ema21 and ema21 < ema50:
            score -= 0.3
            reasons.append("Price below EMA21 and EMA21 < EMA50 (moderate downtrend).")

    # Supertrend confirmation
    if supertrend != 0:
        if close > supertrend:
            score += 0.2
            reasons.append("Price above Supertrend (trend bullish).")
        elif close < supertrend:
            score -= 0.2
            reasons.append("Price below Supertrend (trend bearish).")

    # Clamp
    score = max(min(score, 1.0), -1.0)
    return score, reasons


def _momentum_score(row):
    """
    Score momentum & mean-reversion in [-1, 1] using RSI + MACD.
    """
    rsi = _safe_get(row, "rsi14")
    macd = _safe_get(row, "macd")
    macd_signal = _safe_get(row, "macd_signal")
    macd_hist = _safe_get(row, "macd_hist")

    score = 0.0
    reasons = []

    # RSI zones (skip if invalid data)
    if rsi > 0:  # RSI must be > 0 to be valid
        if rsi > 70:
            score += 0.2  # strong momentum but also near overbought
            reasons.append(f"RSI {rsi:.1f} (strong bullish momentum, but near overbought).")
        elif rsi > 55:
            score += 0.4
            reasons.append(f"RSI {rsi:.1f} (healthy bullish momentum).")
        elif rsi < 30:
            score -= 0.2
            reasons.append(f"RSI {rsi:.1f} (strong bearish momentum, but near oversold).")
        elif rsi < 45:
            score -= 0.4
            reasons.append(f"RSI {rsi:.1f} (healthy bearish momentum).")
        else:
            reasons.append(f"RSI {rsi:.1f} (neutral).")
    else:
        reasons.append("RSI data unavailable (insufficient candles).")

    # MACD cross
    if macd > macd_signal and macd_hist > 0:
        score += 0.3
        reasons.append("MACD above Signal with positive histogram (bullish momentum).")
    elif macd < macd_signal and macd_hist < 0:
        score -= 0.3
        reasons.append("MACD below Signal with negative histogram (bearish momentum).")

    score = max(min(score, 1.0), -1.0)
    return score, reasons


def _volatility_quality(row):
    """
    Score whether volatility is tradeable:
    0..1 where 1 = good volatility, 0 = dead or too chaotic.
    """
    atr = _safe_get(row, "atr14")
    bb_width = _safe_get(row, "bb_width")
    close = _safe_get(row, "close")

    if close <= 0:
        return 0.5, ["Price data invalid."]

    atr_pct = (atr / close) * 100.0
    bbw_pct = (bb_width / close) * 100.0

    score = 0.5
    reasons = []

    # ATR-based filtering (skip if invalid)
    if atr > 0:  # ATR must be > 0 to be valid
        if atr_pct < 0.2:
            score -= 0.3
            reasons.append("ATR too low (very low volatility, moves may be noisy).")
        elif atr_pct > 2.0:
            score -= 0.2
            reasons.append("ATR very high (wild swings, risk of whipsaws).")
        else:
            score += 0.2
            reasons.append("ATR in normal range (volatility acceptable).")
    else:
        reasons.append("ATR data unavailable (insufficient candles).")

    # Bollinger Band width
    if bbw_pct < 0.5:
        score -= 0.2
        reasons.append("Bollinger Bands very tight (squeeze / no clear direction).")
    elif bbw_pct > 5.0:
        score -= 0.1
        reasons.append("Bollinger Bands extremely wide (high volatility regime).")
    else:
        score += 0.1
        reasons.append("Bollinger Bands in normal range.")

    score = max(min(score, 1.0), 0.0)
    return score, reasons


def _candle_quality(row):
    """
    Basic candle structure check:
    - large body vs wick → strong conviction
    - long upper wick in uptrend → possible selling pressure
    - long lower wick in downtrend → possible buying pressure
    Score in [-1, 1].
    """
    o = _safe_get(row, "open", row.get("close", 0))
    h = _safe_get(row, "high", row.get("close", 0))
    l = _safe_get(row, "low", row.get("close", 0))
    c = _safe_get(row, "close")

    body = abs(c - o)
    range_ = max(h - l, 1e-6)

    upper_wick = h - max(c, o)
    lower_wick = min(c, o) - l

    score = 0.0
    reasons = []

    body_ratio = body / range_

    # Strong conviction candles
    if body_ratio > 0.6:
        if c > o:
            score += 0.3
            reasons.append("Strong bullish candle (large body, small wicks).")
        else:
            score -= 0.3
            reasons.append("Strong bearish candle (large body, small wicks).")

    # Long wicks → indecision/fake moves
    if upper_wick > body * 1.5:
        score -= 0.2
        reasons.append("Long upper wick (selling pressure / possible fake breakout).")
    if lower_wick > body * 1.5:
        score += 0.2
        reasons.append("Long lower wick (buying support / rejection of lows).")

    score = max(min(score, 1.0), -1.0)
    return score, reasons


def decide_signal(row: dict, ml_pred: dict = None):
    """
    Main decision engine for BUY / SELL / WAIT.

    Inputs: last candle row as dict with keys
        close, open, high, low,
        ema9, ema21, ema50, ema200,
        rsi14, macd, macd_signal, macd_hist,
        atr14, bb_width, supertrend
        
        ml_pred: optional ML prediction dict with final_ml_score

    Output:
        {
          "action": "BUY"/"SELL"/"WAIT",
          "confidence": 0..1,
          "bullish_score": 0..1,
          "bearish_score": 0..1,
          "reasons": [...],
        }
    """
    trend_s, trend_reasons = _trend_score(row)
    mom_s, mom_reasons = _momentum_score(row)
    vol_q, vol_reasons = _volatility_quality(row)
    candle_s, candle_reasons = _candle_quality(row)

    reasons = []
    reasons.extend(trend_reasons)
    reasons.extend(mom_reasons)
    reasons.extend(vol_reasons)
    reasons.extend(candle_reasons)

    # Extract ML score at the top
    ml_score = None
    if ml_pred and isinstance(ml_pred, dict) and ml_pred.get("enabled") != False:
        ml_score = ml_pred.get("final_ml_score")

    # Combine directional scores
    directional = 0.5 * trend_s + 0.3 * mom_s + 0.2 * candle_s
    # -1..1
    bullish_score = max(directional, 0.0)
    bearish_score = max(-directional, 0.0)
    
    # --- ML Score Influence (continuation confirmation) ---
    if ml_score is not None:
        # If ML is strongly predicting uptrend
        if ml_score > 0.65:
            bullish_score += 0.15
            reasons.append("ML confirms upward continuation.")
        elif ml_score < 0.35:
            bearish_score += 0.15
            reasons.append("ML confirms downward continuation.")
    
    # Clamp scores after ML influence
    bullish_score = min(bullish_score, 1.0)
    bearish_score = min(bearish_score, 1.0)

    # Base confidence from direction + quality of volatility
    base_conf = (abs(directional) * 0.7) + (vol_q * 0.3)
    # Clamp 0..1
    base_conf = max(min(base_conf, 1.0), 0.0)

    # --- High Volatility Check ---
    atr14 = _safe_get(row, "atr14")
    close = _safe_get(row, "close")
    if atr14 > 0 and close > 0 and atr14 > close * 0.01:
        reasons.append("High volatility regime — risky zone")
        base_conf -= 0.15
        base_conf = max(base_conf, 0.0)  # Ensure non-negative

    # --- Entry Logic Booster ---
    # Entry filter: pullback in uptrend
    if bullish_score > 0.5:
        ema9 = _safe_get(row, "ema9")
        if close > 0 and ema9 > 0 and close < ema9:
            reasons.append("Pullback entry zone within uptrend (good risk/reward).")
    
    # Exit warning
    if bearish_score > 0.5 and row["close"] > row["ema9"]:
        reasons.append("Possible pullback against bearish trend; delay entry.")

    # --- CHOP ZONE DETECTOR (No trade) ---
    ema_diff = abs(row["ema9"] - row["ema21"])
    if ema_diff < row["close"] * 0.0004:  # very small spread
        reasons.append("Sideways / low-trend zone")
        return {
            "action": "WAIT",
            "confidence": 0.1,
            "bullish_score": round(bullish_score, 2),
            "bearish_score": round(bearish_score, 2),
            "reasons": reasons,
        }

    # Decide action
    if bullish_score > 0.4 and base_conf > 0.55:
        action = "BUY"
    elif bearish_score > 0.4 and base_conf > 0.55:
        action = "SELL"
    else:
        action = "WAIT"

    # If volatility terrible, force WAIT
    if vol_q < 0.3 and base_conf < 0.7:
        action = "WAIT"
        reasons.append("Volatility conditions are not ideal; forcing WAIT.")

    # If directional signal weak, force WAIT
    if abs(directional) < 0.25:
        action = "WAIT"
        reasons.append("Directional strength weak; no clear edge.")

    # Final confidence: if WAIT, downscale
    if action == "WAIT":
        confidence = min(base_conf, 0.4)
    else:
        confidence = base_conf

    return {
        "action": action,
        "confidence": round(confidence, 2),
        "bullish_score": round(bullish_score, 2),
        "bearish_score": round(bearish_score, 2),
        "reasons": reasons,
    }
