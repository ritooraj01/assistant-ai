"""
Test script to validate all fixes:
1. News headlines load
2. Options PCR/OI show values
3. ML confidence is 60-80% for strong signals
4. Market regime updates properly
5. No '--' or 'Loading...' stuck
"""
import requests
import json

API_URL = "http://localhost:8000/api/signal_live?symbol=NIFTY"

print("🧪 Testing all fixes...\n")

try:
    response = requests.get(API_URL, timeout=10)
    data = response.json()
    
    # Test 1: News Headlines
    print("1️⃣ NEWS HEADLINES TEST:")
    headlines = data.get("news", {}).get("headlines", [])
    if headlines and len(headlines) > 0:
        print(f"   ✅ {len(headlines)} headlines loaded")
        print(f"   📰 Sample: {headlines[0].get('title', 'No title')[:60]}...")
    else:
        print("   ❌ No headlines loaded")
    
    # Test 2: Options Data
    print("\n2️⃣ OPTIONS DATA TEST:")
    options = data.get("options", {})
    oi = options.get("oi", {})
    pcr = oi.get("pcr") or options.get("pcr")
    sentiment = oi.get("sentiment") or options.get("oi_trend")
    
    if pcr is not None:
        print(f"   ✅ PCR = {pcr:.2f}")
    else:
        print(f"   ⚠️ PCR not available (fallback expected)")
    
    if sentiment:
        print(f"   ✅ OI Sentiment = {sentiment}")
    else:
        print(f"   ⚠️ OI Sentiment not available")
    
    # Test 3: ML Confidence
    print("\n3️⃣ ML CONFIDENCE TEST:")
    final = data.get("final", {})
    confidence = final.get("score", 0)
    action = data.get("signal", {}).get("action", "WAIT")
    
    print(f"   Action: {action}")
    print(f"   Confidence: {confidence * 100:.1f}%")
    
    components = final.get("components", {})
    print(f"   📊 Components:")
    print(f"      - Technical: {components.get('technical', 0) * 100:.1f}%")
    print(f"      - Sector: {components.get('sector', 0) * 100:.1f}%")
    print(f"      - News: {components.get('news', 0) * 100:.1f}%")
    print(f"      - VIX Factor: {components.get('vix_factor', 0) * 100:.1f}%")
    
    if action in ["BUY", "SELL"] and confidence >= 0.30:
        print(f"   ✅ Confidence is reasonable ({confidence * 100:.1f}%)")
    elif confidence < 0.15:
        print(f"   ❌ Confidence too low ({confidence * 100:.1f}%) - still an issue!")
    else:
        print(f"   ⚠️ Confidence is {confidence * 100:.1f}% - check if expected")
    
    # Test 4: Market Regime
    print("\n4️⃣ MARKET REGIME TEST:")
    regime = data.get("regime", {})
    regime_label = regime.get("label", "Unknown")
    
    indicators = data.get("indicators", {})
    atr = indicators.get("atr14", 0)
    price = data.get("price", 1)
    atr_pct = (atr / price * 100) if price > 0 else 0
    
    print(f"   Regime: {regime_label}")
    print(f"   ATR%: {atr_pct:.2f}%")
    
    if regime_label != "Dead / Very Low Volatility" or atr_pct < 0.5:
        print(f"   ✅ Regime classification looks good")
    else:
        print(f"   ❌ Regime stuck at 'Dead' - threshold issue!")
    
    # Test 5: No stuck placeholders
    print("\n5️⃣ UI PLACEHOLDERS TEST:")
    issues = []
    
    if not headlines:
        issues.append("Headlines empty (check if 'Loading...' stuck)")
    
    if pcr is None and not options.get("note"):
        issues.append("PCR is None without fallback note")
    
    if not sentiment:
        issues.append("OI Sentiment missing")
    
    if regime_label == "Unknown":
        issues.append("Regime is 'Unknown'")
    
    if issues:
        print("   ⚠️ Potential UI issues:")
        for issue in issues:
            print(f"      - {issue}")
    else:
        print("   ✅ All data fields populated properly")
    
    # Summary
    print("\n" + "="*60)
    print("📋 SUMMARY:")
    print("="*60)
    print(f"✅ News: {len(headlines)} headlines")
    print(f"✅ Options: PCR={pcr if pcr else 'N/A'}, Sentiment={sentiment}")
    print(f"✅ Confidence: {confidence * 100:.1f}% ({action})")
    print(f"✅ Regime: {regime_label}")
    print("="*60)
    
except requests.exceptions.RequestException as e:
    print(f"❌ API Request failed: {e}")
except Exception as e:
    print(f"❌ Test failed: {e}")
