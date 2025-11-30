# 🧪 API Endpoint Testing Guide

## Quick Test Commands

### 1. Health Check
```bash
curl http://localhost:8000/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "ml_loaded": true,
  "timestamp": "2025-01-27T12:00:00"
}
```

---

### 2. Live Signal (Main Endpoint)
```bash
# NIFTY
curl "http://localhost:8000/api/signal_live?symbol=NIFTY"

# BANKNIFTY
curl "http://localhost:8000/api/signal_live?symbol=BANKNIFTY"
```

**Expected Response Structure:**
```json
{
  "symbol": "NIFTY",
  "price": 21500.50,
  "timestamp": "2025-01-27 12:00:00",
  "signal": "BUY/SELL/WAIT",
  "confidence": 85,
  "candles": [...],
  "indicators": {
    "rsi": 65.5,
    "ema_9": 21480.2,
    "ema_21": 21450.1,
    "macd": {...},
    "bollinger": {...}
  },
  "ml_view": {
    "enabled": true,
    "final_ml_score": 0.75,
    "horizons": {
      "1min": {"rf": 0.8, "xgb": 0.7, "lr": 0.6},
      "3min": {...},
      "5min": {...}
    }
  },
  "ml_predict": {
    "enabled": true,
    "signal": "BUY",
    "score": 0.75
  },
  "options": {
    "atm_strike": 21500,
    "ce_oi": 1000000,
    "pe_oi": 1200000,
    "pcr": 1.2,
    "max_pain": 21450,
    "call_writers": 800000,
    "put_writers": 950000
  },
  "news": [...],
  "global": {...},
  "sector": {...}
}
```

---

### 3. Paper Trading - Stats
```bash
curl http://localhost:8000/api/paper/stats
```

**Expected Response:**
```json
{
  "total_trades": 10,
  "open_positions": 2,
  "closed_trades": 8,
  "win_rate": 62.5,
  "total_pnl": 15000.50,
  "roi": 15.0,
  "current_capital": 115000.50
}
```

---

### 4. Paper Trading - Open Position
```bash
curl -X POST "http://localhost:8000/api/paper/open" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NIFTY",
    "action": "BUY",
    "entry_price": 21500,
    "quantity": 50,
    "stop_loss": 21400,
    "take_profit": 21650
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "position_id": "abc123",
  "message": "Position opened"
}
```

---

### 5. Paper Trading - Update Positions
```bash
curl -X POST "http://localhost:8000/api/paper/update" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NIFTY",
    "current_price": 21550
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "closed_positions": ["abc123"],
  "message": "Positions updated, 1 closed"
}
```

---

### 6. Paper Trading - Close Position
```bash
curl -X POST "http://localhost:8000/api/paper/close" \
  -H "Content-Type: application/json" \
  -d '{
    "position_id": "abc123",
    "exit_price": 21550
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "pnl": 2500.0,
  "message": "Position closed"
}
```

---

### 7. Paper Trading - Reset
```bash
curl -X POST "http://localhost:8000/api/paper/reset"
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Paper trading reset to initial capital"
}
```

---

### 8. Backtest (Terminal)
```bash
cd backend
python backtest_signals.py
```

**Expected Output:**
```
✅ ML models loaded successfully
📊 Running backtest with ML enabled...

========== BACKTEST RESULTS ==========
Total Trades: 50
Winning Trades: 32
Losing Trades: 18
Win Rate: 64.0%
Total Return: 15.5%

========== ML ENHANCED RESULTS ==========
ML Trades: 50
ML Win Rate: 68.0%
Improvement: +4.0% win rate
ML Return: 18.2%
Return Improvement: +2.7%
```

---

### 9. Train Models (Terminal)
```bash
cd backend
python -c "from ml.train_ml import train_all; train_all()"
```

**Expected Output:**
```
🚀 Training ML models...
📊 Loaded dataset: 2920 samples
✅ Trained RF model (1min): accuracy=0.78
✅ Trained XGB model (1min): accuracy=0.76
✅ Trained LR model (1min): accuracy=0.72
✅ Metrics saved: models/metrics/rf_1_metrics.json
...
🎉 Training complete! 9 models saved.
```

---

### 10. WebSocket Test (JavaScript)

**Browser Console:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live?symbol=NIFTY');

ws.onmessage = (event) => {
  console.log('📨 Received:', JSON.parse(event.data));
};

ws.onopen = () => console.log('✅ WebSocket connected');
ws.onerror = (err) => console.error('❌ WebSocket error:', err);
```

**Expected Messages (every 5 seconds):**
```json
{
  "symbol": "NIFTY",
  "price": 21500.50,
  "signal": "BUY",
  "timestamp": "2025-01-27 12:00:00",
  "indicators": {...},
  "ml_view": {...}
}
```

---

## Python Test Script

Create `backend/test_api.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    print("\n🔍 Testing Health Endpoint...")
    r = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    assert r.status_code == 200
    print("✅ Health check passed")

