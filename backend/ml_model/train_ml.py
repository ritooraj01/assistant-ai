import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from joblib import dump


def build_features(df):
    df = df.copy()

    # Basic returns
    df["ret"] = df["close"].pct_change()

    # Candle body features
    df["body"] = df["close"] - df["open"]
    df["range"] = df["high"] - df["low"]
    df["body_pct"] = df["body"] / (df["range"] + 1e-6)

    # Wick ratios
    df["upper_wick"] = df["high"] - df[["close","open"]].max(axis=1)
    df["lower_wick"] = df[["close","open"]].min(axis=1) - df["low"]
    df["upper_wick_pct"] = df["upper_wick"] / (df["range"] + 1e-6)
    df["lower_wick_pct"] = df["lower_wick"] / (df["range"] + 1e-6)

    # Indicator ratios
    df["ema9_ratio"] = df["close"] / df["ema9"]
    df["ema21_ratio"] = df["close"] / df["ema21"]
    df["ema50_ratio"] = df["close"] / df["ema50"]

    df["rsi14"] = df["rsi14"]
    df["macd"] = df["macd"]
    df["macd_hist"] = df["macd_hist"]
    df["atr_pct"] = df["atr14"] / df["close"] * 100
    df["bb_width_pct"] = df["bb_width"] / df["close"] * 100

    # Drop NaN
    df = df.replace([np.inf, -np.inf], np.nan).dropna()

    return df


def build_labels(df):
    df = df.copy()

    # Next-1 candle
    df["label_1"] = (df["close"].shift(-1) > df["close"]).astype(int)

    # Next-3 candles
    df["label_3"] = (df["close"].shift(-3) > df["close"]).astype(int)

    # Next-5 candles
    df["label_5"] = (df["close"].shift(-5) > df["close"]).astype(int)

    df = df.dropna()
    return df


def train_model(csv_path="nifty_training_5m.csv"):
    """
    Train Random Forest models for 1, 3, and 5 candle predictions.
    
    Args:
        csv_path: Path to CSV with OHLCV data and indicators
    """
    print(f"📖 Loading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df)} rows")

    # Build features and labels
    df = build_features(df)
    df = build_labels(df)

    feature_cols = [
        "ret","body_pct",
        "upper_wick_pct","lower_wick_pct",
        "ema9_ratio","ema21_ratio","ema50_ratio",
        "rsi14","macd","macd_hist",
        "atr_pct","bb_width_pct"
    ]

    X = df[feature_cols]

    models = {}

    for horizon, label in [(1,"label_1"), (3,"label_3"), (5,"label_5")]:
        y = df[label]

        model = RandomForestClassifier(
            n_estimators=120,
            max_depth=8,
            min_samples_leaf=5,
            class_weight="balanced"
        )

        print(f"\n🤖 Training {horizon}-candle model...")
        print(f"   Features: {X.shape[1]}, Samples: {len(X)}")
        
        model.fit(X, y)
        
        # Save model
        model_path = f"rf_{horizon}c.pkl"
        dump(model, model_path)
        print(f"   ✅ Saved: {model_path}")
        
        # Show accuracy
        score = model.score(X, y)
        print(f"   📊 Training accuracy: {score:.2%}")

        models[horizon] = model

    print("\n🎉 All models trained and saved!")
    print("\n💡 ML predictions are now enabled. Restart your backend server.")
    return models


if __name__ == "__main__":
    train_model()
