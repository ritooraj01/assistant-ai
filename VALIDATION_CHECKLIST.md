# Validation Checklist - New Specification Implementation

## Backend Changes ✅

### 1. Data Validator (`data_validator.py`)
- ✅ Updated `normalize_price_data()` to return new schema:
  - `lastPrice`: Always present (never None/blank)
  - `prevClose`: float or None
  - `pctChange`: float or None
  - `pctChangeAvailable`: boolean (false if prevClose invalid or anomaly >40%)
  - `anomaly`: boolean (true if >40% change detected)
  - `error`: string or None

### 2. Sectors (`sectors.py`)
- ✅ Uses `normalize_price_data()` for validation
- ✅ Returns `lastPrice` always
- ✅ Returns `pct_change_available` flag
- ✅ Returns `anomaly` flag
- ✅ Skips only if lastPrice is None (invalid data)

### 3. Global Markets (`global_cues.py`)
- ✅ USD/INR validation with 70-95 range check
- ✅ Still sends `lastPrice` even if pctChangeAvailable=false
- ✅ Adds `pct_change_available` flag to all markets
- ✅ Adds `proxy: true` flag for SGX/GIFT when mirroring
- ✅ Adds `quality_warning` for USD/INR validation failures

### 4. Main API (`main.py`)
- ✅ Validates indicators and returns `indicators_available` flag
- ✅ Gates reasoning generation with `can_generate_reasoning()`
- ✅ Response includes `indicators_available: boolean`

## Frontend Changes ✅

### 1. Price Display (`formatMarket()`)
- ✅ Always shows `lastPrice` if available
- ✅ Shows "—%" badge when `pct_change_available: false`
- ✅ Shows "⚠" badge for `quality_warning: true`
- ✅ Shows "(proxy)" badge when `proxy: true`
- ✅ Normal display when valid with % change

### 2. Indicator Display
- ✅ RSI: Shows value when `indicators_available: true`, else "—"
- ✅ ATR: Shows value when `indicators_available: true`, else "—"
- ✅ MACD: Shows histogram when `indicators_available: true`, else "—"
- ✅ Bollinger: Shows % when `indicators_available: true`, else "—"
- ✅ All indicators have tooltips explaining "unavailable (insufficient candles)"

### 3. Signal Reasoning (`updateReasons()`)
- ✅ Checks `indicators_available` flag
- ✅ When false: Shows "Based on last price ₹X, indicators insufficient — waiting for more data"
- ✅ When true: Shows normal technical reasoning

### 4. Chart Persistence
- ✅ Symbol change: Clears data, checks initialization, rebinds
- ✅ Interval change: Clears data, checks initialization, rebinds
- ✅ Heartbeat monitor: Detects missing canvas, reinitializes
- ✅ Auto-recovery: Validates series references, resets on error
- ✅ ResizeObserver: Responsive sizing with proper constraints

### 5. UI Clarity
- ✅ Header badge: title="Currently viewing symbol"
- ✅ Sidebar NIFTY card: title="Click to switch to NIFTY 50"
- ✅ SGX/GIFT: Shows "(proxy)" label when mirroring

## Test Cases

### Price Display Tests
- [ ] **Test 1**: HDFC with prevClose=0
  - Expected: Shows lastPrice, displays "—%" badge
  - Actual: _______

- [ ] **Test 2**: Stock with valid prevClose
  - Expected: Shows lastPrice with % change normally
  - Actual: _______

- [ ] **Test 3**: Stock with >40% change (anomaly)
  - Expected: Shows lastPrice, displays "—%" badge, anomaly=true
  - Actual: _______

### Indicator Tests
- [ ] **Test 4**: Start fresh (< 14 candles)
  - Expected: All indicators show "—", tooltip says "insufficient candles"
  - Actual: _______

- [ ] **Test 5**: After 20 candles collected
  - Expected: RSI, ATR, MACD, Bollinger show values
  - Actual: _______

### USD/INR Tests
- [ ] **Test 6**: USD/INR = 89.36 (outside 70-95)
  - Expected: Shows lastPrice 89.36, displays "⚠" badge, no % change
  - Actual: _______

- [ ] **Test 7**: USD/INR = 83.50 (within range)
  - Expected: Shows lastPrice with % change normally
  - Actual: _______

### SGX/GIFT Tests
- [ ] **Test 8**: GIFT Nifty mirroring NIFTY spot
  - Expected: Shows value with "(proxy)" badge
  - Actual: _______