def test_signal_live():
    print("\n🔍 Testing Signal Live Endpoint...")
    r = requests.get(f"{BASE_URL}/api/signal_live?symbol=NIFTY")
    print(f"Status: {r.status_code}")
    data = r.json()
    
    # Check required fields
    required = ["symbol", "price", "signal", "candles", "indicators", 
                "ml_view", "ml_predict", "options", "news", "global", "sector"]
    missing = [f for f in required if f not in data]
    
    if missing:
        print(f"❌ Missing fields: {missing}")
    else:
        print("✅ All required fields present")
    
    print(f"Signal: {data.get('signal')}")
    print(f"ML Score: {data.get('ml_predict', {}).get('score')}")
    assert r.status_code == 200

def test_paper_trading():
    print("\n🔍 Testing Paper Trading...")
    
    # Get stats
    r = requests.get(f"{BASE_URL}/api/paper/stats")
    print(f"Stats: {r.json()}")
    
    # Open position
    r = requests.post(f"{BASE_URL}/api/paper/open", json={
        "symbol": "NIFTY",
        "action": "BUY",
        "entry_price": 21500,
        "quantity": 50,
        "stop_loss": 21400,
        "take_profit": 21650
    })
    print(f"Open Position: {r.json()}")
    position_id = r.json().get("position_id")
    
    # Update
    r = requests.post(f"{BASE_URL}/api/paper/update", json={
        "symbol": "NIFTY",
        "current_price": 21550
    })
    print(f"Update: {r.json()}")
    
    # Close
    if position_id:
        r = requests.post(f"{BASE_URL}/api/paper/close", json={
            "position_id": position_id,
            "exit_price": 21550
        })
        print(f"Close: {r.json()}")
    
    print("✅ Paper trading tests passed")

if __name__ == "__main__":
    try:
        test_health()
        test_signal_live()
        test_paper_trading()
        print("\n🎉 All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
```

**Run:**
```bash
cd backend
pip install requests
python test_api.py
```

---

## Frontend Manual Test Checklist

1. **Open Frontend**: http://localhost:3000
2. **Check Chart Loading**: Should see candlestick chart rendering
3. **Check Symbol Switch**: Click NIFTY/BANKNIFTY cards
4. **Check Live Updates**: Price should update every 5 seconds
5. **Check Indicators**: RSI, MACD, Bollinger Bands visible
6. **Check ML View**: ML scores displayed
7. **Check Options Chain**: OI, PCR, Max Pain displayed
8. **Check News**: Recent news articles loaded
9. **Check Global Cues**: GIFT Nifty, US indices
10. **Check Sectors**: Sector performance shown

---

## Common Issues & Fixes

### 1. ML Models Not Loaded
**Error:** `ML pipeline unavailable`

**Fix:**
```bash
cd backend
python -c "from ml.train_ml import train_all; train_all()"
```

### 2. Chart Not Rendering
**Error:** Blank chart area

**Fix:**
- Check browser console (F12)
- Verify Lightweight Charts CDN loaded
- Check API returns candles: `curl http://localhost:8000/api/signal_live?symbol=NIFTY | jq '.candles'`

### 3. API Returns Empty Data
**Error:** `{"options": null, "news": []}`

**Fix:**
- Check backend logs for errors
- Verify data sources accessible
- Check fallback data: `backend/fallback_data.py`

### 4. Paper Trading Not Persisting
**Error:** Stats reset on restart

**Fix:**
- Check `paper_trading/` directory exists
- Verify JSON files have write permissions
- Check logs for file write errors

### 5. WebSocket Disconnects
**Error:** WebSocket closes frequently

**Fix:**
- Check nginx timeout settings
- Increase `proxy_read_timeout` to 86400s
- Check backend keep-alive settings

---

## Automated Testing (Future)

### Pytest Setup
```bash
pip install pytest pytest-asyncio httpx
```

Create `backend/tests/test_api.py`:
```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_signal_live():
    response = client.get("/api/signal_live?symbol=NIFTY")
    assert response.status_code == 200
    data = response.json()
    assert "signal" in data
    assert "ml_view" in data
```

**Run:**
```bash
pytest backend/tests/
```

---

## Performance Testing

### Load Test with Apache Bench
```bash
# Install ab (Apache Bench)
# Ubuntu: sudo apt install apache2-utils
# Mac: brew install ab

# Test signal endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 http://localhost:8000/api/signal_live?symbol=NIFTY
```

**Expected Performance:**
- Requests per second: > 50
- Mean response time: < 200ms
- Failed requests: 0

---

## Monitoring

### Check Backend Logs
```bash
# Docker
docker logs -f trading_backend

# Direct
tail -f backend/logs/app.log
```

### Check Resource Usage
```bash
# Docker
docker stats trading_backend

# System
htop
```

---

**Happy Testing! 🧪**
