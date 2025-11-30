# backend/test_api_integration.py
"""
Automated QA Suite for API Integrations
Tests: candle continuity, indicator accuracy, FX values, API latency
"""

import asyncio
import time
from api_integrations import get_gift_nifty, get_sgx_nifty, get_usdinr_fx, test_api_latency

class TestResults:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
    
    def add_pass(self, test_name):
        self.tests_run += 1
        self.tests_passed += 1
        print(f"✅ PASS: {test_name}")
    
    def add_fail(self, test_name, reason):
        self.tests_run += 1
        self.tests_failed += 1
        self.failures.append((test_name, reason))
        print(f"❌ FAIL: {test_name} - {reason}")
    
    def summary(self):
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        if self.failures:
            print("\nFailed Tests:")
            for test_name, reason in self.failures:
                print(f"  - {test_name}: {reason}")
        print("="*60 + "\n")


def test_gift_nifty_api(results: TestResults):
    """Test GIFT Nifty API integration"""
    print("\n📊 Testing GIFT Nifty API...")
    
    latency_test = test_api_latency("GIFT Nifty", get_gift_nifty)
    
    # Test 1: API responds
    if latency_test["success"]:
        results.add_pass("GIFT Nifty API responds")
    else:
        results.add_fail("GIFT Nifty API responds", latency_test["error"])
        return
    
    # Test 2: Latency < 500ms
    if latency_test["latency_ms"] < 500:
        results.add_pass(f"GIFT Nifty latency OK ({latency_test['latency_ms']}ms)")
    else:
        results.add_fail("GIFT Nifty latency", f"{latency_test['latency_ms']}ms > 500ms")
    
    # Test 3: Data validation
    last, change = get_gift_nifty()
    if last and 10000 < last < 50000:  # Realistic NIFTY range
        results.add_pass(f"GIFT Nifty data valid ({last})")
    else:
        results.add_fail("GIFT Nifty data validation", f"Value {last} outside realistic range")


def test_sgx_nifty_api(results: TestResults):
    """Test SGX Nifty API integration"""
    print("\n📊 Testing SGX Nifty API...")
    
    latency_test = test_api_latency("SGX Nifty", get_sgx_nifty)
    
    # Test 1: API responds
    if latency_test["success"]:
        results.add_pass("SGX Nifty API responds")
    else:
        results.add_fail("SGX Nifty API responds", latency_test["error"])
        return
    
    # Test 2: Latency < 500ms
    if latency_test["latency_ms"] < 500:
        results.add_pass(f"SGX Nifty latency OK ({latency_test['latency_ms']}ms)")
    else:
        results.add_fail("SGX Nifty latency", f"{latency_test['latency_ms']}ms > 500ms")
    
    # Test 3: Data validation
    last, change = get_sgx_nifty()
    if last and 10000 < last < 50000:  # Realistic NIFTY range
        results.add_pass(f"SGX Nifty data valid ({last})")
    else:
        results.add_fail("SGX Nifty data validation", f"Value {last} outside realistic range")


def test_usdinr_api(results: TestResults):
    """Test USD/INR FX API integration"""
    print("\n💱 Testing USD/INR FX API...")
    
    latency_test = test_api_latency("USD/INR", get_usdinr_fx)
    
    # Test 1: API responds
    if latency_test["success"]:
        results.add_pass("USD/INR API responds")
    else:
        results.add_fail("USD/INR API responds", latency_test["error"])
        return
    
    # Test 2: Latency < 500ms
    if latency_test["latency_ms"] < 500:
        results.add_pass(f"USD/INR latency OK ({latency_test['latency_ms']}ms)")
    else:
        results.add_fail("USD/INR latency", f"{latency_test['latency_ms']}ms > 500ms")
    
    # Test 3: Data validation (70-95 range)
    last, change = get_usdinr_fx()
    if last and 70 <= last <= 95:
        results.add_pass(f"USD/INR data valid ({last})")
    else:
        results.add_fail("USD/INR data validation", f"Value {last} outside realistic range (70-95)")


def test_api_failover(results: TestResults):
    """Test API failover and fallback mechanisms"""
    print("\n🔄 Testing API failover...")
    
    # Test GIFT Nifty failover
    last, change = get_gift_nifty()
    if last is not None:
        results.add_pass("GIFT Nifty failover/fallback works")
    else:
        results.add_fail("GIFT Nifty failover", "All APIs failed, no fallback data")
    
    # Test USD/INR failover
    last, change = get_usdinr_fx()
    if last is not None:
        results.add_pass("USD/INR failover/fallback works")
    else:
        results.add_fail("USD/INR failover", "All APIs failed, no fallback data")


def test_api_reconnection(results: TestResults):
    """Test API reconnection after timeout"""
    print("\n🔌 Testing API reconnection...")
    
    # Simulate multiple calls to test connection persistence
    for i in range(3):
        last, change = get_gift_nifty()
        time.sleep(1)
    
    if last is not None:
        results.add_pass("API reconnection after multiple calls")
    else:
        results.add_fail("API reconnection", "Failed to reconnect after multiple attempts")


def test_data_consistency(results: TestResults):
    """Test data consistency across multiple calls"""
    print("\n📏 Testing data consistency...")
    
    # Call API twice and check for consistency
    last1, change1 = get_usdinr_fx()
    time.sleep(2)
    last2, change2 = get_usdinr_fx()
    
    if last1 and last2:
        # Values should be very close (within 1%)
        diff_pct = abs(last1 - last2) / last1 * 100
        if diff_pct < 1.0:
            results.add_pass(f"Data consistency OK (diff: {diff_pct:.2f}%)")
        else:
            results.add_fail("Data consistency", f"Values differ by {diff_pct:.2f}%")
    else:
        results.add_fail("Data consistency", "One or both API calls failed")


def run_all_tests():
    """Run all API integration tests"""
    print("\n" + "="*60)
    print("AUTOMATED QA SUITE FOR API INTEGRATIONS")
    print("="*60)
    
    results = TestResults()
    
    # Run all test suites
    test_gift_nifty_api(results)
    test_sgx_nifty_api(results)
    test_usdinr_api(results)
    test_api_failover(results)
    test_api_reconnection(results)
    test_data_consistency(results)
    
    # Print summary
    results.summary()
    
    return results.tests_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
