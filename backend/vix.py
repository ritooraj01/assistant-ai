import yfinance as yf

def get_india_vix():
    try:
        data = yf.Ticker("^INDIAVIX").history(period="2d", interval="1d")
        if data.empty:
            return None
        return float(data["Close"].iloc[-1])
    except Exception:
        return None

def vix_risk_level(vix):
    """
    Classify VIX into: low, medium, high volatility regime.
    Returns (risk_score, label, comment)
    risk_score: 0..1
    """
    if vix is None:
        return 0.2, "Unknown", "Unable to fetch VIX."

    if vix < 12:
        return 0.2, "Low", "Low volatility – signals are more reliable."
    elif vix < 18:
        return 0.5, "Medium", "Volatility moderate – good for intraday."
    else:
        return 0.9, "High", "High VIX – expect whipsaws & false breakouts."
