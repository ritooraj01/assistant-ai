# API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, no authentication is required. For production deployment, implement JWT or API key authentication.

---

## Endpoints

### 1. Health Check
**GET** `/api/health`

Check if the API server is running.

**Response:**
```json
{
  "status": "ok"
}
```

---

### 2. Live NSE Price
**GET** `/api/live_nse`

Get the current spot price from NSE for a given symbol.

**Parameters:**
- `symbol` (string, optional): Symbol name (default: "NIFTY")
  - Options: NIFTY, BANKNIFTY, or any NSE stock symbol

**Example:**
```
GET /api/live_nse?symbol=NIFTY
```

**Response:**
```json
{
  "symbol": "NIFTY",
  "last_price": 21850.50
}
```

---

### 3. Historical Data
**GET** `/api/history`

Fetch historical OHLCV candles for charting.

**Parameters:**
- `symbol` (string, optional): Symbol name (default: "NIFTY")
- `interval` (int, optional): Candle interval in minutes (default: 5, range: 1-60)
- `limit` (int, optional): Number of candles (default: 200, range: 10-1000)

**Example:**
```
GET /api/history?symbol=NIFTY&interval=5&limit=100
```

**Response:**
```json
{
  "symbol": "NIFTY",
  "interval": 5,
  "candles": [
    {
      "time": 1701234000,
      "open": 21800.0,
      "high": 21850.0,
      "low": 21780.0,
      "close": 21830.0
    },
    ...
  ]
}
```

---

### 4. Complete Signal Analysis (Main Endpoint)
**GET** `/api/signal_live`

Get comprehensive trading analysis including candles, indicators, ML predictions, options analysis, news, sectors, and more.

**Parameters:**
- `symbol` (string, optional): Symbol name (default: "NIFTY")
- `interval` (int, optional): Candle interval in seconds (default: 60)
- `limit` (int, optional): Number of candles (default: 50)

**Example:**
```
GET /api/signal_live?symbol=NIFTY&interval=300&limit=100
```

