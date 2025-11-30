from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
import requests
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import time
import traceback
from nsepython import nsefetch
from live_candles import get_engine
from signal_logic import decide_signal
from technical import compute_all_indicators
import yfinance as yf
import pandas as pd
import numpy as np
import math
from news_sentiment import fetch_filtered_news, analyze_sentiment
from sectors import sector_score_for_symbol
from options_helper import suggest_option_strikes
from earnings import fetch_upcoming_results, sector_event_risk
from sectors import SECTOR_STOCKS
from global_cues import get_global_cues, compute_global_bias
from vix import get_india_vix, vix_risk_level
from fii_dii import get_fii_dii_trend
from volume_logic import detect_volume_anomaly, detect_fake_breakout
from cache_helper import cached_call, cache_get, cache_set
from fallback_data import load_sample_candles, load_sample_price
from cache_background import start_cache_thread
from reversal import detect_reversal
from market_mood import compute_market_mood
from conflict import resolve_conflicts
from fastapi import WebSocket
from price_helper import get_nse_spot_price
from options_fetcher import get_option_chain
from strike_engine import choose_strike
from option_signal import option_signal
from iv_engine import iv_trend
from oi_engine import analyze_oi
from greeks import bs_greeks
from ml_ensemble import ensemble_ml
from expected_move import expected_move
from orderflow import classify_orderflow
from regime import detect_regime
from reversal_ai import reversal_probability
from data_validator import validate_indicators, can_generate_reasoning



# Import ML prediction pipeline
ML_ENABLED = False

try:
    from ml.ml_model import predict_next
    ML_ENABLED = True
    print("✅ ML models loaded successfully")
except Exception as e:
    print(f"⚠️ ML pipeline unavailable: {e}")
    print("   Run 'python train_models.py' to train models")
    
    def predict_next(df):
        return {"enabled": False, "reason": "ML models not trained yet"}


app = FastAPI()

# Temporarily disabled - debugging
# start_cache_thread()

# Global exception handler to ensure CORS headers on all responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = f"{type(exc).__name__}: {str(exc)}"
    print(f"❌ EXCEPTION in {request.url.path}: {error_detail}")
    traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={"error": error_detail, "path": str(request.url.path)},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Enhanced CORS configuration to allow all requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=3600  # Cache preflight requests for 1 hour
)

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/test_cors")
def test_cors():
    return {"message": "CORS is working!", "timestamp": time.time()}


# -----------------------------------------
# REAL-TIME NSE SPOT PRICE (imported from price_helper)
# -----------------------------------------


@app.get("/api/live_nse")
def live_nse(symbol: str = "NIFTY"):
    try:
        last_price = get_nse_spot_price(symbol)
    except Exception as e:
        return {"error": str(e)}

    return {
        "symbol": symbol.upper(),
        "last_price": last_price
    }


# -----------------------------------------
# REAL-TIME OHLC BUILT FROM LIVE TICKS
# -----------------------------------------
@app.get("/api/ohlc_live")
def ohlc_live(symbol: str = "NIFTY", interval: int = 60, limit: int = 50):
    try:
        price = get_nse_spot_price(symbol)
    except Exception as e:
        return {"error": f"Failed to fetch spot price: {e}"}

    engine = get_engine(symbol, interval_sec=interval, max_candles=limit)
    engine.update_with_price(price)

    candles = engine.get_candles()
    candles = candles[-limit:]

    return {
        "symbol": symbol.upper(),
        "interval_sec": interval,
        "candles": candles
    }

