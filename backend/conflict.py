def resolve_conflicts(signal, ml, indicators, mood, sector):
    """
    Adjust BUY/SELL/WAIT action if conflicting conditions appear.
    """

    base = signal["action"]
    reasons = signal["reasons"]

    ml_up = ml.get("next_1_up", 0)
    ml_down = 1 - ml_up
    sector_score = sector.get("sector_score", 0)
    market_mood = mood

    # ----------------------------
    # RULE 1: Technical BUY but ML bearish → WAIT
    # ----------------------------
    if base == "BUY" and ml_up < 0.45:
        reasons.append("ML contradicts BUY → switching to WAIT")
        return "WAIT", reasons

    # ----------------------------
    # RULE 2: Technical SELL but ML bullish → WAIT
    # ----------------------------
    if base == "SELL" and ml_up > 0.55:
        reasons.append("ML contradicts SELL → switching to WAIT")
        return "WAIT", reasons

    # ----------------------------
    # RULE 3: Market mood bad but BUY → WAIT
    # ----------------------------
    if base == "BUY" and market_mood < 40:
        reasons.append("Market mood too weak for BUY → WAIT")
        return "WAIT", reasons

    # ----------------------------
    # RULE 4: Sector against trade
    # ----------------------------
    if base == "BUY" and sector_score < -0.3:
        reasons.append("Sector not supporting the trade → WAIT")
        return "WAIT", reasons

    if base == "SELL" and sector_score > 0.3:
        reasons.append("Sector contradicts SELL → WAIT")
        return "WAIT", reasons

    # ----------------------------
    # RULE 5: Multi-Timeframe Trend Conflict
    # ----------------------------
    mtf = signal.get("mtf", {})
    
    if base == "BUY" and mtf.get("tf15") == -1:
        reasons.append("15m trend bearish → WAIT")
        return "WAIT", reasons

    if base == "SELL" and mtf.get("tf15") == 1:
        reasons.append("15m trend bullish → WAIT")
        return "WAIT", reasons

    # ----------------------------
    # RULE 6: Perfect alignment → Strong BUY / Strong SELL
    # ----------------------------
    if base == "BUY" and ml_up > 0.70 and market_mood > 65 and sector_score > 0.2:
        reasons.append("Perfect confluence → STRONG BUY")
        return "STRONG BUY", reasons

    if base == "SELL" and ml_down > 0.70 and market_mood < 35 and sector_score < -0.2:
        reasons.append("Perfect confluence → STRONG SELL")
        return "STRONG SELL", reasons

    return base, reasons
