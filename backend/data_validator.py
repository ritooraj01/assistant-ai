"""
Data validation and normalization utilities.
Ensures consistent, safe data handling across all endpoints.
"""
import math
from typing import Optional, Tuple, Dict, Any


def validate_price(price: float, prev_close: Optional[float] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate price data.
    
    Returns:
        (is_valid, error_message)
    """
    if price is None or not math.isfinite(price) or price <= 0:
        return False, f"Invalid price: {price}"
    
    if prev_close is not None:
        if prev_close <= 0 or not math.isfinite(prev_close):
            return False, f"Invalid prevClose: {prev_close}"
            
        # Check for extreme percentage changes (> 40%)
        change_pct = abs((price - prev_close) / prev_close * 100)
        if change_pct > 40:
            return False, f"Extreme change: {change_pct:.2f}%"
    
    return True, None


def normalize_price_data(
    last: float,
    prev_close: Optional[float] = None,
    symbol: str = ""
) -> Dict[str, Any]:
    """
    Normalize price data with validation and anomaly detection.
    
    NEW SPECIFICATION:
    - Always return lastPrice (never None/blank)
    - If prevClose valid → calculate pctChange normally
    - If prevClose invalid → pctChangeAvailable = false
    - Detect anomalies (>40%) → pctChangeAvailable = false, anomaly = true
    
    Returns dict matching JSON schema:
        - lastPrice: always present (float)
        - prevClose: float or None
        - pctChange: float or None
        - pctChangeAvailable: boolean
        - anomaly: boolean (true if >40% change detected)
        - error: string or None
    """
    result = {
        "lastPrice": None,
        "prevClose": None,
        "pctChange": None,
        "pctChangeAvailable": False,
        "anomaly": False,
        "error": None
    }
    
    # Validate last price - ALWAYS required
    if last is None or not math.isfinite(last) or last <= 0:
        result["error"] = f"Invalid last price: {last}"
        print(f"⚠️ DATA VALIDATION: {symbol} - {result['error']}")
        return result
    
    result["lastPrice"] = round(float(last), 2)
    
    # If no previous close, can't calculate change but price is still valid
    if prev_close is None or prev_close <= 0 or not math.isfinite(prev_close):
        result["prevClose"] = None
        result["pctChangeAvailable"] = False
        # lastPrice is present, but no % change
        return result
    
    result["prevClose"] = round(float(prev_close), 2)
    
    # Calculate change
    change_pct = ((last - prev_close) / prev_close) * 100
    
    # Check for anomalies (> 40% change)
    if abs(change_pct) > 40:
        result["anomaly"] = True
        result["pctChangeAvailable"] = False
        result["error"] = f"Extreme change detected: {change_pct:.2f}%"
        print(f"⚠️ ANOMALY: {symbol} - last={last}, prev={prev_close}, change={change_pct:.2f}%")
        # Keep lastPrice, but suppress % change
        return result
    
    # Valid percentage change
    result["pctChange"] = round(change_pct, 2)
    result["pctChangeAvailable"] = True
    
    return result


def validate_indicator(value: float, name: str, min_val: Optional[float] = None) -> Optional[float]:
    """
    Validate indicator value.
    Returns None if invalid, otherwise the validated float value.
    
    Args:
        value: The indicator value
        name: Name of the indicator (for logging)
        min_val: Minimum valid value (e.g., 0 for RSI, ATR)
    """
    if value is None:
        return None
    
    try:
        val = float(value)
    except (TypeError, ValueError):
        print(f"⚠️ INDICATOR: {name} - cannot convert to float: {value}")
        return None
    
    # Check for NaN or infinite
    if not math.isfinite(val):
        print(f"⚠️ INDICATOR: {name} - not finite: {val}")
        return None
    
    # Check minimum value
    if min_val is not None and val < min_val:
        print(f"⚠️ INDICATOR: {name} - below minimum {min_val}: {val}")
        return None
    
    return val


def validate_indicators(indicators: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate all indicators in a dict.
    Returns dict with validated values (None for invalid).
    """
    validated = {}
    
    # RSI must be 0-100, or None if insufficient data
    rsi = indicators.get("rsi14")
    validated["rsi14"] = validate_indicator(rsi, "RSI", min_val=0) if rsi not in [0, None] else None
    
    # ATR must be > 0
    atr = indicators.get("atr14")
    validated["atr14"] = validate_indicator(atr, "ATR", min_val=0.01) if atr not in [0, None] else None
    
    # MACD - must have all three values or all None
    macd = validate_indicator(indicators.get("macd"), "MACD")
    macd_signal = validate_indicator(indicators.get("macd_signal"), "MACD_Signal")
    macd_hist = validate_indicator(indicators.get("macd_hist"), "MACD_Hist")
    
    if macd is not None and macd_signal is not None and macd_hist is not None:
        validated["macd"] = macd
        validated["macd_signal"] = macd_signal
        validated["macd_hist"] = macd_hist
    else:
        validated["macd"] = None
        validated["macd_signal"] = None
        validated["macd_hist"] = None
    
    # Bollinger Bands
    validated["bb_upper"] = validate_indicator(indicators.get("bb_upper"), "BB_Upper")
    validated["bb_lower"] = validate_indicator(indicators.get("bb_lower"), "BB_Lower")
    validated["bb_width"] = validate_indicator(indicators.get("bb_width"), "BB_Width")
    validated["bb_percent"] = validate_indicator(indicators.get("bb_percent"), "BB_Percent")
    
    # EMAs
    validated["ema9"] = validate_indicator(indicators.get("ema9"), "EMA9")
    validated["ema21"] = validate_indicator(indicators.get("ema21"), "EMA21")
    validated["ema50"] = validate_indicator(indicators.get("ema50"), "EMA50")
    validated["ema200"] = validate_indicator(indicators.get("ema200"), "EMA200")
    
    # Supertrend
    validated["supertrend"] = validate_indicator(indicators.get("supertrend"), "Supertrend")
    
    return validated


def validate_forex_rate(rate: float, pair: str = "USDINR") -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Validate forex rates with range checks.
    
    Returns:
        (is_valid, validated_rate, error_message)
    """
    if rate is None or not math.isfinite(rate) or rate <= 0:
        return False, None, f"Invalid {pair} rate: {rate}"
    
    # USD/INR specific validation (expected range: 70-95)
    if pair == "USDINR":
        if rate < 70 or rate > 95:
            return False, None, f"USDINR rate outside expected range (70-95): {rate}"
    
    return True, round(float(rate), 2), None


def can_generate_reasoning(indicators: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Check if we have sufficient valid indicators to generate reasoning.
    
    Returns:
        (can_generate, reason_if_not)
    """
    validated = validate_indicators(indicators)
    
    # Need at least price, one EMA, and one momentum indicator
    if validated.get("ema21") is None:
        return False, "Insufficient candles for EMA calculation"
    
    if validated.get("rsi14") is None and validated.get("macd") is None:
        return False, "Insufficient candles for momentum indicators"
    
    return True, ""