@app.get("/api/ohlc_live_indicators")
def ohlc_live_indicators(symbol: str = "NIFTY", interval: int = 60, limit: int = 50):
    """
    Build real-time OHLC candles and compute technical indicators.
    """
    from technical import compute_all_indicators
    import pandas as pd

    try:
        price = get_nse_spot_price(symbol)
    except Exception as e:
        return {"error": f"Failed to fetch spot price: {e}"}

    engine = get_engine(symbol, interval_sec=interval, max_candles=limit)
    engine.update_with_price(price)

    candles = engine.get_candles()
    candles = candles[-limit:]

    # Convert to DataFrame for indicator calculation
    df = pd.DataFrame(candles)

    # Compute indicators
    df = compute_all_indicators(df)

    last = df.iloc[-1]

    return {
        "symbol": symbol.upper(),
        "interval_sec": interval,
        "price": float(last["close"]),

        # Trend indicators
        "ema9": float(last["ema9"]),
        "ema21": float(last["ema21"]),
        "ema50": float(last["ema50"]),
        "ema200": float(last["ema200"]),

        # Momentum
        "rsi14": float(last["rsi14"]),
        "macd": float(last["macd"]),
        "macd_signal": float(last["macd_signal"]),
        "macd_hist": float(last["macd_hist"]),

        # Volatility
        "atr14": float(last["atr14"]),
        "bb_upper": float(last["bb_upper"]),
        "bb_lower": float(last["bb_lower"]),
        "bb_width": float(last["bb_width"]),

        # Trend direction
        "supertrend": float(last["supertrend"])
    }

@app.get("/api/history")
def history(
    symbol: str = Query("NIFTY"),
    interval: int = Query(5, ge=1, le=60),
    limit: int = Query(200, ge=10, le=1000)
):
    """
    Return historical OHLC candles for the given symbol and interval.
    Used to seed the frontend chart so it doesn't start empty.
    """

    # Map indices to Yahoo tickers
    yf_map = {
        "NIFTY": "^NSEI",
        "NIFTY50": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
    }

    s = symbol.upper()
    ticker = yf_map.get(s, s + ".NS")  # for stocks: INFY -> INFY.NS

    try:
        print(f"📥 Downloading history for {ticker} with interval {interval}m")
        df = yf.download(
            ticker,
            period="5d",                  # last 5 days
            interval=f"{interval}m",      # "5m", "15m", etc.
            auto_adjust=True,
            progress=False,
        )
        print(f"✅ Downloaded {len(df)} candles for {ticker}")
    except Exception as e:
        print(f"❌ yfinance error: {e}")
        # Fallback to sample data if yfinance fails
        from fallback_data import load_sample_candles_with_time
        sample = load_sample_candles_with_time(symbol, limit)
        if sample:
            print(f"✅ Using {len(sample)} sample candles as fallback")
            return {"symbol": s, "interval": interval, "candles": sample}
        return {"error": f"Failed to download history: {e}"}

    if df.empty:
        print(f"⚠️ yfinance returned empty dataframe for {ticker}")
        # Try fallback data
        from fallback_data import load_sample_candles_with_time
        sample = load_sample_candles_with_time(symbol, limit)
        if sample:
            print(f"✅ Using {len(sample)} sample candles as fallback")
            return {"symbol": s, "interval": interval, "candles": sample}
        return {"error": "No historical data returned.", "symbol": symbol}

    df = df.tail(limit)

    # Flatten MultiIndex columns if they exist (yfinance quirk)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    candles = []
    # Iterate using iloc for clean integer-based indexing
    for i in range(len(df)):
        ts = int(df.index[i].timestamp())
        candles.append({
            "time": ts,
            "open": float(df.iloc[i]['Open']),
            "high": float(df.iloc[i]['High']),
            "low": float(df.iloc[i]['Low']),
            "close": float(df.iloc[i]['Close']),
        })

    return {"symbol": s, "interval": interval, "candles": candles}

