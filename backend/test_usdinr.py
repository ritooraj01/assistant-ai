"""Test script to check USD/INR API response"""
import requests
import json

url = "http://127.0.0.1:8000/api/signal_live?symbol=NIFTY"

try:
    response = requests.get(url, timeout=10)
    data = response.json()
    
    global_cues = data.get("global_cues", {})
    usdinr = global_cues.get("usdinr", {})
    
    print("=" * 60)
    print("USD/INR Response:")
    print("=" * 60)
    print(json.dumps(usdinr, indent=2))
    print("\n")
    
    print("Expected fields:")
    print(f"  last: {usdinr.get('last')}")
    print(f"  change_pct: {usdinr.get('change_pct')}")
    print(f"  pct_change_available: {usdinr.get('pct_change_available')}")
    print(f"  quality_warning: {usdinr.get('quality_warning')}")
    
except Exception as e:
    print(f"Error: {e}")
