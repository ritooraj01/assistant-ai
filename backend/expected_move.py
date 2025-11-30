# backend/expected_move.py

def expected_move(close_spot, atr14, ml_score: float | None = None):
    """
    Compute expected move in index points and suggested SL/Target in option points.
    Very simple but surprisingly effective.
    """
    if close_spot is None or atr14 is None:
        return None

    atr_pct = (atr14 / close_spot) * 100

    # Base move = 0.6 * ATR
    base_move_pts = atr14 * 0.6

    # Adjust by ML confidence if available
    if ml_score is not None:
        # scale factor between 0.8 and 1.2
        factor = 0.8 + (ml_score - 0.5) * 0.8  # ml_score ~ 0.3..0.7
        base_move_pts *= factor

    # Simple SL/Target ratio (1:2 RR)
    target_pts = base_move_pts
    sl_pts = base_move_pts / 2

    return {
        "atr_pct": round(atr_pct, 2),
        "expected_move_pts": round(base_move_pts, 1),
        "target_pts": round(target_pts, 1),
        "sl_pts": round(sl_pts, 1),
        "rr": 2.0
    }
