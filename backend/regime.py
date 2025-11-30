# backend/regime.py

def detect_regime(row: dict, ml_trend: str | None = None):
    """
    Classify current regime: Trending / Sideways / Volatile / Dead
    """
    close = float(row.get("close", 0) or 0)
    atr14 = float(row.get("atr14", 0) or 0)
    bb_width = float(row.get("bb_width", 0) or 0)

    if close <= 0:
        return {"label": "Unknown", "score": 0.0}

    atr_pct = (atr14 / close) * 100
    bb_pct = (bb_width / close) * 100

    score = 0.0
    label = "Sideways"

    # Volatility component
    if atr_pct < 0.5 and bb_pct < 1.0:
        label = "Low Volatility"
        score = -0.3
    elif atr_pct > 1.5 and bb_pct > 3.5:
        label = "High Volatility"
        score = 0.2
    else:
        label = "Normal Volatility"
        score = 0.0

    # ML trend influence
    if ml_trend:
        if "Strong Bullish" in ml_trend or "Strong Bearish" in ml_trend:
            score += 0.4
            label = "Trending"
        elif "Bullish" in ml_trend or "Bearish" in ml_trend:
            score += 0.2

    # Clamp
    score = max(min(score, 1.0), -1.0)

    return {
        "label": label,
        "score": round(score, 2),
        "atr_pct": round(atr_pct, 2),
        "bb_pct": round(bb_pct, 2),
    }
