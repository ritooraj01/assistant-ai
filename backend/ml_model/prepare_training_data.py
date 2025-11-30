"""
Prepare training data for ML models by fetching historical data and computing indicators.
This script downloads NIFTY historical data and adds all required technical indicators.
"""

import pandas as pd
import yfinance as yf
import sys
import os

# Add parent directory to path to import technical indicators
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from technical import compute_all_indicators


def download_nifty_data(period="3mo", interval="5m"):
    """
    Download NIFTY 50 historical data from Yahoo Finance.
    
    Args:
        period: "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"
        interval: "1m", "2m", "5m", "15m", "30m", "60m", "1d"
    
    Returns:
        DataFrame with OHLCV data
    """
    print(f"📥 Downloading NIFTY data ({period}, {interval} interval)...")
    
    # NIFTY 50 ticker on Yahoo Finance
    ticker = "^NSEI"
    
    # Download data
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    
    # Reset index to make timestamp a column
    df = df.reset_index()
    
    # Rename columns to lowercase
    df.columns = [col.lower() if isinstance(col, str) else col for col in df.columns]
    if 'datetime' in df.columns:
        df = df.rename(columns={'datetime': 'timestamp'})
    
    # Keep only required columns
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    print(f"✅ Downloaded {len(df)} candles")
    return df


def prepare_training_dataset(output_file="nifty_training_5m.csv", period="3mo", interval="5m"):
    """
    Download data, compute indicators, and save to CSV for ML training.
    """
    # Download raw data
    df = download_nifty_data(period=period, interval=interval)
    
    if len(df) < 200:
        print(f"⚠️ Warning: Only {len(df)} candles. Minimum 200 recommended for training.")
        print("   Consider using a longer period (e.g., '6mo' or '1y')")
    
    # Compute all technical indicators
    print("🔧 Computing technical indicators...")
    df = compute_all_indicators(df)
    
    # Drop rows with NaN (from indicator warmup)
    df = df.dropna()
    
    print(f"✅ {len(df)} complete candles with indicators")
    
    # Save to CSV
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    df.to_csv(output_path, index=False)
    print(f"💾 Saved to: {output_path}")
    
    # Show sample
    print("\n📊 Sample data (first 2 rows):")
    print(df.head(2)[['timestamp', 'close', 'ema9', 'ema21', 'rsi14', 'macd']].to_string())
    
    print("\n✅ Training data ready!")
    print(f"   Columns: {len(df.columns)}")
    print(f"   Rows: {len(df)}")
    print(f"\n💡 Now run: python train_ml.py")
    
    return df


if __name__ == "__main__":
    # You can adjust these parameters:
    # - period: "1mo", "3mo", "6mo", "1y", "2y" (more data = better model)
    # - interval: "5m", "15m", "1h" (match your trading timeframe)
    
    prepare_training_dataset(
        output_file="nifty_training_5m.csv",
        period="3mo",  # 3 months of data
        interval="5m"  # 5-minute candles
    )
