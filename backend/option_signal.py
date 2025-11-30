def option_signal(ml, iv, oi, mood, sector):
    buy_call_score = 0
    buy_put_score = 0
    reasons = []

    # ML impact
    if ml["next_3_up"] > 0.60:
        buy_call_score += 2
        reasons.append("ML predicts upward move.")
    if ml["next_3_up"] < 0.40:
        buy_put_score += 2
        reasons.append("ML predicts downward move.")

    # IV logic
    if iv["trend"] == "high":
        buy_call_score += 1
        reasons.append("IV expansion favors call.")
    if iv["trend"] == "low":
        buy_put_score += 1
        reasons.append("IV low favors put.")

    # OI logic
    if oi["sentiment"] == "call buildup":
        buy_call_score += 1.5
        reasons.append("Call OI buildup detected.")
    if oi["sentiment"] == "put buildup":
        buy_put_score += 1.5
        reasons.append("Put OI buildup detected.")

    # Market mood
    if mood > 60:
        buy_call_score += 1
    if mood < 40:
        buy_put_score += 1

    # Sector mood
    if sector > 0.2:
        buy_call_score += 1
    if sector < -0.2:
        buy_put_score += 1

    # Determine final
    if buy_call_score - buy_put_score >= 2:
        action = "CALL BUY"
        confidence = min(100, int((buy_call_score / 6) * 100))
    elif buy_put_score - buy_call_score >= 2:
        action = "PUT BUY"
        confidence = min(100, int((buy_put_score / 6) * 100))
    else:
        action = "AVOID"
        confidence = 35

    return {
        "action": action,
        "confidence": confidence,
        "buy_call_score": buy_call_score,
        "buy_put_score": buy_put_score,
        "reasons": reasons
    }