@app.get("/api/signal_live")
def signal_live(symbol: str = "NIFTY", interval: int = 60, limit: int = 50):
    """
    Master endpoint:
    - Live OHLC & indicators
    - Technical signal
    - Sector confirmation
    - News sentiment
    - Global cues (Nifty, Nasdaq, Crude, USDINR)
    - India VIX regime
    - FII/DII trend
    - Volume & fake breakout
    - Event / earnings risk
    - Final combined recommendation
    - Options idea
    """
    print(f"📡 === REQUEST RECEIVED === symbol={symbol}, interval={interval}s, limit={limit}")
    symbol = symbol.upper()
    print(f"📡 Processing: {symbol}")

    # --- live price / candles --- (cache price for 1 second to avoid repeated NSE calls)
    engine = get_engine(symbol, interval_sec=interval, max_candles=limit)
    candles: list[dict] = []
    using_fallback = False

    # Try to get fresh price from NSE (not cached)
    price = None
    price_cache_key = f"nse_price_{symbol}"
    
    try:
        # Check if we already have a cached price from within this interval
        # to avoid multiple update_with_price calls for the same price
        existing_candles = engine.get_candles(include_current=True)
        last_update_ts = existing_candles[-1]["start_ts"] if existing_candles else 0
        time_since_last_update = time.time() - last_update_ts
        
        # Only fetch and update if enough time has passed (at least half the interval)
        should_update = time_since_last_update >= (interval / 2)
        
        if should_update:
            # Try to get fresh price
            price = get_nse_spot_price(symbol)
            # Cache it for 1 second for other simultaneous requests
            cache_set(price_cache_key, price, ttl=1)
            price = float(price)
            # Update engine with fresh price
            engine.update_with_price(price)
        else:
            # Too soon to update - just use existing data
            price = existing_candles[-1]["close"] if existing_candles else None
            
    except Exception as price_error:
        # NSE API failed - use fallback strategies
        cached_price = cache_get(price_cache_key)
        if cached_price is not None:
            price = cached_price
        else:
            # Use pre-populated historical candles
            candles = engine.get_candles()[-limit:]
            if candles:
                price = candles[-1]["close"]
                using_fallback = False  # We're using real historical data
            else:
                # Last resort: sample candles
                sample_candles = load_sample_candles(symbol, limit)
                if sample_candles:
                    candles = sample_candles
                    price = sample_candles[-1]["close"]
                    using_fallback = True
                else:
                    return {"error": f"Failed to fetch spot price: {price_error}"}
    
    # Get candles from engine if we haven't already
    if not candles:
        candles = engine.get_candles()[-limit:]

    # If still no candles, try fallback data
    if not candles:
        sample_candles = load_sample_candles(symbol, limit)
        if sample_candles:
            candles = sample_candles
            price = price if price is not None else sample_candles[-1]["close"]
            using_fallback = True
        else:
            # Generate synthetic candles as last resort
            from fallback_data import generate_synthetic_candles
            if price:
                candles = generate_synthetic_candles(price, limit, interval)
                using_fallback = True
            else:
                return {"error": "No candles available"}

    # Validate price data
    if price is None:
        print(f"⚠️ ERROR: {symbol} has None price")
        return {"error": f"Price data unavailable for {symbol}", "symbol": symbol}
    
    price = float(price)
    if price <= 0 or pd.isna(price):
        print(f"⚠️ ANOMALY: {symbol} has invalid price: {price}")
        return {"error": f"Invalid price data for {symbol}", "symbol": symbol}

    # Convert candles to DataFrame and compute indicators
    # Note: We can't easily cache this since candles change frequently
    # But the engine itself maintains state efficiently in memory
    df = pd.DataFrame(candles)
    df = compute_all_indicators(df)

    # --- Multi-Timeframe Trend Analysis ---
    def trend(ema9, ema21, close):
        """Returns 1 (uptrend), -1 (downtrend), or 0 (no clear trend)"""
        # Handle None/NaN values
        if ema9 is None or ema21 is None or close is None:
            return 0
        if pd.isna(ema9) or pd.isna(ema21) or pd.isna(close):
            return 0
        if close > ema9 > ema21:
            return 1
        if close < ema9 < ema21:
            return -1
        return 0

    # Current timeframe trend (1m, 3m, or 5m)
    tf1 = trend(df.iloc[-1]["ema9"], df.iloc[-1]["ema21"], df.iloc[-1]["close"])

    # Higher timeframe trend (3x current interval, e.g., 15m if current is 5m)
    engine15 = get_engine(symbol, interval_sec=interval * 3, max_candles=40)
    engine15.update_with_price(price)
    candles15 = engine15.get_candles()
    
    tf15 = 0  # default neutral
    if candles15 and len(candles15) > 0:
        df15 = pd.DataFrame(candles15)
        df15 = compute_all_indicators(df15)
        if len(df15) > 0:
            tf15 = trend(df15.iloc[-1]["ema9"], df15.iloc[-1]["ema21"], df15.iloc[-1]["close"])

    # --- Reversal Detection ---
    reversal = detect_reversal(df)

    # Extract series for charting
    ema21_series = df["ema21"].bfill().fillna(df["close"]).tolist()
    ema50_series = df["ema50"].bfill().fillna(df["close"]).tolist()
    supertrend_series = df["supertrend"].bfill().fillna(df["close"]).tolist()

    last = df.iloc[-1].to_dict()

    # --- ML Prediction (before signal decision) ---
    if ML_ENABLED:
        try:
            ml_pred = predict_next(df) or {}
            if "enabled" not in ml_pred:
                ml_pred["enabled"] = True
        except Exception as e:
            ml_pred = {
                "enabled": False,
                "error": str(e)
            }
    else:
        ml_pred = {"enabled": False, "reason": "ML models not loaded"}

    # --- 1) ML Ensemble View ---
    ml_view = ensemble_ml(ml_pred if isinstance(ml_pred, dict) else {})

    # --- 2) Reversal Probability AI ---
    rev_prob = reversal_probability(df)

    # --- 3) Market Regime Detection ---
    regime = detect_regime(last, ml_view.get("trend_label", "neutral"))

    # Debug: Check what's in the last row
    print(f"DEBUG: last row keys: {list(last.keys())}")
    print(f"DEBUG: last row sample: close={last.get('close')}, rsi14={last.get('rsi14')}, ema21={last.get('ema21')}")
    print(f"DEBUG: DataFrame shape: {df.shape}, columns: {list(df.columns)}")
    
    # Build raw indicators dict
    raw_indicators = {
        "ema9": last.get("ema9"),
        "ema21": last.get("ema21"),
        "ema50": last.get("ema50"),
        "ema200": last.get("ema200"),
        "rsi14": last.get("rsi14"),
        "macd": last.get("macd"),
        "macd_signal": last.get("macd_signal"),
        "macd_hist": last.get("macd_hist"),
        "atr14": last.get("atr14"),
        "bb_upper": last.get("bb_upper"),
        "bb_lower": last.get("bb_lower"),
        "bb_width": last.get("bb_width"),
        "bb_percent": last.get("bb_percent"),
        "supertrend": last.get("supertrend"),
    }
    
    # Validate indicators (returns None for invalid/insufficient data)
    indicators = validate_indicators(raw_indicators)
    print(f"DEBUG: validated indicators: {indicators}")
    
    # Check if we can generate reasoning with current data
    can_reason, reason_msg = can_generate_reasoning(indicators)
    indicators_available = can_reason  # Flag for frontend
    if not can_reason:
        print(f"⚠️ Cannot generate reasoning: {reason_msg}")

    # --- technical signal (with ML influence) ---
    signal = decide_signal(last, ml_pred=ml_pred)
    action = signal["action"]  # BUY / SELL / WAIT
    tech_component = signal["confidence"]  # 0..1

    # --- sector confirmation --- (cache for 30 seconds)
    sector_score, sector_comments, sector_changes = cached_call(
        f"sector_{symbol}_{action}", sector_score_for_symbol, 30, symbol, action
    )
    sector_component = (sector_score + 1) / 2  # -1..1 -> 0..1

    # --- news sentiment --- (cache for 60 seconds)
    query_map = {
        "NIFTY": "Nifty 50 India stock market",
        "BANKNIFTY": "Bank Nifty Indian banking stocks",
    }
    q = query_map.get(symbol, f"{symbol} India stock market")
    try:
        headlines = cached_call(f"news_{symbol}", fetch_filtered_news, 60, q)
        sentiment_raw, sentiment_summary = analyze_sentiment(headlines)
    except Exception as news_error:
        print(f"⚠️ News fetch failed: {news_error}")
        headlines = []
        sentiment_raw, sentiment_summary = 0.0, "News data unavailable."
    sentiment_component = (sentiment_raw + 1) / 2  # -1..1 -> 0..1

    # --- global cues --- (cache for 30 seconds)
    global_data = cached_call("global_cues", get_global_cues, 30)
    global_score, global_comments = compute_global_bias(global_data)
    global_component = (global_score + 1) / 2  # -1..1 -> 0..1

    # --- VIX regime --- (cache for 30 seconds)
    vix_val = cached_call("india_vix", get_india_vix, 30)
    vix_risk_score, vix_label, vix_comment = vix_risk_level(vix_val)
    vix_component = 1 - vix_risk_score  # high risk => lower confidence

    # --- FII/DII --- (cache for 60 seconds)
    fii_score_raw, fii_label, fii_comments = cached_call("fii_dii", get_fii_dii_trend, 60)
    fii_component = (fii_score_raw + 1) / 2  # -1..1 -> 0..1

    # --- Market Mood ---
    try:
        market_mood = compute_market_mood(
            global_data, 
            {"sentiment_raw": sentiment_raw},
            vix_val,
            {"fii_net": fii_score_raw * 1000}
        )
    except Exception as e:
        print(f"⚠️ Market mood computation failed: {e}")
        market_mood = 50  # neutral fallback

    # --- Volume & Fake breakout ---
    vol_score, vol_comment = detect_volume_anomaly(df)
    brk_score, brk_comment = detect_fake_breakout(df)
    vol_component = (vol_score + 1) / 2
    brk_component = (brk_score + 1) / 2

    # --- Event / Earnings risk --- (cache for 300 seconds = 5 minutes)
    earnings = cached_call("earnings", fetch_upcoming_results, 300)
    # decide which sectors to look at for this symbol
    if symbol in ("NIFTY", "NIFTY50"):
        sectors_list = list(SECTOR_STOCKS.keys())
    elif symbol == "BANKNIFTY":
        sectors_list = ["BANKS", "FINANCIAL"]
    else:
        sectors_list = list(SECTOR_STOCKS.keys())

    risk_total = 0.0
    risk_dates = {}
    risk_reasons = []

    for sec in sectors_list:
        r, dt, reasons = sector_event_risk(SECTOR_STOCKS[sec], earnings)
        risk_total += r
        if dt:
            risk_dates[sec] = dt
        risk_reasons.extend(reasons)

    event_risk_score = min(risk_total, 1.0)  # 0..1

    # --- final combined score ---
    base_score = (
        0.35 * tech_component +
        0.15 * sector_component +
        0.15 * sentiment_component +
        0.10 * global_component +
        0.10 * fii_component +
        0.10 * vol_component +
        0.05 * brk_component
    )

    ml_score = ml_view.get("final_ml_score")
    if isinstance(ml_score, (int, float)):
        if action == "BUY" and ml_score > 0.60:
            base_score += 0.07
        elif action == "SELL" and ml_score < 0.40:
            base_score += 0.07

    # reduce confidence for high VIX + high event risk
    # Apply reductions separately to avoid over-penalizing (max 30% for VIX + max 20% for events)
    vix_reduction = (1 - vix_component) * 0.3  # VIX reduces by max 30%
    event_reduction = event_risk_score * 0.2   # Events reduce by max 20%
    base_score *= (1 - vix_reduction - event_reduction)

    final_score = round(min(max(base_score, 0.0), 1.0), 2)

    if action == "BUY":
        if final_score >= 0.75:
            final_label = "Strong Buy"
            final_note = "Technicals, sectors, global cues and news strongly favour longs."
        elif final_score >= 0.6:
            final_label = "Buy (moderate)"
            final_note = "Bias is bullish but manage position size."
        else:
            final_label = "Cautious / Small Buy"
            final_note = "Bullish bias but setup is not very strong."
    elif action == "SELL":
        if final_score >= 0.75:
            final_label = "Strong Sell"
            final_note = "Multiple factors align for downside – suitable for experienced traders."
        elif final_score >= 0.6:
            final_label = "Sell (moderate)"
            final_note = "Bearish bias; use strict risk management."
        else:
            final_label = "Cautious / Hedge Only"
            final_note = "Bearish hints but not a very strong short."
    else:
        final_label = "No Trade / Wait"
        final_note = "Signals, sectors or news are not aligned. Better to stay out."

    # --- options suggestion ---
    options_idea = suggest_option_strikes(symbol, float(last["close"]), action)

    # --- Advanced Options Analysis ---
    options_analysis = {}
    try:
        # 1) Fetch Option Chain
        oc = get_option_chain(symbol)
        
        # Check if options fetcher returned an error
        if "error" in oc:
            # Provide fallback values for better UX
            options_analysis = {
                "pcr": 1.0,
                "oi_trend": "Neutral",
                "iv_trend": "Stable",
                "note": "Options data temporarily unavailable - using neutral values",
                "error": f"Option chain fetch failed: {oc['error']}"
            }
        else:
            records = oc.get("records", {}).get("data", [])
            
            if not records:
                # Provide fallback values when no records available
                options_analysis = {
                    "pcr": 1.0,
                    "oi_trend": "Neutral",
                    "iv_trend": "Stable",
                    "note": "Options data temporarily unavailable - using neutral values",
                    "error": "No option chain data available from NSE"
                }
            else:
                # 2) Choose strike set
                strikes = [x["strikePrice"] for x in records]
                strike_info = choose_strike(price, strikes)
                
                # ATM data
                atm_strike = strike_info["atm"]
                atm_data = next((item for item in records if item["strikePrice"] == atm_strike), None)
                
                if atm_data:
                    ce = atm_data.get("CE", {})
                    pe = atm_data.get("PE", {})
                    
                    # 3) IV Analysis
                    iv_info = iv_trend(ce, pe)
                    
                    # 4) OI Analysis
                    oi_info = analyze_oi(ce, pe)
                    
                    # 5) Greeks (using CE IV for ATM, 1 day to expiry as default)
                    ce_iv = ce.get("impliedVolatility", 20.0)
                    greeks = bs_greeks(price, atm_strike, ce_iv, 1)
                    
                    # 6) Final Option Signal
                    # Prepare ML data with defaults if not available
                    def _ml_prob(new_key: str, legacy_key: str) -> float:
                        if not ml_pred or ml_pred.get("enabled") is False:
                            return 0.5
                        value = ml_pred.get(new_key)
                        if value is None:
                            value = ml_pred.get(legacy_key, 0.5)
                        try:
                            return float(value)
                        except (TypeError, ValueError):
                            return 0.5

                    ml_for_options = {
                        "next_1_up": _ml_prob("p1", "next_1_up"),
                        "next_3_up": _ml_prob("p3", "next_3_up"),
                        "next_5_up": _ml_prob("p5", "next_5_up"),
                    }
                    
                    opt_signal = option_signal(
                        ml_for_options, 
                        iv_info, 
                        oi_info, 
                        market_mood, 
                        sector_score
                    )
                    
                    # 7) Order Flow Classification
                    order_flow = classify_orderflow(ce, pe)
                    
                    # 8) Expected Move Calculation
                    exp_move = expected_move(
                        price, 
                        last["atr14"], 
                        ml_view.get("final_ml_score", 0.5)
                    )
                    
                    options_analysis = {
                        "strike": strike_info,
                        "iv": iv_info,
                        "oi": oi_info,
                        "greeks": greeks,
                        "order_flow": order_flow,
                        "exp_move": exp_move,
                        "signal": opt_signal
                    }
                else:
                    options_analysis = {"error": "ATM strike data not found"}
            
    except Exception as e:
        options_analysis = {"error": f"Option analysis failed: {str(e)}"}

    # --- Add Multi-Timeframe data to signal ---
    signal["mtf"] = {
        "tf1": tf1,      # Current timeframe (1m, 3m, or 5m)
        "tf15": tf15     # Higher timeframe (3x current interval)
    }

    # --- Conflict Resolution ---
    # Prepare sector_view dict for conflict resolution
    sector_view_dict = {
        "sector_score": sector_score,
        "sector_comments": sector_comments,
        "sector_changes": sector_changes,
    }
    
    # Resolve conflicts between signal, ML, indicators, market mood, and sector
    final_action, updated_reasons = resolve_conflicts(
        signal,
        ml_pred,
        indicators,
        market_mood,
        sector_view_dict
    )
    
    # Update signal with resolved action and reasons
    signal["action"] = final_action
    signal["reasons"] = updated_reasons

    # Convert candles to Lightweight Charts format
    candles_out = []
    for c in candles:
        # c is e.g. {"start_ts": ..., "open":..., "high":..., "low":..., "close":...}
        ts = int(c.get("start_ts", 0))
        candles_out.append({
            "time": ts,
            "open": float(c["open"]),
            "high": float(c["high"]),
            "low": float(c["low"]),
            "close": float(c["close"]),
        })
    
    # Log candle data being sent
    print(f"📤 Sending {len(candles_out)} candles for {symbol}")
    if candles_out:
        latest_candle = candles_out[-1]
        print(f"📊 Latest candle: time={latest_candle['time']}, close={latest_candle['close']}")

    return {
        "symbol": symbol,
        "interval_sec": interval,
        "price": float(last["close"]),
        "candles": candles_out,
        "indicators": indicators,
        "indicators_available": indicators_available,  # NEW: Flag if indicators valid
        "signal": signal,
        "series": {
            "ema21": ema21_series[-len(candles_out):] if len(ema21_series) > 0 else [],
            "ema50": ema50_series[-len(candles_out):] if len(ema50_series) > 0 else [],
            "supertrend": supertrend_series[-len(candles_out):] if len(supertrend_series) > 0 else [],
        },
        "news": {
            "sentiment_score": sentiment_raw,
            "sentiment_summary": sentiment_summary,
            "headlines": headlines,
        },
        "sector_view": {
            "sector_score": sector_score,
            "sector_comments": sector_comments,
            "sector_changes": sector_changes,
        },
        "global": {
            "data": global_data,
            "score": global_score,
            "comments": global_comments,
        },
        "vix": {
            "value": vix_val,
            "label": vix_label,
            "comment": vix_comment,
            "risk_score": vix_risk_score,
        },
        "fii_dii": {
            "score": fii_score_raw,
            "label": fii_label,
            "comments": fii_comments,
        },
        "volume_analysis": {
            "score": vol_score,
            "comment": vol_comment,
        },
        "fake_breakout": {
            "score": brk_score,
            "comment": brk_comment,
        },
        "reversal_signals": reversal,
        "reversal_prob": rev_prob.get("prob", 0.5),  # NEW: AI reversal probability
        "event_risk": {
            "score": event_risk_score,
            "next_results": risk_dates,
            "reasons": risk_reasons,
        },
        "market_mood": market_mood,
        "regime": regime,  # NEW: Market regime (trending/ranging/volatile)
        "ml_view": ml_view,  # NEW: ML ensemble view with trend labels
        "final": {
            "score": final_score,
            "label": final_label,
            "note": final_note,
            "components": {
                "technical": tech_component,
                "sector": sector_component,
                "news": sentiment_component,
                "global": global_component,
                "fii_dii": fii_component,
                "volume": vol_component,
                "breakout": brk_component,
                "vix_factor": vix_component,
                "event_risk": event_risk_score,
            },
        },
        "ml_predict": ml_pred,
        "options": options_analysis if options_analysis else options_idea,
        "options_suggestion": options_idea,  # Keep simple suggestion for backward compatibility
        "meta": {
            "data_source": "fallback" if using_fallback else "live"
        },
    }


