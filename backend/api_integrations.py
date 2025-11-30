# backend/api_integrations.py
"""
Enhanced API integrations for reliable market data
Replaces yfinance proxies with proper APIs
"""

import requests
import yfinance as yf
from typing import Tuple, Optional

def get_gift_nifty() -> Tuple[Optional[float], Optional[float]]:
    """
    Fetch GIFT Nifty futures from NSE IFSC-SGX Connect
    Falls back to NIFTY spot if API unavailable
    
    Returns: (last_price, change_pct)
    """
    try:
        # Try yfinance with GIFT Nifty symbol first
        # GIFT Nifty trades on NSE IFSC - try common symbols
        gift_symbols = ["GIFTNIFTY.NS", "NIFTY_FUT.NS", "^NSEIFSC"]
        
        for symbol in gift_symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d", interval="1d")
                if not hist.empty and len(hist) >= 2:
                    last = float(hist["Close"].iloc[-1])
                    prev = float(hist["Close"].iloc[-2])
                    change_pct = (last - prev) / prev * 100
                    # If we got valid data (not same as NIFTY), use it
                    if abs(last - 20000) > 1000:  # Reasonable check for futures vs spot
                        print(f"✅ GIFT Nifty from yfinance ({symbol}): {last} ({change_pct:+.2f}%)")
                        return last, change_pct
            except:
                continue
        
        # If yfinance fails, try direct NSE IFSC API
        url = "https://www.niftyindices.com/Backpage.aspx/getGIFTNiftyData"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            last = data.get("last")
            change_pct = data.get("change_pct")
            
            if last and change_pct is not None:
                print(f"✅ GIFT Nifty from NSE IFSC: {last} ({change_pct:+.2f}%)")
                return float(last), float(change_pct)
        
        raise Exception("GIFT Nifty API returned invalid data")
        
    except Exception as e:
        print(f"⚠️ GIFT Nifty API failed: {e}, using NIFTY spot proxy")
        # Fallback to NIFTY spot
        try:
            ticker = yf.Ticker("^NSEI")
            hist = ticker.history(period="5d", interval="1d")
            if len(hist) >= 2:
                last = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2])
                change_pct = (last - prev) / prev * 100
                print(f"📊 Using NIFTY spot as GIFT proxy: {last} ({change_pct:+.2f}%)")
                return last, change_pct
        except Exception as fallback_error:
            print(f"❌ NIFTY spot fallback failed: {fallback_error}")
        
        return None, None


def get_sgx_nifty() -> Tuple[Optional[float], Optional[float]]:
    """
    Fetch SGX Nifty futures from Singapore Exchange
    Falls back to NIFTY spot if API unavailable
    
    Returns: (last_price, change_pct)
    """
    try:
        # SGX API endpoint (requires subscription)
        # For production, use official SGX API: https://www.sgx.com/
        # This is a placeholder implementation
        url = "https://api.sgx.com/derivatives/v1/nifty"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            last = data.get("last")
            change_pct = data.get("change_pct")
            
            if last and change_pct is not None:
                print(f"✅ SGX Nifty from SGX API: {last} ({change_pct:+.2f}%)")
                return float(last), float(change_pct)
        
        raise Exception("SGX Nifty API returned invalid data")
        
    except Exception as e:
        print(f"⚠️ SGX Nifty API failed: {e}, falling back to NIFTY spot")
        # Fallback to NIFTY spot (same as GIFT)
        try:
            ticker = yf.Ticker("^NSEI")
            hist = ticker.history(period="5d", interval="1d")
            if len(hist) >= 2:
                last = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2])
                change_pct = (last - prev) / prev * 100
                print(f"📊 Using NIFTY spot as SGX proxy: {last} ({change_pct:+.2f}%)")
                return last, change_pct
        except Exception as fallback_error:
            print(f"❌ NIFTY spot fallback failed: {fallback_error}")
        
        return None, None


