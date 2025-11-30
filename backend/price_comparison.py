#!/usr/bin/env python3
"""
Price Comparison Tool
Compares prices from Trading Assistant App vs Yahoo Finance
"""
import yfinance as yf
import requests
from datetime import datetime
from tabulate import tabulate

# Stock symbols to check
STOCKS = [
    ('NIFTY', '^NSEI'),
    ('HDFCBANK', 'HDFCBANK.NS'),
    ('RELIANCE', 'RELIANCE.NS'),
    ('ICICIBANK', 'ICICIBANK.NS'),
    ('INFY', 'INFY.NS'),
    ('TCS', 'TCS.NS'),
]

API_BASE = "http://127.0.0.1:8000"

def get_app_price(symbol):
    """Get price from trading assistant app"""
    try:
        response = requests.get(f"{API_BASE}/api/signal_live?symbol={symbol}&interval=5&limit=10", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('price', 'N/A')
        return "API ERROR"
    except Exception as e:
        return f"ERROR: {str(e)[:20]}"

def get_yahoo_price(ticker):
    """Get latest price from Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d", interval="1m")
        if not hist.empty:
            return round(hist['Close'].iloc[-1], 2)
        return "NO DATA"
    except Exception as e:
        return f"ERROR: {str(e)[:20]}"

def main():
    print("\n" + "="*70)
    print(" PRICE COMPARISON: Trading Assistant App vs Yahoo Finance")
    print("="*70 + "\n")
    
    results = []
    for name, ticker in STOCKS:
        print(f"Fetching {name}...", end='\r')
        
        app_price = get_app_price(name)
        yahoo_price = get_yahoo_price(ticker)
        
        # Calculate difference
        if isinstance(app_price, (int, float)) and isinstance(yahoo_price, (int, float)):
            diff = app_price - yahoo_price
            diff_pct = (diff / yahoo_price) * 100 if yahoo_price != 0 else 0
            diff_str = f"{diff:+.2f} ({diff_pct:+.2f}%)"
            match = "✅ MATCH" if abs(diff_pct) < 0.1 else "⚠️ DIFF"
        else:
            diff_str = "N/A"
            match = "❌ ERROR"
        
        results.append([
            name,
            f"₹{app_price}" if isinstance(app_price, (int, float)) else app_price,
            f"₹{yahoo_price}" if isinstance(yahoo_price, (int, float)) else yahoo_price,
            diff_str,
            match
        ])
    
    print(" " * 50, end='\r')  # Clear the fetching message
    
    headers = ["Symbol", "App Price", "Yahoo Price", "Difference", "Status"]
    print(tabulate(results, headers=headers, tablefmt="grid"))
    
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n✅ = Prices match (< 0.1% difference)")
    print("⚠️ = Prices differ")
    print("❌ = Error fetching data\n")

if __name__ == "__main__":
    main()
