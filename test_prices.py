"""
Test script to verify Trading Assistant prices from API
"""
import requests
import time

API_BASE = "http://127.0.0.1:8000"

symbols = ['NIFTY', 'HDFCBANK', 'RELIANCE', 'TCS', 'INFY']

print("\n" + "="*60)
print("TRADING ASSISTANT - PRICE VERIFICATION")
print("="*60 + "\n")

for symbol in symbols:
    try:
        url = f"{API_BASE}/api/signal_live?symbol={symbol}&interval=5&limit=10"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        price = data.get('price', 'N/A')
        rsi = data.get('indicators', {}).get('rsi14', 0)
        atr = data.get('indicators', {}).get('atr14', 0)
        
        print(f"{symbol:12} Rs. {price:>10,.2f}   (RSI: {rsi:>6.2f}, ATR: {atr:>6.2f})")
        time.sleep(0.5)  # Small delay between requests
        
    except Exception as e:
        print(f"{symbol:12} ERROR: {e}")

print("\n" + "="*60 + "\n")
