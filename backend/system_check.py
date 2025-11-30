"""
System Health Check and Diagnostic Tool
Validates all modules are working correctly before deployment
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def check_imports():
    """Check all critical imports"""
    print("Checking imports...")
    errors = []
    
    required_modules = [
        # Core
        ("fastapi", "FastAPI"),
        ("pandas", "pandas"),
        ("numpy", "NumPy"),
        
        # Backend modules
        ("technical", "Technical Indicators"),
        ("signal_logic", "Signal Logic"),
        ("ml_ensemble", "ML Ensemble"),
        ("options_fetcher", "Options Fetcher"),
        ("news_sentiment", "News Sentiment"),
        ("global_cues", "Global Cues"),
        ("vix", "VIX"),
        ("fii_dii", "FII/DII"),
        ("sectors", "Sectors"),
        ("cache_helper", "Cache Helper"),
        ("fallback_data", "Fallback Data"),
        ("live_candles", "Live Candles"),
        ("regime", "Regime Detection"),
        ("reversal_ai", "Reversal AI"),
        ("orderflow", "Order Flow"),
        ("expected_move", "Expected Move"),
        ("conflict", "Conflict Resolution"),
        ("market_mood", "Market Mood"),
        
        # ML
        ("ml.ml_model", "ML Models"),
        ("ml.train_ml", "ML Training"),
        ("ml.prepare_features", "ML Features"),
    ]
    
    for module_name, display_name in required_modules:
        try:
            __import__(module_name)
            print(f"  [OK] {display_name}")
        except Exception as e:
            error_msg = f"  [ERROR] {display_name}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
    
    return errors

def check_data_files():
    """Check if required data files exist"""
    print("\nChecking data files...")
    errors = []
    
    data_dir = Path(__file__).parent.parent / "data"
    required_files = [
        "nifty_5m.csv",
    ]
    
    for filename in required_files:
        filepath = data_dir / filename
        if filepath.exists():
            print(f"  [OK] {filename}")
        else:
            error_msg = f"  [WARN] {filename} (optional)"
            print(error_msg)
    
    return errors

def check_ml_models():
    """Check if ML models exist"""
    print("\nChecking ML models...")
    
    models_dir = Path(__file__).parent.parent / "models"
    if not models_dir.exists():
        print("  [WARN] Models directory not found (run training first)")
        return []
    
    model_files = list(models_dir.glob("*.pkl"))
    if model_files:
        print(f"  [OK] Found {len(model_files)} model files")
        for mf in model_files:
            print(f"     - {mf.name}")
    else:
        print("  [WARN] No model files found (run training first)")
    
    return []

def check_functions():
    """Check critical functions"""
    print("\nChecking critical functions...")
    errors = []
    
    try:
        from technical import compute_all_indicators
        import pandas as pd
        
        # Test with sample data
        test_df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100.5, 101.5, 102.5],
        })
        
        result = compute_all_indicators(test_df)
        if 'ema9' in result.columns and 'rsi14' in result.columns:
            print("  [OK] Technical indicators working")
        else:
            errors.append("  [ERROR] Technical indicators missing columns")
            print(errors[-1])
    except Exception as e:
        error_msg = f"  [ERROR] Technical indicators error: {e}"
        print(error_msg)
        errors.append(error_msg)
    
    try:
        from signal_logic import decide_signal
        test_row = {
            'open': 100, 'high': 101, 'low': 99, 'close': 100.5,
            'ema9': 100, 'ema21': 99, 'ema50': 98, 'ema200': 97,
            'rsi14': 55, 'macd': 0.5, 'macd_signal': 0.3, 'macd_hist': 0.2,
            'atr14': 1.5, 'bb_width': 2.0, 'supertrend': 99
        }
        signal = decide_signal(test_row)
        if 'action' in signal and 'confidence' in signal:
            print("  [OK] Signal logic working")
        else:
            errors.append("  [ERROR] Signal logic output format incorrect")
            print(errors[-1])
    except Exception as e:
        error_msg = f"  [ERROR] Signal logic error: {e}"
        print(error_msg)
        errors.append(error_msg)
    
    return errors

def main():
    """Run all checks"""
    print("=" * 60)
    print("TRADING ASSISTANT SYSTEM CHECK")
    print("=" * 60)
    
    all_errors = []
    
    # Run checks
    all_errors.extend(check_imports())
    all_errors.extend(check_data_files())
    all_errors.extend(check_ml_models())
    all_errors.extend(check_functions())
    
    # Summary
    print("\n" + "=" * 60)
    if all_errors:
        print(f"[ERROR] FOUND {len(all_errors)} ISSUES:")
        for error in all_errors:
            print(error)
        print("\n[WARNING] System may not function correctly.")
    else:
        print("[OK] ALL CHECKS PASSED!")
        print("[OK] System is ready for production.")
    print("=" * 60)
    
    return len(all_errors) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
