# backend/ml_ensemble.py

def ensemble_ml(ml_pred: dict) -> dict:
    """Normalise ML output for API responses.

    Supports both new-format keys (p1/p3/p5) and legacy keys
    (next_1_up/next_3_up/next_5_up).
    """

    if not ml_pred:
        return {
            "enabled": False,
            "p1": None,
            "p3": None,
            "p5": None,
            "final_ml_score": None,
            "trend_label": "No ML data",
        }

    def _get_prob(new_key: str, legacy_key: str, default: float = 0.5) -> float:
        value = ml_pred.get(new_key)
        if value is None:
            value = ml_pred.get(legacy_key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    p1 = _get_prob("p1", "next_1_up")
    p3 = _get_prob("p3", "next_3_up")
    p5 = _get_prob("p5", "next_5_up")

    final_score = ml_pred.get("final_ml_score")
    if final_score is None:
        final_score = 0.4 * p1 + 0.35 * p3 + 0.25 * p5

    try:
        final_score = float(final_score)
    except (TypeError, ValueError):
        final_score = 0.5

    trend_label = ml_pred.get("trend_label")
    if not trend_label:
        if final_score >= 0.7:
            trend_label = "Strong Bullish"
        elif final_score >= 0.6:
            trend_label = "Bullish"
        elif final_score >= 0.55:
            trend_label = "Mild Bullish"
        elif final_score <= 0.3:
            trend_label = "Strong Bearish"
        elif final_score <= 0.4:
            trend_label = "Bearish"
        elif final_score <= 0.45:
            trend_label = "Mild Bearish"
        else:
            trend_label = "Sideways / No Edge"

    return {
        "enabled": ml_pred.get("enabled", True),
        "p1": round(p1, 3),
        "p3": round(p3, 3),
        "p5": round(p5, 3),
        "final_ml_score": round(final_score, 3),
        "trend_label": trend_label,
    }
