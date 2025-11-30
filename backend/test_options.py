"""
Test script to debug options chain fetching
"""
from options_fetcher import get_option_chain
from strike_engine import choose_strike
from iv_engine import iv_trend
from oi_engine import analyze_oi
from greeks import bs_greeks
from option_signal import option_signal

def test_options():
    print("="*50)
    print("TESTING OPTIONS CHAIN")
    print("="*50)
    
    # Test 1: Fetch option chain
    print("\n1. Fetching NIFTY option chain...")
    oc = get_option_chain("NIFTY")
    
    if "error" in oc:
        print(f"   ❌ Error: {oc['error']}")
        return
    
    print(f"   ✅ Fetched successfully")
    print(f"   Keys: {list(oc.keys())}")
    
    # Test 2: Get records
    print("\n2. Extracting records...")
    records = oc.get("records", {}).get("data", [])
    print(f"   Records found: {len(records)}")
    
    if not records:
        print("   ❌ No records available")
        return
    
    # Test 3: Choose strikes
    print("\n3. Choosing strikes...")
    price = 26200  # Sample NIFTY price
    strikes = [x["strikePrice"] for x in records]
    print(f"   Available strikes: {len(strikes)}")
    print(f"   Strike range: {min(strikes)} to {max(strikes)}")
    
    strike_info = choose_strike(price, strikes)
    print(f"   ✅ ATM Strike: {strike_info['atm']}")
    print(f"   OTM CE: {strike_info['otm_call']}")
    print(f"   OTM PE: {strike_info['otm_put']}")
    
    # Test 4: Get ATM data
    print("\n4. Getting ATM data...")
    atm_strike = strike_info["atm"]
    atm_data = next((item for item in records if item["strikePrice"] == atm_strike), None)
    
    if not atm_data:
        print("   ❌ ATM data not found")
        return
    
    print(f"   ✅ ATM data found")
    print(f"   Keys: {list(atm_data.keys())}")
    
    ce = atm_data.get("CE", {})
    pe = atm_data.get("PE", {})
    
    print(f"   CE keys: {list(ce.keys())[:5]}...")
    print(f"   PE keys: {list(pe.keys())[:5]}...")
    
    # Test 5: IV Analysis
    print("\n5. IV Analysis...")
    iv_info = iv_trend(ce, pe)
    print(f"   ✅ IV: {iv_info}")
    
    # Test 6: OI Analysis
    print("\n6. OI Analysis...")
    oi_info = analyze_oi(ce, pe)
    print(f"   ✅ OI: {oi_info}")
    
    # Test 7: Greeks
    print("\n7. Greeks Calculation...")
    ce_iv = ce.get("impliedVolatility", 20.0)
    greeks = bs_greeks(price, atm_strike, ce_iv, 1)
    print(f"   ✅ Greeks: {greeks}")
    
    # Test 8: Option Signal
    print("\n8. Option Signal...")
    ml_dummy = {"next_1_up": 0.5, "next_3_up": 0.5, "next_5_up": 0.5}
    opt_signal = option_signal(ml_dummy, iv_info, oi_info, 55, 0.0)
    print(f"   ✅ Signal: {opt_signal}")
    
    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED!")
    print("="*50)

if __name__ == "__main__":
    try:
        test_options()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
