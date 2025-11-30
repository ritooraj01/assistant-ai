"""Model loading and inference utilities for the trading assistant."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

import joblib
import numpy as np
import pandas as pd

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
WEIGHTS = {"xgb": 0.5, "rf": 0.3, "lr": 0.2}
HORIZON_WEIGHTS = {"1": 0.5, "3": 0.3, "5": 0.2}

_MODELS: Dict[str, Dict[str, object]] = {"1": {}, "3": {}, "5": {}}
_FEATURE_COLUMNS: pd.Index | None = None


def load_models() -> None:
    """Load trained models into memory."""
    global _FEATURE_COLUMNS

    for horizon in _MODELS.keys():
        for model_name in WEIGHTS.keys():
            path = MODEL_DIR / f"{model_name}_{horizon}.pkl"
            if not path.exists():
                logging.warning("Model file missing: %s", path)
                continue
            _MODELS[horizon][model_name] = joblib.load(path)
            logging.info("Loaded %s", path.name)

    if not any(_MODELS[h].keys() for h in _MODELS):
        logging.error("No models loaded. Ensure training has been completed.")

    # Attempt to capture feature ordering from any model pipeline that stores it
    for horizon_models in _MODELS.values():
        lr_model = horizon_models.get("lr")
        if lr_model is not None:
            # Logistic regression pipeline stores feature names on the scaler after fitting (sklearn 1.0+)
            scaler = lr_model.named_steps.get("scaler") if hasattr(lr_model, "named_steps") else None
            if scaler is not None and hasattr(scaler, "feature_names_in_"):
                _FEATURE_COLUMNS = pd.Index(scaler.feature_names_in_)
                break


def _ensure_models_loaded() -> None:
    if not any(_MODELS[h].keys() for h in _MODELS):
        load_models()


def _prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    features = df.copy()
    features = features.drop(columns=[col for col in features.columns if col.startswith("y_")], errors="ignore")
    features = features.replace([np.inf, -np.inf], np.nan).ffill().bfill().fillna(0)

    if _FEATURE_COLUMNS is not None:
        missing = [col for col in _FEATURE_COLUMNS if col not in features.columns]
        for col in missing:
            features[col] = 0.0
        features = features[_FEATURE_COLUMNS]

    return features


def _predict_single(model, X: pd.DataFrame) -> float:
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[:, 1]
        return float(proba[-1])
    elif hasattr(model, "predict"):
        prediction = model.predict(X)
        return float(np.clip(prediction[-1], 0, 1))
    else:
        raise AttributeError(f"Model {model} does not support prediction")


def predict_next(df_last_rows: pd.DataFrame) -> Dict[str, float | str]:
    """Predict next moves using the ensemble of models."""
    _ensure_models_loaded()

    if df_last_rows.empty:
        return {"enabled": False, "reason": "Input dataframe is empty"}

    if not any(_MODELS[h] for h in _MODELS):
        return {"enabled": False, "reason": "ML models not loaded"}

    X = _prepare_features(df_last_rows)
    results: Dict[str, float] = {}

    for horizon, models in _MODELS.items():
        probs = []
        for model_name, model in models.items():
            weight = WEIGHTS.get(model_name, 0)
            try:
                prob = _predict_single(model, X)
            except Exception as exc:
                logging.error("Prediction failed for horizon %s model %s: %s", horizon, model_name, exc)
                continue
            probs.append(weight * prob)
        if probs:
            results[f"p{horizon}"] = float(np.clip(sum(probs), 0.0, 1.0))
        else:
            results[f"p{horizon}"] = 0.5  # neutral fallback

    final_ml_score = sum(HORIZON_WEIGHTS[h] * results.get(f"p{h}", 0.5) for h in HORIZON_WEIGHTS)
    final_ml_score = float(np.clip(final_ml_score, 0.0, 1.0))

    if final_ml_score > 0.60:
        trend = "UP"
    elif final_ml_score < 0.40:
        trend = "DOWN"
    else:
        trend = "SIDEWAYS"

    return {
        "enabled": True,
        "p1": round(results.get("p1", 0.5), 4),
        "p3": round(results.get("p3", 0.5), 4),
        "p5": round(results.get("p5", 0.5), 4),
        "next_1_up": round(results.get("p1", 0.5), 4),
        "next_3_up": round(results.get("p3", 0.5), 4),
        "next_5_up": round(results.get("p5", 0.5), 4),
        "final_ml_score": round(final_ml_score, 4),
        "trend_label": trend,
    }


# Lazy loading - models will be loaded on first prediction call
# This avoids slow import times and allows the module to be imported even without models
# try:  # pragma: no cover - executed on import
#     load_models()
# except Exception as exc:
#     logging.warning("ML models could not be loaded at import time: %s", exc)
