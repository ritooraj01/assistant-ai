from nsepython import nsefetch, nse_quote_ltp
import yfinance as yf

def get_nse_spot_price(symbol: str) -> float:
    """
    Fetch live NSE spot price for indices or stocks.
    Supports: NIFTY, BANKNIFTY, FINNIFTY, MIDCAP, SENSEX (indices)
    And all NSE stocks (e.g., RELIANCE, HDFCBANK, TCS, etc.)
    """
    symbol_upper = symbol.upper()
    
    # Check if it's an index
    index_map = {
        "NIFTY": "NIFTY 50",
        "NIFTY50": "NIFTY 50",
        "BANKNIFTY": "NIFTY BANK",
        "FINNIFTY": "NIFTY FIN SERVICE",
        "MIDCAP": "NIFTY MIDCAP 100",
        "SENSEX": "SENSEX"
    }

    # If it's an index, fetch from allIndices API
    if symbol_upper in index_map:
        index_name = index_map[symbol_upper]
        try:
            url = "https://www.nseindia.com/api/allIndices"
            data = nsefetch(url)
            for index in data["data"]:
                if index["index"] == index_name:
                    return float(index["last"])
            print(f"⚠️ Index {index_name} not found, trying yfinance fallback")
        except Exception as e:
            print(f"⚠️ NSE API error for {symbol}: {e}, trying yfinance fallback")
    
    # If it's a stock, fetch using nse_quote_ltp
    try:
        price = nse_quote_ltp(symbol_upper)
        if price and price > 0:
            print(f"✅ NSE live price for {symbol_upper}: ₹{price}")
            return float(price)
        else:
            print(f"⚠️ Invalid NSE price for {symbol_upper}: {price}, trying yfinance")
    except Exception as e:
        print(f"⚠️ NSE API error for stock {symbol_upper}: {e}, trying yfinance")
    
    # Fallback to yfinance (1-minute delayed data)
    try:
        ticker_symbol = f"{symbol_upper}.NS" if not symbol_upper.startswith("^") else symbol_upper
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="1d", interval="1m")
        if not hist.empty:
            price = float(hist['Close'].iloc[-1])
            print(f"📊 yfinance fallback price for {symbol_upper}: ₹{price}")
            return price
        else:
            print(f"❌ No yfinance data for {symbol_upper}, returning 0")
            return 0.0
    except Exception as e:
        print(f"❌ yfinance fallback failed for {symbol_upper}: {e}")
        return 0.0
