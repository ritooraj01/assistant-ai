def detect_volume_anomaly(df):
    """
    Detect if volume spike is happening.
    Returns (strength, comment)
    """
    if "volume" not in df:
        return 0, "Volume data unavailable."

    avg20 = df["volume"].tail(20).mean()
    cur = df["volume"].iloc[-1]

    if cur > avg20 * 1.5:
        return 0.4, "Strong volume spike detected."
    elif cur < avg20 * 0.5:
        return -0.2, "Volume extremely low (avoid trades)."
    else:
        return 0.1, "Volume normal."

def detect_fake_breakout(df):
    """
    Simple breakout check: if candle wick is large.
    Returns (penalty, comment)
    """
    row = df.iloc[-1]
    candle_size = abs(row["close"] - row["open"])
    wick_high = row["high"] - max(row["close"], row["open"])
    wick_low = min(row["close"], row["open"]) - row["low"]

    # High wick = fake breakout risk
    if wick_high > candle_size * 1.5 or wick_low > candle_size * 1.5:
        return -0.4, "Fake breakout risk: large wick detected."
    else:
        return 0.1, "No breakout risk."
