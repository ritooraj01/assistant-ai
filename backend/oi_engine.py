def analyze_oi(ce, pe):
    # Validate inputs and provide fallback values
    if not ce or not isinstance(ce, dict):
        ce = {}
    if not pe or not isinstance(pe, dict):
        pe = {}
    
    ce_oi = ce.get("openInterest", 0) or 0
    pe_oi = pe.get("openInterest", 0) or 0

    ce_chg = ce.get("changeinOpenInterest", 0) or 0
    pe_chg = pe.get("changeinOpenInterest", 0) or 0

    # If no valid data, return neutral fallback
    if ce_oi == 0 and pe_oi == 0:
        return {
            "ce_chg": 0,
            "pe_chg": 0,
            "skew": 0,
            "sentiment": "Neutral - Data Unavailable",
            "score": 0,
            "pcr": 1.0
        }

    skew = ce_oi - pe_oi

    sentiment = "neutral"
    score = 0

    if ce_chg > 0 and pe_chg < 0:
        sentiment = "call buildup"
        score += 1

    if ce_chg < 0 and pe_chg > 0:
        sentiment = "put buildup"
        score -= 1

    if skew > 0:
        score += 0.5
    else:
        score -= 0.5

    # Calculate PCR (Put-Call Ratio)
    pcr = (pe_oi / ce_oi) if ce_oi > 0 else 1.0

    return {
        "ce_chg": ce_chg,
        "pe_chg": pe_chg,
        "skew": skew,
        "sentiment": sentiment,
        "score": score,
        "pcr": pcr
    }
