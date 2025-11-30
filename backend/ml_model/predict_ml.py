import joblib
import numpy as np
import pandas as pd
import os

# Get the directory where this file is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Load models once (with error handling)
try:
    model_1 = joblib.load(os.path.join(current_dir, "rf_1c.pkl"))
    model_3 = joblib.load(os.path.join(current_dir, "rf_3c.pkl"))
    model_5 = joblib.load(os.path.join(current_dir, "rf_5c.pkl"))
    MODELS_LOADED = True
except FileNotFoundError as e:
    print(f"⚠️ ML models not found: {e}")
    print(f"⚠️ Run train_ml.py to generate the model files")
    MODELS_LOADED = False
    model_1, model_3, model_5 = None, None, None


class MLPredictor:
    """
    ML Predictor with exponential smoothing to reduce prediction jitter.
    Maintains state: prev_pred stores last final_ml_score for smoothing.
    """
    def __init__(self):
        self.prev_pred = None  # Store previous final_ml_score for smoothing
    
    def extract_features_from_row(self, row):
        try:
            return np.array([
                row["ret"],
                row["body_pct"],
                row["upper_wick_pct"],
                row["lower_wick_pct"],
                row["ema9_ratio"],
                row["ema21_ratio"],
                row["ema50_ratio"],
                row["rsi14"],
                row["macd"],
                row["macd_hist"],
                row["atr_pct"],
                row["bb_width_pct"],
            ]).reshape(1, -1)
        except:
            return None
    
    def predict_next(self, df):
        """
        df = last 50 candles with indicators before calling this
        Returns smoothed ML predictions using exponential averaging (0.3 prev + 0.7 current)
        """
        if not MODELS_LOADED:
            return {
                "enabled": False,
                "reason": "ML models not trained yet. Run train_ml.py first."
            }
        
        row = df.iloc[-1].copy()

        # Build required features
        row["ret"] = row["close"] / df["close"].iloc[-2] - 1
        row["body"] = row["close"] - row["open"]
        row["range"] = row["high"] - row["low"]
        row["body_pct"] = row["body"] / (row["range"] + 1e-6)
        row["upper_wick"] = row["high"] - max(row["close"], row["open"])
        row["lower_wick"] = min(row["close"], row["open"]) - row["low"]
        row["upper_wick_pct"] = row["upper_wick"] / (row["range"] + 1e-6)
        row["lower_wick_pct"] = row["lower_wick"] / (row["range"] + 1e-6)

        row["ema9_ratio"] = row["close"] / row["ema9"]
        row["ema21_ratio"] = row["close"] / row["ema21"]
        row["ema50_ratio"] = row["close"] / row["ema50"]
        row["atr_pct"] = row["atr14"] / row["close"] * 100
        row["bb_width_pct"] = row["bb_width"] / row["close"] * 100

        feat = self.extract_features_from_row(row)
        if feat is None:
            return None

        # Predictions
        p1 = model_1.predict_proba(feat)[0][1]
        p3 = model_3.predict_proba(feat)[0][1]
        p5 = model_5.predict_proba(feat)[0][1]

        # Calculate raw final score
        current_score = (p1*0.4 + p3*0.35 + p5*0.25)
        
        # Apply exponential smoothing to reduce jitter
        if self.prev_pred is not None:
            final_score = (self.prev_pred * 0.3) + (current_score * 0.7)
        else:
            final_score = current_score
        
        # Store for next iteration
        self.prev_pred = final_score

        return {
            "next_1_up": round(float(p1), 3),
            "next_3_up": round(float(p3), 3),
            "next_5_up": round(float(p5), 3),
            "final_ml_score": round(float(final_score), 3),
            "raw_ml_score": round(float(current_score), 3)  # For debugging
        }


# Global predictor instance (maintains state across calls)
_predictor = MLPredictor()

def predict_next(df):
    """
    Wrapper function for backward compatibility.
    Uses global predictor instance to maintain smoothing state.
    """
    return _predictor.predict_next(df)
