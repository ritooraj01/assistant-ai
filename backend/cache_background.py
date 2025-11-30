import threading
import time
from cache_helper import cache_set, cache_get

# Data providers
from global_cues import get_global_cues
from vix import get_india_vix
from fii_dii import get_fii_dii_trend
from news_sentiment import fetch_filtered_news, analyze_sentiment
from earnings import fetch_upcoming_results

# Optional (only if you added sector heatmap API)
try:
    from sectors import fetch_sector_data
    SECTOR_ENABLED = True
except ImportError:
    SECTOR_ENABLED = False


# ---------------------------------------------------------
# Adaptive TTL based on volatility (India VIX)
# ---------------------------------------------------------

def ttl_for_global(vix):
    """
    High volatility → more frequent updates
    Low volatility → normal 30-second TTL
    """
    if vix is None:
        return 30

    if vix > 20:
        return 8
    elif vix > 16:
        return 12
    elif vix > 13:
        return 20
    else:
        return 30


def ttl_for_news(vix):
    if vix is None:
        return 60
    if vix > 20:
        return 20
    elif vix > 16:
        return 30
    else:
        return 60


def ttl_for_fii(vix):
    # FII/DII is daily data but refreshing faster helps stability
    if vix is None:
        return 60
    if vix > 18:
        return 30
    else:
        return 60


# ---------------------------------------------------------
# Background Loop
# ---------------------------------------------------------

def background_cache_loop():
    """
    Runs forever in a background thread.
    Preloads all external data so /api/signal_live is instant.
    """
    print("🔄 Background cache refresher started...")
    
    # Initial delay to let the app start
    time.sleep(2)

    while True:
        try:
            # ----------- VIX FIRST (for adaptive TTLs) ------------
            vix_val = get_india_vix()
            cache_set("india_vix", vix_val, ttl=30)

            # ----------- GLOBAL CUES (adaptive) -------------------
            gc_ttl = ttl_for_global(vix_val)
            global_cues = get_global_cues()
            cache_set("global_cues", global_cues, ttl=gc_ttl)

            # ----------- FII/DII (adaptive) -----------------------
            fii_ttl = ttl_for_fii(vix_val)
            fii_data = get_fii_dii_trend()
            cache_set("fii_dii", fii_data, ttl=fii_ttl)

            # ----------- NEWS (adaptive) --------------------------
            news_ttl = ttl_for_news(vix_val)
            headlines = fetch_filtered_news("Nifty 50 India stock market")
            sentiment_raw, sentiment_text = analyze_sentiment(headlines)

            cache_set("news_nifty", {
                "headlines": headlines,
                "sentiment_raw": sentiment_raw,
                "sentiment_text": sentiment_text
            }, ttl=news_ttl)

            # ----------- EARNINGS CALENDAR ------------------------
            earnings_list = fetch_upcoming_results()
            cache_set("earnings", earnings_list, ttl=300)

            # ----------- SECTOR HEATMAP (optional) ---------------
            if SECTOR_ENABLED:
                try:
                    sectors = fetch_sector_data()
                    cache_set("sector_data", sectors, ttl=30)
                except:
                    pass

        except Exception as e:
            print(f"⚠️ Background cache error: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

        # Run loop every 10 seconds — TTL will manage staleness
        time.sleep(10)


# ---------------------------------------------------------
# Start background thread on app startup
# ---------------------------------------------------------

def start_cache_thread():
    t = threading.Thread(target=background_cache_loop, daemon=True)
    t.start()
    print("🟢 Cache thread started.")
