import time
from collections import deque
from typing import Dict, Deque, List

# One OHLC candle structure
class Candle:
    def __init__(self, start_ts: float, price: float):
        self.start_ts = start_ts  # unix timestamp (seconds)
        self.open = price
        self.high = price
        self.low = price
        self.close = price

    def to_dict(self):
        return {
            "start_ts": self.start_ts,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close
        }

# Per-symbol state
class CandleEngine:
    def __init__(self, interval_sec: int = 60, max_candles: int = 100):
        self.interval_sec = interval_sec
        self.max_candles = max_candles
        self.current_candle: Candle | None = None
        self.candles: Deque[Candle] = deque()

    def update_with_price(self, price: float, now: float | None = None):
        if now is None:
            now = time.time()

        if self.current_candle is None:
            # first tick -> start new candle
            self.current_candle = Candle(start_ts=now, price=price)
            return

        # Check if this tick still belongs to current candle
        if now - self.current_candle.start_ts < self.interval_sec:
            # update OHLC
            self.current_candle.high = max(self.current_candle.high, price)
            self.current_candle.low = min(self.current_candle.low, price)
            self.current_candle.close = price
        else:
            # close current candle and start a new one
            self.candles.append(self.current_candle)
            # keep only last max_candles
            while len(self.candles) > self.max_candles:
                self.candles.popleft()
            self.current_candle = Candle(start_ts=now, price=price)

    def get_candles(self, include_current: bool = True) -> List[Dict]:
        result = [c.to_dict() for c in self.candles]
        if include_current and self.current_candle is not None:
            result.append(self.current_candle.to_dict())
        return result

# Global registry: one engine per symbol+interval
_engines: Dict[str, CandleEngine] = {}

def get_engine(symbol: str, interval_sec: int, max_candles: int = 100) -> CandleEngine:
    """
    Get or create a candle engine for symbol+interval.
    On first creation, pre-populate with historical data from yfinance.
    """
    key = f"{symbol.upper()}_{interval_sec}"
    if key not in _engines:
        print(f"🔧 Creating new engine for {key} with max_candles={max_candles}")
        engine = CandleEngine(interval_sec=interval_sec, max_candles=max_candles)
        # Pre-populate with historical data
        _prepopulate_engine(engine, symbol, interval_sec, max_candles)
        print(f"📊 Engine {key} now has {len(engine.candles)} historical candles")
        _engines[key] = engine
    else:
        print(f"♻️ Reusing existing engine for {key} with {len(_engines[key].candles)} candles")
    return _engines[key]


def _prepopulate_engine(engine: CandleEngine, symbol: str, interval_sec: int, max_candles: int):
    """
    Pre-populate engine with historical candles from yfinance to provide
    sufficient data for technical indicators (RSI needs 14+, EMA200 needs 200+).
    """
    try:
        import yfinance as yf
        import pandas as pd
        
        # Map symbol to Yahoo Finance ticker
        ticker_map = {
            "NIFTY": "^NSEI",
            "BANKNIFTY": "^NSEBANK",
        }
        ticker = ticker_map.get(symbol.upper(), f"{symbol.upper()}.NS")
        
        # Convert interval_sec to yfinance interval format
        # Ensure we get enough data for indicators (RSI needs 14+, EMA200 needs 200+)
        if interval_sec <= 60:
            interval_str = "1m"
            period = "5d"  # Get more 1-minute data
        elif interval_sec <= 300:
            interval_str = "5m"
            period = "60d"  # 60 days of 5-minute data (more than enough)
        elif interval_sec <= 900:
            interval_str = "15m"
            period = "60d"
        elif interval_sec <= 3600:
            interval_str = "1h"
            period = "730d"  # 2 years
        else:
            interval_str = "1d"
            period = "max"  # Max daily data
        
        # Download historical data
        df = yf.download(ticker, period=period, interval=interval_str, auto_adjust=True, progress=False)
        
        if df.empty:
            print(f"⚠️ No historical data available for {symbol} from yfinance")
            return
        
        # Flatten MultiIndex columns if they exist
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Take last max_candles rows
        df = df.tail(max_candles)
        
        # Convert to Candle objects and add to engine
        for i in range(len(df)):
            ts = int(df.index[i].timestamp())
            open_price = float(df.iloc[i]['Open'])
            high_price = float(df.iloc[i]['High'])
            low_price = float(df.iloc[i]['Low'])
            close_price = float(df.iloc[i]['Close'])
            
            # Create candle and add to history
            candle = Candle(start_ts=ts, price=open_price)
            candle.high = high_price
            candle.low = low_price
            candle.close = close_price
            engine.candles.append(candle)
        
        print(f"✅ Pre-populated {len(engine.candles)} historical candles for {symbol}")
        
    except Exception as e:
        print(f"⚠️ Failed to pre-populate {symbol}: {e}")