**Response Structure:**
```json
{
  "symbol": "NIFTY",
  "interval_sec": 300,
  "price": 21850.50,
  
  "candles": [
    {
      "time": 1701234000,
      "open": 21800.0,
      "high": 21850.0,
      "low": 21780.0,
      "close": 21830.0
    }
  ],
  
  "indicators": {
    "ema9": 21835.0,
    "ema21": 21820.0,
    "ema50": 21800.0,
    "ema200": 21750.0,
    "rsi14": 58.5,
    "macd": 12.5,
    "macd_signal": 10.2,
    "macd_hist": 2.3,
    "atr14": 85.3,
    "bb_upper": 21900.0,
    "bb_lower": 21750.0,
    "bb_width": 150.0,
    "supertrend": 21790.0
  },
  
  "signal": {
    "action": "BUY",
    "confidence": 0.72,
    "bullish_score": 0.68,
    "bearish_score": 0.22,
    "reasons": [
      "Strong EMA uptrend (close > EMA9 > EMA21 > EMA50 > EMA200).",
      "RSI 58.5 (healthy bullish momentum).",
      "MACD above Signal with positive histogram (bullish momentum).",
      ...
    ],
    "mtf": {
      "tf1": 1,
      "tf15": 1
    }
  },
  
  "series": {
    "ema21": [21810.0, 21815.0, 21820.0, ...],
    "ema50": [21790.0, 21795.0, 21800.0, ...],
    "supertrend": [21780.0, 21785.0, 21790.0, ...]
  },
  
  "ml_view": {
    "enabled": true,
    "p1": 0.67,
    "p3": 0.65,
    "p5": 0.62,
    "final_ml_score": 0.65,
    "trend_label": "UP"
  },
  
  "ml_predict": {
    "enabled": true,
    "p1": 0.67,
    "p3": 0.65,
    "p5": 0.62,
    "next_1_up": 0.67,
    "next_3_up": 0.65,
    "next_5_up": 0.62,
    "final_ml_score": 0.65,
    "trend_label": "UP"
  },
  
  "options": {
    "strike": {
      "atm": 21850,
      "otm_call_1": 21900,
      "otm_call_2": 21950,
      "otm_put_1": 21800,
      "otm_put_2": 21750
    },
    "iv": {
      "ce_iv": 18.5,
      "pe_iv": 19.2,
      "trend": "neutral",
      "score": 0.1
    },
    "oi": {
      "ce_oi": 125000,
      "pe_oi": 142000,
      "ce_oi_chg": 5000,
      "pe_oi_chg": -3000,
      "sentiment": "bullish",
      "score": 0.25
    },
    "greeks": {
      "delta": 0.52,
      "gamma": 0.008,
      "theta": -15.3,
      "vega": 42.1
    },
    "order_flow": {
      "flows": ["CE long buildup or writing...", ...],
      "score": 0.3,
      "ce_oi": 125000,
      "pe_oi": 142000,
      "ce_chg": 5000,
      "pe_chg": -3000
    },
    "exp_move": {
      "atr_pct": 0.39,
      "expected_move_pts": 51.2,
      "target_pts": 51.2,
      "sl_pts": 25.6,
      "rr": 2.0
    },
    "signal": {
      "action": "CALL BUY",
      "confidence": 75,
      "buy_call_score": 5.5,
      "buy_put_score": 2.0,
      "reasons": [...]
    }
  },
  
  "options_suggestion": {
    "bias": "Bullish",
    "opt_type": "CALL",
    "recommended_strikes": [21800, 21850, 21900],
    "expiry_hint": "Use nearest weekly expiry for intraday; monthly for positional."
  },
  
  "news": {
    "sentiment_score": 0.35,
    "sentiment_summary": "Moderately positive sentiment from recent news.",
    "headlines": [
      {"title": "Nifty hits new high...", "source": "Economic Times", "sentiment": 0.6},
      ...
    ]
  },
  
  "sector_view": {
    "sector_score": 0.42,
    "sector_comments": "Banking and IT sectors showing strength.",
    "sector_changes": {
      "IT": 1.2,
      "BANKING": 0.8,
      "AUTO": -0.3,
      ...
    }
  },
  
  "global": {
    "data": {
      "nasdaq": {"last": 15234.5, "change_pct": 0.45},
      "crude": {"last": 82.3, "change_pct": -0.22},
      "usdinr": {"last": 83.15, "change_pct": 0.05},
      "nifty_spot": {"last": 21850.5, "change_pct": 0.35}
    },
    "score": 0.28,
    "comments": "Global markets moderately positive."
  },
  
  "vix": {
    "value": 15.8,
    "label": "Medium Risk",
    "comment": "Moderate volatility, normal trading conditions.",
    "risk_score": 0.42
  },
  
  "fii_dii": {
    "score": 0.35,
    "label": "Moderate Buying",
    "comments": ["FII net buyers today", "DII supporting rally"]
  },
  
  "volume_analysis": {
    "score": 0.25,
    "comment": "Volume above average, supporting the move."
  },
  
  "fake_breakout": {
    "score": 0.15,
    "comment": "No fake breakout detected."
  },
  
  "reversal_signals": {
    "detected": false,
    "patterns": [],
    "reasons": []
  },
  
  "reversal_prob": 0.15,
  
  "event_risk": {
    "score": 0.12,
    "next_results": {
      "IT": ["2025-01-15", "2025-01-18"],
      ...
    },
    "reasons": ["TCS results on 15th Jan", ...]
  },
  
  "market_mood": 68,
  
  "regime": {
    "label": "Trending",
    "score": 0.65,
    "atr_pct": 0.39,
    "bb_pct": 0.68
  },
  
  "final": {
    "score": 0.72,
    "label": "Buy (moderate)",
    "note": "Bias is bullish but manage position size.",
    "components": {
      "technical": 0.72,
      "sector": 0.71,
      "news": 0.67,
      "global": 0.64,
      "fii_dii": 0.67,
      "volume": 0.62,
      "breakout": 0.57,
      "vix_factor": 0.58,
      "event_risk": 0.12
    }
  },
  
  "meta": {
    "data_source": "live"
  }
}
```

