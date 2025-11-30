"""Model training script for the trading assistant ML pipeline."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
DATA_FILES = [DATA_DIR / "nifty_ml.csv", DATA_DIR / "banknifty_ml.csv"]
LABELS: Dict[str, str] = {"1": "y_1", "3": "y_3", "5": "y_5"}

RANDOM_STATE = 42
TEST_SIZE = 0.2


def _load_datasets() -> pd.DataFrame:
    frames = []
    for path in DATA_FILES:
        if not path.exists():
            logging.warning("Dataset missing: %s", path)
            continue
        df = pd.read_csv(path)
        frames.append(df)
    if not frames:
        raise FileNotFoundError("No processed datasets found. Run prepare_features.save_features() first.")
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.replace([np.inf, -np.inf], np.nan).dropna()
    return combined


def _train_models(X_train: pd.DataFrame, y_train: pd.Series) -> Tuple[RandomForestClassifier, XGBClassifier, Pipeline]:
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_split=5,
        min_samples_leaf=3,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    xgb = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        tree_method="hist",
        learning_rate=0.05,
        max_depth=6,
        n_estimators=400,
        subsample=0.9,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        random_state=RANDOM_STATE,
    )
    lr = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE)),
        ]
    )

    rf.fit(X_train, y_train)
    xgb.fit(X_train, y_train)
    lr.fit(X_train, y_train)

    return rf, xgb, lr


def train_all() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR = MODEL_DIR / "metrics"
    METRICS_DIR.mkdir(exist_ok=True)
    
    df = _load_datasets()

    feature_cols = [col for col in df.columns if not col.startswith("y_")]
    results = {}

    for horizon, label in LABELS.items():
        logging.info("Training models for horizon %s (label=%s)", horizon, label)

        X = df[feature_cols]
        y = df[label]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
        )

        rf, xgb, lr = _train_models(X_train, y_train)

        preds_rf = rf.predict(X_test)
        preds_xgb = xgb.predict(X_test)
        preds_lr = lr.predict(X_test)

        acc_rf = accuracy_score(y_test, preds_rf)
        acc_xgb = accuracy_score(y_test, preds_xgb)
        acc_lr = accuracy_score(y_test, preds_lr)

        logging.info(
            "Accuracy horizon %s -> RF: %.3f | XGB: %.3f | LR: %.3f",
            horizon,
            acc_rf,
            acc_xgb,
            acc_lr,
        )

        # Save models
        joblib.dump(rf, MODEL_DIR / f"rf_{horizon}.pkl")
        joblib.dump(xgb, MODEL_DIR / f"xgb_{horizon}.pkl")
        joblib.dump(lr, MODEL_DIR / f"lr_{horizon}.pkl")
        
        # Save detailed metrics
        from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_score, recall_score, f1_score
        import json
        
        for model_name, model, preds in [("rf", rf, preds_rf), ("xgb", xgb, preds_xgb), ("lr", lr, preds_lr)]:
            # Get probabilities for ROC-AUC
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(X_test)[:, 1]
                roc_auc = roc_auc_score(y_test, proba)
            else:
                # For LR in pipeline
                proba = model.predict_proba(X_test)[:, 1]
                roc_auc = roc_auc_score(y_test, proba)
            
            metrics = {
                "model": model_name,
                "horizon": horizon,
                "accuracy": float(accuracy_score(y_test, preds)),
                "precision": float(precision_score(y_test, preds, zero_division=0)),
                "recall": float(recall_score(y_test, preds, zero_division=0)),
                "f1_score": float(f1_score(y_test, preds, zero_division=0)),
                "roc_auc": float(roc_auc),
                "confusion_matrix": confusion_matrix(y_test, preds).tolist(),
                "train_samples": len(X_train),
                "test_samples": len(X_test),
                "features_used": len(feature_cols)
            }
            
            # Save metrics
            metrics_file = METRICS_DIR / f"{model_name}_{horizon}_metrics.json"
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            logging.info(f"  {model_name.upper()}: Acc={metrics['accuracy']:.3f}, Precision={metrics['precision']:.3f}, Recall={metrics['recall']:.3f}, F1={metrics['f1_score']:.3f}, ROC-AUC={metrics['roc_auc']:.3f}")
        
        # Save feature importance for RF and XGB
        feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'rf_importance': rf.feature_importances_,
            'xgb_importance': xgb.feature_importances_
        }).sort_values('rf_importance', ascending=False)
        
        importance_file = METRICS_DIR / f"feature_importance_{horizon}.csv"
        feature_importance.to_csv(importance_file, index=False)
        logging.info(f"  Top 5 features: {', '.join(feature_importance.head(5)['feature'].tolist())}")

        results[horizon] = {
            "rf": acc_rf,
            "xgb": acc_xgb,
            "lr": acc_lr,
        }

    logging.info("Training complete. Accuracies: %s", results)
    logging.info(f"Metrics saved to {METRICS_DIR}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    train_all()
