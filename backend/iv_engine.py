def iv_trend(ce, pe):
    """
    Detect IV expansion/crush.
    """
    iv_now = (ce.get("impliedVolatility") or 0 + pe.get("impliedVolatility") or 0) / 2

    trend = "flat"
    score = 0

    if iv_now > 15:
        trend = "high"
        score += 1
    if iv_now < 12:
        trend = "low"
        score -= 1

    if iv_now > 14 and ce.get("changeinOpenInterest", 0) > 0:
        score += 1

    return {
        "iv": iv_now,
        "trend": trend,
        "score": score
    }
