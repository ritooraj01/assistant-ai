def _strike_step(symbol: str) -> int:
    s = symbol.upper()
    if s in ("NIFTY", "NIFTY50"):
        return 50
    if s in ("BANKNIFTY", "FINNIFTY"):
        return 100
    return 50


def suggest_option_strikes(symbol: str, spot: float, action: str):
    """
    Simple ATM/OTM suggestions based on spot & trade direction.

    action = "BUY" (bullish) or "SELL" (bearish / short bias for futures)
    We return calls for bullish, puts for bearish.
    """
    step = _strike_step(symbol)
    atm = round(spot / step) * step

    strikes = [atm - step, atm, atm + step]

    if action == "BUY":
        opt_type = "CALL"
        bias = "Bullish"
    elif action == "SELL":
        opt_type = "PUT"
        bias = "Bearish"
    else:
        # WAIT / unknown → just suggest ATM both sides for reference
        return {
            "bias": "Neutral / WAIT",
            "note": "No clear trade signal, ATM strikes shown only for reference.",
            "call_strikes": strikes,
            "put_strikes": strikes,
        }

    return {
        "bias": bias,
        "opt_type": opt_type,
        "recommended_strikes": strikes,
        "expiry_hint": "Use nearest weekly expiry for intraday; monthly for positional."
    }