---

### 5. News Sentiment
**GET** `/api/news_sentiment`

Get latest news headlines and sentiment analysis.

**Parameters:**
- `symbol` (string, optional): Symbol name (default: "NIFTY")

**Example:**
```
GET /api/news_sentiment?symbol=NIFTY
```

**Response:**
```json
{
  "symbol": "NIFTY",
  "sentiment_score": 0.35,
  "summary": "Moderately positive sentiment from recent news.",
  "headlines": [
    {
      "title": "Nifty reaches all-time high amid positive global cues",
      "source": "Economic Times",
      "sentiment": 0.6
    },
    ...
  ]
}
```

---

### 6. Sector View
**GET** `/api/sector_view`

Get sector strength analysis.

**Parameters:**
- `symbol` (string, optional): Symbol name (default: "NIFTY")
- `action` (string, optional): Trade action (default: "BUY")
  - Options: BUY, SELL

**Example:**
```
GET /api/sector_view?symbol=NIFTY&action=BUY
```

**Response:**
```json
{
  "symbol": "NIFTY",
  "action": "BUY",
  "sector_score": 0.42,
  "sector_comments": "Banking and IT sectors showing strength.",
  "sector_changes": {
    "IT": 1.2,
    "BANKING": 0.8,
    "AUTO": -0.3,
    "PHARMA": 0.5,
    "REALTY": -0.1
  }
}
```

---

### 7. WebSocket - Live Data Stream
**WebSocket** `/ws/live`

Real-time streaming of trading data.

**Parameters:**
- `symbol` (string): Symbol name
- `interval` (int): Update interval in seconds

**Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live?symbol=NIFTY&interval=5');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Live update:', data);
};
```

**Message Format:**
Same as `/api/signal_live` response structure.

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "error": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Endpoint not found
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Currently, no rate limiting is implemented. For production:
- Implement rate limiting (e.g., 100 requests/minute)
- Use API keys for authentication
- Monitor usage patterns

---

## Caching

The API uses intelligent caching to reduce load:
- **NSE Price**: 1 second TTL
- **News**: 60 seconds TTL
- **Sector Data**: 30 seconds TTL
- **Global Cues**: 30 seconds TTL
- **VIX**: 30 seconds TTL
- **FII/DII**: 60 seconds TTL
- **Earnings**: 300 seconds (5 minutes) TTL

---

## Best Practices

1. **Use WebSocket for real-time updates** instead of polling `/api/signal_live`
2. **Cache responses** on the client side when appropriate
3. **Handle fallback data** - API returns sample data if live data fails
4. **Check `meta.data_source`** to know if data is "live" or "fallback"
5. **Implement retry logic** for network failures
6. **Validate inputs** before making API calls

---

## Examples

### Python
```python
import requests

# Get live signal
response = requests.get('http://localhost:8000/api/signal_live', params={
    'symbol': 'NIFTY',
    'interval': 300,
    'limit': 100
})

data = response.json()
print(f"Signal: {data['signal']['action']}")
print(f"Confidence: {data['signal']['confidence']}")
```

### JavaScript
```javascript
// Fetch historical data
fetch('http://localhost:8000/api/history?symbol=NIFTY&interval=5&limit=200')
  .then(response => response.json())
  .then(data => {
    console.log('Candles:', data.candles);
  });

// Get live NSE price
async function getLivePrice(symbol) {
  const response = await fetch(`http://localhost:8000/api/live_nse?symbol=${symbol}`);
  const data = await response.json();
  return data.last_price;
}
```

### cURL
```bash
# Health check
curl http://localhost:8000/api/health

# Get signal
curl "http://localhost:8000/api/signal_live?symbol=NIFTY&interval=60&limit=50"

# Get news
curl "http://localhost:8000/api/news_sentiment?symbol=BANKNIFTY"
```

---

## Support

For issues or questions, please open an issue on GitHub:
https://github.com/yourusername/trading-assistant/issues
