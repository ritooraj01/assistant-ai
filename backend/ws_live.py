import asyncio
import json
from fastapi import WebSocket
from live_candles import get_engine
from technical import compute_all_indicators
from signal_logic import decide_signal
from market_mood import compute_market_mood
from conflict import resolve_conflicts
from global_cues import get_global_cues
from news_sentiment import fetch_filtered_news, analyze_sentiment
from fii_dii import get_fii_dii_trend
from vix import get_india_vix
from price_helper import get_nse_spot_price
import pandas as pd
from fallback_data import load_sample_candles, load_sample_price

# ML prediction import
ML_ENABLED = False

try:
    from ml.ml_model import predict_next
    ML_ENABLED = True
except Exception as e:
    print(f"⚠️ ML pipeline unavailable: {e}")
    
    def predict_next(df):
        return {"enabled": False, "reason": "ML models not trained yet"}

async def websocket_loop(websocket: WebSocket, symbol: str, interval: int):
    await websocket.accept()

    engine = get_engine(symbol, interval_sec=interval, max_candles=80)
    last_price = load_sample_price(symbol)

    while True:
        try:
            using_fallback = False
            updated_engine = False
            candles = []

            try:
                live_price = get_nse_spot_price(symbol)
                price = float(live_price)
                engine.update_with_price(price)
                last_price = price
                updated_engine = True
            except Exception as price_error:
                print(f"⚠️ WebSocket price fetch failed: {price_error}")
                price = last_price if last_price is not None else load_sample_price(symbol)
                if price is None:
                    fallback_candles = load_sample_candles(symbol, 80)
                    if not fallback_candles:
                        await asyncio.sleep(2)
                        continue
                    candles = fallback_candles
                    price = candles[-1]["close"]
                    using_fallback = True

            if not updated_engine and price is not None and not using_fallback:
                engine.update_with_price(float(price))
                updated_engine = True

            if not candles:
                candles = engine.get_candles()[-80:]
                if not candles:
                    fallback_candles = load_sample_candles(symbol, 80)
                    if fallback_candles:
                        candles = fallback_candles
                        price = candles[-1]["close"]
                        using_fallback = True
                    else:
                        await asyncio.sleep(2)
                        continue

            df = pd.DataFrame(candles)
            if df.empty:
                await asyncio.sleep(2)
                continue

            df = compute_all_indicators(df)
            last = df.iloc[-1].to_dict()

            if ML_ENABLED:
                try:
                    ml = predict_next(df)
                except Exception as ml_error:
                    print(f"⚠️ ML prediction failed: {ml_error}")
                    ml = {"enabled": False, "error": str(ml_error)}
            else:
                ml = {"enabled": False, "reason": "ML models not trained yet"}

            try:
                signal = decide_signal(last, ml)
            except Exception as signal_error:
                print(f"⚠️ Signal computation failed: {signal_error}")
                signal = {
                    "action": "WAIT",
                    "confidence": 0.0,
                    "bullish_score": 0.0,
                    "bearish_score": 0.0,
                    "reasons": [f"Signal generation failed: {signal_error}"],
                }

            try:
                global_cues = get_global_cues()
            except Exception as global_error:
                print(f"⚠️ Global cues fetch failed: {global_error}")
                global_cues = {}

            try:
                news_headlines = fetch_filtered_news(symbol, max_items=10)
            except Exception as news_error:
                print(f"⚠️ News fetch failed: {news_error}")
                news_headlines = []

            try:
                sentiment_raw, sentiment_summary = analyze_sentiment(news_headlines)
            except Exception as sentiment_error:
                print(f"⚠️ News sentiment failed: {sentiment_error}")
                sentiment_raw, sentiment_summary = 0.0, "News data unavailable."

            news_payload = {
                "headlines": news_headlines,
                "sentiment_raw": sentiment_raw,
                "sentiment_summary": sentiment_summary,
            }

            fii_score, fii_label, fii_comments = get_fii_dii_trend()
            fii_payload = {
                "score": fii_score,
                "label": fii_label,
                "comments": fii_comments,
            }

            vix_value = get_india_vix()

            market_mood = compute_market_mood(
                global_cues or {},
                {"sentiment_raw": sentiment_raw},
                vix_value,
                {"fii_net": fii_score * 1000}
            )

            final_action, new_reasons = resolve_conflicts(
                signal,
                ml,
                last,
                market_mood,
                {"sector_score": 0}
            )
            signal["action"] = final_action
            signal["reasons"] = new_reasons

            packet = {
                "symbol": symbol,
                "price": price,
                "candles": candles[-80:],
                "indicators": last,
                "signal": signal,
                "ml_predict": ml,
                "market_mood": market_mood,
                "global_cues": global_cues,
                "news": news_payload,
                "fii_dii": fii_payload,
                "vix": vix_value,
                "meta": {"data_source": "fallback" if using_fallback else "live"},
            }

            try:
                await websocket.send_text(json.dumps(packet))
            except Exception as send_error:
                print(f"WebSocket disconnected: {send_error}")
                break
            
            await asyncio.sleep(1)

        except Exception as e:
            print("WebSocket Error:", e)
            await asyncio.sleep(2)
            continue