- [ ] **Test 9**: GIFT Nifty with distinct value
  - Expected: Shows value without "(proxy)" badge
  - Actual: _______

### Signal Reasoning Tests
- [ ] **Test 10**: Start fresh (indicators_available=false)
  - Expected: "Based on last price ₹X, indicators insufficient — waiting for more data"
  - Actual: _______

- [ ] **Test 11**: After indicators available
  - Expected: Normal technical reasoning (RSI, MACD, trend analysis)
  - Actual: _______

### Chart Persistence Tests
- [ ] **Test 12**: Switch from NIFTY to INFY
  - Expected: Chart clears, reloads with new symbol data, stays visible
  - Actual: _______

- [ ] **Test 13**: Switch interval from 5m to 15m
  - Expected: Chart clears, reloads with new interval, stays visible
  - Actual: _______

- [ ] **Test 14**: Simulate 40s no updates (stale feed)
  - Expected: Heartbeat detects, auto-reconnects, chart persists
  - Actual: _______

- [ ] **Test 15**: Manually remove canvas from DOM
  - Expected: Heartbeat detects, reinitializes chart
  - Actual: _______

### Chart Overflow Tests
- [ ] **Test 16**: Resize window to 400px width
  - Expected: Chart resizes smoothly, no overflow, min 300px enforced
  - Actual: _______

- [ ] **Test 17**: Mobile viewport (480px)
  - Expected: Chart fits within max-height:360px, no scrollbars
  - Actual: _______

### UI Clarity Tests
- [ ] **Test 18**: Hover over header symbol badge
  - Expected: Tooltip shows "Currently viewing symbol"
  - Actual: _______

- [ ] **Test 19**: Hover over sidebar NIFTY card
  - Expected: Tooltip shows "Click to switch to NIFTY 50"
  - Actual: _______

## Data Contract Verification

### Example API Response (should match):
```json
{
  "symbol": "HDFC",
  "price": 1006.70,
  "indicators": {
    "rsi14": null,
    "atr14": null,
    "macd": null,
    "macd_signal": null,
    "macd_hist": null
  },
  "indicators_available": false,
  "signal": {
    "action": "WAIT",
    "confidence": 0.3,
    "reasons": []
  },
  "global": {
    "data": {
      "nifty_spot": {
        "last": 24350.50,
        "change_pct": 0.45,
        "pct_change_available": true
      },
      "gift_nifty": {
        "last": 24350.50,
        "change_pct": 0.45,
        "pct_change_available": true,
        "proxy": true
      },
      "usdinr": {
        "last": 89.36,
        "change_pct": null,
        "pct_change_available": false,
        "quality_warning": true
      }
    }
  }
}
```

### Sector Response Example:
```json
{
  "BANKS": {
    "index_name": "NIFTY BANK",
    "last": 51245.80,
    "change_pct": 0.75,
    "pct_change_available": true,
    "anomaly": false
  },
  "IT": {
    "index_name": "NIFTY IT",
    "last": 34567.00,
    "change_pct": null,
    "pct_change_available": false,
    "anomaly": true
  }
}
```

## Known Limitations

1. **SGX/GIFT Proxy**: Until dedicated API feeds are integrated, will show `proxy: true` when mirroring NIFTY spot
2. **Indicator Warm-up**: First 14-20 candles will show indicators_available=false
3. **USD/INR Range**: Hard-coded to 70-95 range, may need adjustment for extreme market conditions
4. **Chart Recovery**: 500ms delay after reinitialization before reloading data

## Success Criteria

✅ **All tests pass** in checklist above
✅ **No extreme percentages** displayed (HDFC -96%, Adani +745%)
✅ **No zero-price equities** visible
✅ **Indicators show "—"** when insufficient data
✅ **Signal reasoning gated** by indicator availability
✅ **Chart persists** after symbol/interval changes
✅ **Chart does not overflow** container
✅ **SGX/GIFT clearly marked** as proxy
✅ **USD/INR shows price** but suppresses invalid % change
✅ **NIFTY entries have tooltips** explaining their purpose

## Deployment Steps

1. ✅ Backend server reloaded automatically (uvicorn --reload detected changes)
2. ⏳ Frontend: Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
3. ⏳ Test all scenarios in checklist
4. ⏳ Monitor console logs for validation warnings (⚠️ prefixed)
5. ⏳ Verify no errors in browser console

---

**Status**: Implementation Complete ✅  
**Date**: November 30, 2025  
**Version**: 2.2.0 (New Specification)  
**Next**: Manual Testing Required
