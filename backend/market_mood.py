def compute_market_mood(global_cues, news, vix, fii):
    score = 50  # neutral baseline

    # Global cues
    if global_cues:
        # Handle both old format [val, pct] and new format {"last": val, "change_pct": pct}
        nasdaq = global_cues.get("nasdaq", {})
        if isinstance(nasdaq, dict):
            ng = nasdaq.get("change_pct", 0) or 0
        else:
            ng = nasdaq[1] if len(nasdaq) > 1 else 0
        score += ng * 2  # Nasdaq impact
        
        nifty = global_cues.get("nifty_spot", {})
        if isinstance(nifty, dict):
            gf = nifty.get("change_pct", 0) or 0
        else:
            gf = nifty[1] if len(nifty) > 1 else 0
        score += gf * 3  # Gift Nifty / NIFTY spot

    # VIX
    if vix:
        if vix > 18:
            score -= 10
        elif vix < 14:
            score += 5

    # FII/DII
    if fii:
        flow = fii.get("fii_net", 0)
        if flow > 500:
            score += 8
        elif flow < -500:
            score -= 8

    # News sentiment
    if news:
        raw = news.get("sentiment_raw", 0)
        score += raw * 10  # scale

    # Clamp range and return as integer
    score = max(0, min(100, score))
    return int(round(score))