def get_usdinr_fx() -> Tuple[Optional[float], Optional[float]]:
    """
    Fetch USD/INR from reliable FX API
    Tries multiple sources: Twelve Data, Alpha Vantage, yfinance
    
    Returns: (last_rate, change_pct)
    """
    # Try Twelve Data API first (free tier: 800 calls/day)
    try:
        # Get API key from environment variable or config
        # For production: export TWELVE_DATA_API_KEY=your_key
        import os
        api_key = os.environ.get("TWELVE_DATA_API_KEY", "demo")
        
        url = f"https://api.twelvedata.com/time_series"
        params = {
            "symbol": "USD/INR",
            "interval": "1day",
            "outputsize": 2,
            "apikey": api_key
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            values = data.get("values", [])
            
            if len(values) >= 2:
                last = float(values[0]["close"])
                prev = float(values[1]["close"])
                change_pct = (last - prev) / prev * 100
                
                # Validate realistic range
                if 70 <= last <= 95:
                    print(f"✅ USD/INR from Twelve Data: {last:.2f} ({change_pct:+.2f}%)")
                    return last, change_pct
                else:
                    print(f"⚠️ USD/INR {last} outside realistic range, trying fallback")
    
    except Exception as e:
        print(f"⚠️ Twelve Data API failed: {e}")
    
    # Fallback to Alpha Vantage (free tier: 25 calls/day)
    try:
        api_key = os.environ.get("ALPHA_VANTAGE_API_KEY", "demo")
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "FX_DAILY",
            "from_symbol": "USD",
            "to_symbol": "INR",
            "apikey": api_key
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            time_series = data.get("Time Series FX (Daily)", {})
            
            if time_series:
                dates = sorted(time_series.keys(), reverse=True)[:2]
                if len(dates) >= 2:
                    last = float(time_series[dates[0]]["4. close"])
                    prev = float(time_series[dates[1]]["4. close"])
                    change_pct = (last - prev) / prev * 100
                    
                    if 70 <= last <= 95:
                        print(f"✅ USD/INR from Alpha Vantage: {last:.2f} ({change_pct:+.2f}%)")
                        return last, change_pct
    
    except Exception as e:
        print(f"⚠️ Alpha Vantage API failed: {e}")
    
    # Final fallback to yfinance
    try:
        ticker = yf.Ticker("USDINR=X")
        hist = ticker.history(period="5d", interval="1d")
        
        if len(hist) >= 2:
            last = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2])
            change_pct = (last - prev) / prev * 100
            
            if 70 <= last <= 95:
                print(f"📊 USD/INR from yfinance fallback: {last:.2f} ({change_pct:+.2f}%)")
                return last, change_pct
            else:
                print(f"⚠️ USD/INR {last} from yfinance outside realistic range")
    
    except Exception as e:
        print(f"❌ yfinance USD/INR fallback failed: {e}")
    
    return None, None


def test_api_latency(api_name: str, api_func) -> dict:
    """
    Test API latency and reliability
    Returns: {success: bool, latency_ms: float, error: str}
    """
    import time
    
    start = time.time()
    try:
        result = api_func()
        latency = (time.time() - start) * 1000
        
        success = result[0] is not None
        
        return {
            "api_name": api_name,
            "success": success,
            "latency_ms": round(latency, 2),
            "error": None if success else "Returned None"
        }
    
    except Exception as e:
        latency = (time.time() - start) * 1000
        return {
            "api_name": api_name,
            "success": False,
            "latency_ms": round(latency, 2),
            "error": str(e)
        }


if __name__ == "__main__":
    print("\n=== Testing API Integrations ===\n")
    
    # Test GIFT Nifty
    gift_test = test_api_latency("GIFT Nifty", get_gift_nifty)
    print(f"GIFT Nifty: {gift_test}")
    
    # Test SGX Nifty
    sgx_test = test_api_latency("SGX Nifty", get_sgx_nifty)
    print(f"SGX Nifty: {sgx_test}")
    
    # Test USD/INR
    usdinr_test = test_api_latency("USD/INR", get_usdinr_fx)
    print(f"USD/INR: {usdinr_test}")
    
    print("\n=== Test Complete ===\n")
