from nsepython import nsefetch
from data_validator import normalize_price_data

# -----------------------------------
# NSE Index Mapping for Each Sector
# -----------------------------------
SECTOR_INDICES = {
    "BANKS": "NIFTY BANK",
    "IT": "NIFTY IT",
    "PHARMA": "NIFTY PHARMA",
    "AUTO": "NIFTY AUTO",
    "FMCG": "NIFTY FMCG",
    "FINANCIAL": "NIFTY FIN SERVICE",

    # Newly added sectors
    "ENERGY": "NIFTY ENERGY",
    "METALS": "NIFTY METAL",
    "TELECOM": "NIFTY TELECOM",
    "INFRA_DIVERSIFIED": "NIFTY INFRASTRUCTURE",  # closest matching index
}

# -----------------------------------
# Key Stocks per Sector
# -----------------------------------
SECTOR_STOCKS = {
    "BANKS": [
        "HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK"
    ],
    "IT": [
        "TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "COFORGE"
    ],
    "PHARMA": [
        "SUNPHARMA", "DRREDDY", "CIPLA", "AUROPHARMA"
    ],
    "AUTO": [
        "M&M", "HEROMOTOCO"
    ],
    "FMCG": [
        "HINDUNILVR", "ITC", "NESTLEIND"
    ],
    "FINANCIAL": [
        "HDFCLIFE", "SBILIFE", "BAJFINANCE", "BAJAJFINSV"
    ],
    "ENERGY": [
        "RELIANCE", "ONGC", "NTPC", "POWERGRID"
    ],
    "INFRA_DIVERSIFIED": [
        "ADANIENT", "ADANIPORTS", "LT", "ULTRACEMCO"
    ],
}

# -----------------------------------
# Fetch sector moves from NSE
# -----------------------------------
def get_sector_index_changes():
    """
    Returns { sector: { index_name, last, change_pct } }
    Scans NSE /api/allIndices for movement.
    """
    url = "https://www.nseindia.com/api/allIndices"
    try:
        data = nsefetch(url)
    except Exception as exc:
        print(f"⚠️ Sector index fetch failed: {exc}")
        return {}
    out = {}

    for row in data.get("data", []):
        idx_name = row.get("index")
        last = row.get("last")
        prev = row.get("previousClose")

        if last is None or prev is None:
            continue

        for sector, nse_index in SECTOR_INDICES.items():
            if idx_name == nse_index:
                # Use validator to normalize and check for anomalies
                normalized = normalize_price_data(
                    last=float(last),
                    prev_close=float(prev) if prev else None,
                    symbol=f"{sector}_INDEX"
                )
                
                # Skip if no lastPrice (invalid data)
                if normalized["lastPrice"] is None:
                    print(f"⚠️ Skipping {sector}: {normalized['error']}")
                    continue
                
                out[sector] = {
                    "index_name": idx_name,
                    "last": normalized["lastPrice"],
                    "change_pct": normalized["pctChange"],
                    "pct_change_available": normalized["pctChangeAvailable"],
                    "anomaly": normalized["anomaly"]
                }

    return out


# -----------------------------------
# Sector scoring logic used by /api/signal_live
# -----------------------------------
def sector_score_for_symbol(symbol: str, action: str):
    """
    Scores how sector movements align with BUY/SELL signal.
    Returns:
      score ∈ [-1, 1]
      comments list
      raw sector changes
    """
    sector_changes = get_sector_index_changes()
    comments = []
    score = 0.0

    # Symbol-based relevance
    if symbol.upper() == "BANKNIFTY":
        relevant = ["BANKS", "FINANCIAL"]
    elif symbol.upper() == "NIFTY":
        # Broad-sector confirmation
        relevant = list(SECTOR_INDICES.keys())
    else:
        # fallback
        relevant = list(SECTOR_INDICES.keys())

    for sector in relevant:
        info = sector_changes.get(sector)
        if not info:
            continue

        chg = info["change_pct"]

        if action == "BUY":
            if chg > 0.5:
                score += 0.12
                comments.append(f"{info['index_name']} up {chg}% (supports buying).")
            elif chg < -0.5:
                score -= 0.12
                comments.append(f"{info['index_name']} down {chg}% (weakens long bias).")

        elif action == "SELL":
            if chg < -0.5:
                score += 0.12
                comments.append(f"{info['index_name']} down {chg}% (supports selling).")
            elif chg > 0.5:
                score -= 0.12
                comments.append(f"{info['index_name']} up {chg}% (weakens short bias).")

    # clamp to [-1, 1]
    score = max(min(score, 1.0), -1.0)

    return score, comments, sector_changes