@app.get("/api/news_sentiment")
def news_sentiment(symbol: str = "NIFTY"):
    """
    Fetch sector/market-focused news and sentiment.
    """
    query_map = {
        "NIFTY": "Nifty 50 India stock market",
        "BANKNIFTY": "Bank Nifty Indian banking stocks",
        "IT": "Nifty IT Indian IT stocks",
        "PHARMA": "Nifty Pharma Indian pharma stocks",
    }

    q = query_map.get(symbol.upper(), f"{symbol} India stock market")
    # Cache news for 60 seconds
    headlines = cached_call(f"news_{symbol}", fetch_filtered_news, 60, q)
    sentiment, summary = analyze_sentiment(headlines)

    return {
        "symbol": symbol.upper(),
        "sentiment_score": sentiment,
        "summary": summary,
        "headlines": headlines,
    }

@app.get("/api/sector_view")
def sector_view(symbol: str = "NIFTY", action: str = "BUY"):
    score, comments, sector_changes = sector_score_for_symbol(symbol, action.upper())
    return {
        "symbol": symbol.upper(),
        "action": action.upper(),
        "sector_score": score,
        "sector_comments": comments,
        "sector_changes": sector_changes,
    }

@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket, symbol: str = "NIFTY", interval: int = 5):
    # Import here to avoid circular import
    from ws_live import websocket_loop
    await websocket_loop(websocket, symbol, interval)


