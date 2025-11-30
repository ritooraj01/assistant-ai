# Trading Dashboard - Complete Guide

## ✅ What's Been Added

### **Left Sidebar** (All the things you asked for!)

1. **🌍 Global Markets**
   - Gift Nifty (with % change)
   - Nasdaq (with % change)
   - Crude Oil (with % change)
   - USD/INR (with % change)
   - Shows in GREEN (positive) or RED (negative)

2. **📊 Market Regime**
   - Shows: High Volatility / Normal / Low Volatility
   - Explains what it means in plain language
   - Based on ATR (Average True Range) indicator

3. **🏢 Sector Performance**
   - Shows top sectors (Bank, IT, Auto, Pharma)
   - Displays % change for each sector
   - Color-coded: Green (up), Red (down)
   - **NOTE**: Currently showing placeholder data - backend needs to provide actual sector data

4. **📈 Options Signal** (For your options trading!)
   - Action: BUY/SELL/AVOID
   - Strike Price
   - IV (Implied Volatility)
   - OI Sentiment (Open Interest)

### **Main Content Area**

1. **Big Action Card** - Tells you BUY/SELL/WAIT immediately
2. **Live Price + Full Chart** - Real-time candlestick chart (350px on desktop, 250px on mobile)
3. **AI Predictions** - Next 1, 3, and 5 candle predictions
4. **Why This Signal?** - Plain language explanations (no jargon!)
5. **Market Overview** - Quick mood, news, volatility, FII flow
6. **Latest Headlines** - Top 8 news items

## 🔧 Chart Troubleshooting

### Why Chart Might Not Show:

1. **Backend not running** → Backend is NOW running on http://127.0.0.1:8000
2. **TradingView library not loaded** → Check browser console (F12) for errors
3. **Container width is 0** → Open browser console and look for "Initializing chart, container width: X"

### To Debug Chart:

1. Open your browser
2. Press F12 (open Developer Tools)
3. Go to Console tab
4. Look for these messages:
   - "Initializing chart, container width: XXX" → Should be > 0
   - "Chart library not loaded" → Means CDN failed
   - "Data received:" → Shows what backend sent

## 📱 Mobile Friendly

- **Desktop**: Sidebar on left, main content on right
- **Tablet** (< 1024px): Sidebar moves to top in 2-column grid
- **Mobile** (< 768px): Everything stacks vertically
- **Small Mobile** (< 480px): Optimized for small screens

## 🎨 Color Scheme

- **Background**: Pure black (#0a0a0a)
- **Cards**: Dark gray (#1a1a1a)
- **Borders**: Subtle gray (#2a2a2a)
- **Green**: Bullish/Positive (#22c55e)
- **Red**: Bearish/Negative (#ef4444)
- **Yellow**: Neutral/Wait (#fbbf24)
- **Purple**: Timeframe buttons (#667eea)

## 🚀 How to Use

### Open Dashboard:
1. Make sure backend is running: `cd d:\App\backend; uvicorn main:app --reload`
2. Open `d:\App\frontend\index.html` in browser (or use Live Server)
3. Dashboard auto-refreshes every 3 seconds

### For Stock Scalping & Options Trading:

**Left Sidebar Shows:**
- Global market sentiment (Gift Nifty, Nasdaq) - Is global market helping or hurting?
- Market Regime - High volatility = more profit opportunity but more risk
- Sector Performance - Which sectors are hot today?
- Options Signal - Specific options trading recommendation

**Main Area Shows:**
- Big BUY/SELL/WAIT signal with confidence %
- Live chart to see price action
- AI predictions for next candles
- Plain language reasons (no RSI/MACD jargon!)

### Timeframe Buttons:
- Click **1m** for super-fast scalping
- Click **3m** for quick trades
- Click **5m** (default) for slightly longer trades

## 🐛 Known Issues

1. **Sectors showing placeholder data**
   - Backend needs to return actual sector data
   - Current format needed:
   ```json
   "sectors": [
     {"name": "Bank", "change": 2.3},
     {"name": "IT", "change": -1.2}
   ]
   ```

2. **Crude Oil might show "N/A"**
   - Backend's global_cues.crude sometimes returns empty
   - Dashboard now shows "--" instead of breaking

## 📝 Files Modified

1. **index.html** - Added sidebar layout with all sections
2. **styles.css** - Added sidebar styles + responsive grid
3. **script.js** - Added functions to populate:
   - updateGlobalMarkets()
   - updateMarketRegime()
   - updateSectors()
   - updateOptions()

## 🔍 What to Check Next

1. Open browser console (F12) and look for:
   - "Initializing chart" message
   - "Data received:" with full JSON
   - Any red error messages

2. If chart still doesn't show:
   - Check if TradingView CDN is blocked
   - Try opening: https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js
   - Should download a JavaScript file

3. If sectors show wrong data:
   - Backend needs to be updated to return actual sector performance
   - File to modify: backend/sectors.py or backend/main.py

## 💡 Tips

- **For Scalping**: Use 1m timeframe, watch for high confidence signals (>70%)
- **For Options**: Check Options Signal in sidebar + Market Regime (avoid high volatility if new)
- **For Sectors**: Watch which sector is strongest, trade stocks in that sector
- **Mobile Trading**: Dashboard works great on phone - all key info visible

---

**Backend Status:** ✅ Running on http://127.0.0.1:8000
**Auto-refresh:** Every 3 seconds
**Chart Library:** TradingView Lightweight Charts v4.1.3
