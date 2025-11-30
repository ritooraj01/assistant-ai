import yfinance as yf
from api_integrations import get_gift_nifty, get_sgx_nifty, get_usdinr_fx
from data_validator import validate_forex_rate

def _last_and_change(ticker: str):
    """
    Return (last_price, pct_change_today) for ticker.
    pct_change_today is % vs previous close.
    """
    try:
        data = yf.Ticker(ticker).history(period="5d", interval="1d")
        if data.empty:
            return None, None
        
        # Flatten MultiIndex columns if they exist
        if hasattr(data.columns, 'levels'):
            data.columns = data.columns.get_level_values(0)
        
        if len(data) < 2:
            # Only 1 day of data - return last price with no change
            last = float(data["Close"].iloc[-1])
            return last, 0.0
        
        prev = float(data["Close"].iloc[-2])
        last = float(data["Close"].iloc[-1])
        
        if prev == 0:
            return last, 0.0
        
        change_pct = (last - prev) / prev * 100.0
        return last, change_pct
    except Exception as e:
        print(f"⚠️ Failed to fetch {ticker}: {e}")
        return None, None


def get_global_cues():
    """
    Get global markets relevant to India:
      - NIFTY spot                                 -> ^NSEI
      - GIFT Nifty (NSE IFSC-SGX API)             -> Dedicated futures feed
      - SGX Nifty (SGX API)                        -> Singapore futures feed
      - Nasdaq 100                                 -> ^NDX
      - Crude oil                                  -> CL=F
      - USDINR (Twelve Data / Alpha Vantage)       -> Multi-source FX feed
    Returns dict with last + change_pct for each.
    """
    nifty_last, nifty_chg = _last_and_change("^NSEI")
    nasdaq_last, nasdaq_chg = _last_and_change("^NDX")
    crude_last, crude_chg = _last_and_change("CL=F")
    
    # Use dedicated API integrations
    gift_last, gift_chg = get_gift_nifty()
    sgx_last, sgx_chg = get_sgx_nifty()
    usdinr_last, usdinr_chg = get_usdinr_fx()
    
    # Validate USD/INR with proper range checking (70-95)
    usdinr_valid, validated_usdinr, usdinr_error = validate_forex_rate(usdinr_last, "USDINR")
    usdinr_pct_available = usdinr_valid  # Only show % if within valid range
    
    if not usdinr_valid:
        print(f"⚠️ USD/INR validation failed: {usdinr_error}")
        # Still send lastPrice, but mark pctChangeAvailable = false
        validated_usdinr = usdinr_last if usdinr_last else None
        usdinr_chg = None
    
    # Check if GIFT/SGX are actually mirroring NIFTY (proxy fallback active)
    gift_is_proxy = (gift_last == nifty_last) if (gift_last and nifty_last) else False
    sgx_is_proxy = (sgx_last == nifty_last) if (sgx_last and nifty_last) else False
    
    if gift_is_proxy:
        print(f"⚠️ GIFT Nifty mirroring NIFTY spot - using proxy fallback")
    if sgx_is_proxy:
        print(f"⚠️ SGX Nifty mirroring NIFTY spot - using proxy fallback")

    return {
        "nifty_spot": {
            "last": nifty_last,
            "change_pct": nifty_chg,
            "pct_change_available": (nifty_last is not None and nifty_chg is not None)
        },
        "gift_nifty": {
            "last": gift_last,
            "change_pct": gift_chg,
            "pct_change_available": (gift_last is not None and gift_chg is not None),
            "proxy": gift_is_proxy  # Mark as proxy until distinct feed
        },
        "sgx_nifty": {
            "last": sgx_last,
            "change_pct": sgx_chg,
            "pct_change_available": (sgx_last is not None and sgx_chg is not None),
            "proxy": sgx_is_proxy  # Mark as proxy until distinct feed
        },
        "nasdaq": {
            "last": nasdaq_last,
            "change_pct": nasdaq_chg,
            "pct_change_available": (nasdaq_last is not None and nasdaq_chg is not None)
        },
        "crude": {
            "last": crude_last,
            "change_pct": crude_chg,
            "pct_change_available": (crude_last is not None and crude_chg is not None)
        },
        "usdinr": {
            "last": validated_usdinr,
            "change_pct": usdinr_chg,
            "pct_change_available": usdinr_pct_available,
            "quality_warning": not usdinr_valid
        },
    }


def compute_global_bias(global_data: dict):
    """
    Convert global % changes into a bias score [-1..1] and comments.
    Positive score = bullish bias for India.
    """

    score = 0.0
    comments: list[str] = []

    nifty = global_data["nifty_spot"]
    nasdaq = global_data["nasdaq"]
    crude = global_data["crude"]
    usdinr = global_data["usdinr"]

    # --- NIFTY spot ---
    if nifty["change_pct"] is not None:
        chg = nifty["change_pct"]
        if chg > 0.5:
            score += 0.3
            comments.append(f"Nifty spot up {chg:.2f}% (supports bullish bias).")
        elif chg < -0.5:
            score -= 0.3
            comments.append(f"Nifty spot down {chg:.2f}% (supports bearish bias).")

    # --- Nasdaq (IT correlation) ---
    if nasdaq["change_pct"] is not None:
        chg = nasdaq["change_pct"]
        if chg > 0.7:
            score += 0.2
            comments.append(f"Nasdaq up {chg:.2f}% (positive for Indian IT).")
        elif chg < -0.7:
            score -= 0.2
            comments.append(f"Nasdaq down {chg:.2f}% (negative for Indian IT).")

    # --- Crude oil (inflation risk for India) ---
    if crude["last"] is not None:
        crude_px = crude["last"]
        if crude_px > 90:
            score -= 0.25
            comments.append("Crude oil > 90$ (inflation risk, negative for India).")
        elif crude_px < 80:
            score += 0.1
            comments.append("Crude oil below 80$ (supportive for India).")

    # --- USDINR (currency pressure) ---
    if usdinr["last"] is not None:
        fx = usdinr["last"]
        if fx > 84:
            score -= 0.2
            comments.append("USDINR high (pressure on INR, risk-off).")
        elif fx < 83:
            score += 0.1
            comments.append("USDINR stable (ok for IT/exports).")

    # clamp
    score = max(min(score, 1.0), -1.0)
    return score, comments