# -----------------------------------------
# SERVE FRONTEND FILES
# -----------------------------------------
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the main HTML file"""
    index_path = os.path.join(frontend_path, "index.html")
    return FileResponse(index_path)

@app.get("/styles.css")
async def serve_css():
    """Serve CSS file"""
    css_path = os.path.join(frontend_path, "styles.css")
    return FileResponse(css_path)

@app.get("/script.js")
async def serve_js():
    """Serve JavaScript file"""
    js_path = os.path.join(frontend_path, "script.js")
    return FileResponse(js_path)

@app.get("/test-chart.html")
async def serve_test_chart():
    """Serve test chart HTML file"""
    test_path = os.path.join(frontend_path, "test-chart.html")
    return FileResponse(test_path)

@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"status": "ok", "message": "Backend is working!", "timestamp": pd.Timestamp.now().isoformat()}


# -----------------------------------------
# PAPER TRADING ENDPOINTS
# -----------------------------------------

@app.get("/api/paper/stats")
def paper_trading_stats():
    """Get paper trading statistics"""
    from paper_trading import get_paper_engine
    engine = get_paper_engine()
    return engine.get_stats()


@app.post("/api/paper/open")
def paper_trading_open(
    symbol: str,
    action: str,
    entry_price: float,
    quantity: int,
    stop_loss: float,
    take_profit: float,
    signal_confidence: float = 0.0,
    ml_score: float = None
):
    """Open a paper trading position"""
    from paper_trading import get_paper_engine
    engine = get_paper_engine()
    return engine.open_position(
        symbol, action, entry_price, quantity,
        stop_loss, take_profit, signal_confidence, ml_score
    )


@app.post("/api/paper/update")
def paper_trading_update(symbol: str, current_price: float):
    """Update paper trading positions (check SL/TP)"""
    from paper_trading import get_paper_engine
    engine = get_paper_engine()
    closed = engine.update_positions(current_price, symbol)
    return {"closed_positions": closed}


@app.post("/api/paper/close")
def paper_trading_close(position_id: int, current_price: float):
    """Manually close a paper trading position"""
    from paper_trading import get_paper_engine
    engine = get_paper_engine()
    result = engine.close_position(position_id, current_price, "MANUAL")
    if result:
        return {"success": True, "position": result}
    return {"success": False, "error": "Position not found"}


@app.post("/api/paper/reset")
def paper_trading_reset():
    """Reset paper trading (start fresh)"""
    from paper_trading import get_paper_engine
    engine = get_paper_engine()
    engine.reset()
    return {"success": True, "message": "Paper trading reset"}