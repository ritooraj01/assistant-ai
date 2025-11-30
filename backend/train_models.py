"""
Quick ML Training Script
Downloads data, prepares features, trains models in one go
"""

import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    print("=" * 70)
    print("ML MODEL TRAINING PIPELINE")
    print("=" * 70)
    
    # Step 1: Download data
    print("\n[STEP 1/3] Downloading historical data...")
    try:
        from ml.download_data import download_all
        download_all()
        print("[OK] Data download complete")
    except Exception as e:
        print(f"[ERROR] Data download failed: {e}")
        print("[INFO] Attempting to use existing data...")
    
    # Step 2: Prepare features
    print("\n[STEP 2/3] Preparing features and labels...")
    try:
        from ml.prepare_features import save_features
        save_features()
        print("[OK] Feature preparation complete")
    except Exception as e:
        print(f"[ERROR] Feature preparation failed: {e}")
        return False
    
    # Step 3: Train models
    print("\n[STEP 3/3] Training ML models...")
    try:
        from ml.train_ml import train_all
        train_all()
        print("[OK] Model training complete")
    except Exception as e:
        print(f"[ERROR] Model training failed: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("[SUCCESS] ML pipeline completed successfully!")
    print("=" * 70)
    print("\nModels are now ready for use in the trading system.")
    print("Restart the backend server to load the new models.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
