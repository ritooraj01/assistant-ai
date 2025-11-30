import requests

def get_fii_dii_trend():
    """
    Fetch NSE FII/DII cash market data.
    """
    url = "https://www.nseindia.com/api/fiidiiCashFlow"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        data = requests.get(url, headers=headers, timeout=8).json()
    except:
        return (0, "Unknown", "Could not fetch FII/DII data.")

    if "data" not in data or not data["data"]:
        return (0, "Unknown", "No data available.")

    last = data["data"][-1]

    fii = float(last["FII"])
    dii = float(last["DII"])

    comments = []
    score = 0.0

    if fii > 0:
        score += 0.3
        comments.append("FII are net buyers (supports bullish bias).")
    else:
        score -= 0.3
        comments.append("FII are net sellers (supports bearish bias).")

    if dii > 0:
        score += 0.1
        comments.append("DII buying provides support.")
    else:
        score -= 0.1
        comments.append("DII selling adds to weakness.")

    # clamp
    score = max(min(score, 1), -1)

    label = "Bullish" if score > 0 else "Bearish"

    return score, label, comments
