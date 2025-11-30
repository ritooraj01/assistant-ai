# ML Model Training Guide

## 📚 Overview
Train Random Forest models to predict NIFTY price direction for 1, 3, and 5 candles ahead.

## 🚀 Quick Start (3 Steps)

### Step 1: Prepare Training Data
Download historical NIFTY data and compute indicators:

```bash
cd d:\App\backend\ml_model
python prepare_training_data.py
```

**What this does:**
- Downloads 3 months of NIFTY 5m data from Yahoo Finance
- Computes all technical indicators (EMA, RSI, MACD, ATR, Bollinger Bands, etc.)
- Saves to `nifty_training_5m.csv`
- Typically generates ~3,000-5,000 candles

**Parameters you can adjust** (in the script):
- `period`: "1mo", "3mo", "6mo", "1y" (more data = better model)
- `interval`: "5m", "15m", "1h" (match your trading timeframe)

---

### Step 2: Train ML Models
Train 3 Random Forest models (1-candle, 3-candle, 5-candle predictions):

```bash
python train_ml.py
```

**What this does:**
- Builds 12 features per candle (returns, wicks, EMA ratios, RSI, MACD, ATR, BB width)
- Trains 3 Random Forest models (120 trees each, max depth 8)
- Saves model files:
  - `rf_1c.pkl` - Predicts next 1 candle direction
  - `rf_3c.pkl` - Predicts next 3 candles direction
  - `rf_5c.pkl` - Predicts next 5 candles direction
- Shows training accuracy for each model

**Training time:** ~10-30 seconds

---

### Step 3: Restart Backend
Restart your backend server to load the new models:

```bash
cd d:\App\backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

You should see:
```
✅ ML models loaded successfully
```

---

## 📊 Features Used for Prediction

The models use these 12 features:

1. **ret** - Price return (close change %)
2. **body_pct** - Candle body as % of range
3. **upper_wick_pct** - Upper wick as % of range
4. **lower_wick_pct** - Lower wick as % of range
5. **ema9_ratio** - Close / EMA9
6. **ema21_ratio** - Close / EMA21
7. **ema50_ratio** - Close / EMA50
8. **rsi14** - RSI indicator (0-100)
9. **macd** - MACD line
10. **macd_hist** - MACD histogram
11. **atr_pct** - ATR as % of price
12. **bb_width_pct** - Bollinger Band width as % of price

---

## 🎯 Model Output

Each model predicts probability (0-1) of price going UP:

- **next_1_up**: Probability next candle closes higher
- **next_3_up**: Probability 3 candles ahead is higher
- **next_5_up**: Probability 5 candles ahead is higher
- **final_ml_score**: Weighted average (40% × 1c + 35% × 3c + 25% × 5c)

**Signal interpretation:**
- `final_ml_score > 0.65` → Strong bullish (adds +0.15 to signal confidence)
- `final_ml_score < 0.35` → Strong bearish (adds +0.15 to signal confidence)
- `0.35 - 0.65` → Neutral (no boost)

**Smoothing:**
- Predictions are smoothed using exponential averaging (30% previous + 70% current)
- Reduces jitter and improves stability

---

## 📈 Improving Model Performance

### Get More Data
```python
# In prepare_training_data.py, change:
prepare_training_dataset(
    period="6mo",  # or "1y" for more data
    interval="5m"
)
```

### Match Your Trading Timeframe
If you trade 15m charts, use 15m data:
```python
prepare_training_dataset(
    period="6mo",
    interval="15m"
)
```

### Retrain Periodically
- Markets change over time
- Retrain monthly with fresh data
- Keep old models as backup

---

## 🔍 Troubleshooting

### "No such file: nifty_training_5m.csv"
Run `python prepare_training_data.py` first

### "Not enough data to train"
Use longer period: `period="6mo"` or `period="1y"`

### "ML models not found"
Make sure `.pkl` files are in `d:\App\backend\ml_model\` directory

### Models give poor predictions
- Needs more training data (use period="6mo" or "1y")
- Market conditions changed (retrain with recent data)
- Consider feature engineering (add more indicators)

---

## 🎓 Technical Details

**Algorithm:** Random Forest Classifier
- Ensemble of 120 decision trees
- Max depth: 8 levels
- Class weights: Balanced (handles imbalanced data)
- Min samples per leaf: 5

**Why Random Forest?**
- ✅ Handles non-linear patterns
- ✅ Robust to overfitting
- ✅ Works well with technical indicators
- ✅ Fast prediction (real-time capable)
- ✅ No need for feature scaling

**Labels:**
- Binary classification: 1 = Price goes UP, 0 = Price goes DOWN
- Calculated from future close prices

---

## 📝 Files Generated

After training, you'll have:
```
ml_model/
├── prepare_training_data.py   (Step 1 script)
├── train_ml.py                 (Step 2 script)
├── predict_ml.py               (Prediction logic - already exists)
├── nifty_training_5m.csv       (Training dataset with indicators)
├── rf_1c.pkl                   (1-candle prediction model)
├── rf_3c.pkl                   (3-candle prediction model)
└── rf_5c.pkl                   (5-candle prediction model)
```

---

## 🚀 Next Steps After Training

1. ✅ **Restart backend** - Models auto-load on startup
2. ✅ **Refresh frontend** - ML progress bars will show live predictions
3. ✅ **Monitor signals** - ML influences signal confidence by ±0.15
4. ✅ **Check conflict resolution** - ML predictions resolve signal conflicts

---

## 💡 Pro Tips

1. **Test before live trading** - Verify predictions make sense
2. **Combine with other signals** - ML is one input, not the only input
3. **Watch for overfitting** - If training accuracy > 95%, model may be overfitted
4. **Update regularly** - Retrain monthly with fresh market data
5. **Check smoothing** - Compare `raw_ml_score` vs `final_ml_score` to see smoothing effect

---

Good luck with your ML-powered trading! 🎯📈
