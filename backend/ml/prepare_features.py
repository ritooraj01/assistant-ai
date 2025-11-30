"""Feature engineering pipeline for the trading assistant ML models."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILES = {
    "nifty": DATA_DIR / "nifty_ml.csv",
    "banknifty": DATA_DIR / "banknifty_ml.csv",
}
INPUT_FILES = {
    "nifty": DATA_DIR / "nifty_5m.csv",
    "banknifty": DATA_DIR / "banknifty_5m.csv",
}


# ---------------------------------------------------------------------------
# Indicator helpers
# ---------------------------------------------------------------------------

def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = pd.Series(gain, index=series.index).rolling(window=period).mean()
    avg_loss = pd.Series(loss, index=series.index).rolling(window=period).mean()
    rs = avg_gain / (avg_loss.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


def _macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
    ema_fast = _ema(series, fast)
    ema_slow = _ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _ema(macd_line, signal)
    return macd_line, signal_line


def _bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    mid = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return mid, upper, lower


def _supertrend(df: pd.DataFrame, period: int = 14, multiplier: float = 3.0) -> pd.Series:
    atr = _atr(df, period)
    hl2 = (df["high"] + df["low"]) / 2
    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(1, index=df.index)

    for i in range(period, len(df)):
        prev = i - 1
        if df["close"].iloc[i] > upperband.iloc[prev]:
            direction.iloc[i] = 1
        elif df["close"].iloc[i] < lowerband.iloc[prev]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[prev]
            if direction.iloc[i] > 0 and lowerband.iloc[i] < lowerband.iloc[prev]:
                lowerband.iloc[i] = lowerband.iloc[prev]
            if direction.iloc[i] < 0 and upperband.iloc[i] > upperband.iloc[prev]:
                upperband.iloc[i] = upperband.iloc[prev]

        supertrend.iloc[i] = lowerband.iloc[i] if direction.iloc[i] > 0 else upperband.iloc[i]

    supertrend = supertrend.ffill()
    return supertrend


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.sort_values("timestamp")
    df.set_index(pd.to_datetime(df["timestamp"]), inplace=True)

    df["return"] = df["close"].pct_change()
    df["log_return"] = np.log(df["close"]).diff()
    df["pct_change"] = df["close"].pct_change()
    df["volatility_20"] = df["return"].rolling(window=20).std()

    df["ema_9"] = _ema(df["close"], 9)
    df["ema_21"] = _ema(df["close"], 21)
    df["ema_50"] = _ema(df["close"], 50)

    macd_line, macd_signal = _macd(df["close"], 12, 26, 9)
    df["macd_line"] = macd_line
    df["macd_signal"] = macd_signal
    df["macd_hist"] = macd_line - macd_signal

    df["rsi_14"] = _rsi(df["close"], 14)
    df["atr_14"] = _atr(df, 14)

    bb_mid, bb_upper, bb_lower = _bollinger(df["close"], 20)
    df["bb_mid"] = bb_mid
    df["bb_upper"] = bb_upper
    df["bb_lower"] = bb_lower
    df["bb_width"] = bb_upper - bb_lower

    df["supertrend"] = _supertrend(df, 14, 3.0)

    df["candle_body"] = (df["close"] - df["open"]).abs()
    df["candle_range"] = df["high"] - df["low"]
    df["upper_wick"] = df["high"] - df[["close", "open"]].max(axis=1)
    df["lower_wick"] = df[["close", "open"]].min(axis=1) - df["low"]

    df["volume_change"] = df["volume"].pct_change().replace([np.inf, -np.inf], 0).fillna(0)
    df["volume_ema20"] = _ema(df["volume"], 20)
    df["volume_ratio"] = (
        df["volume"]
        .div(df["volume_ema20"].replace(0, np.nan))
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
    )

    df = df.drop(columns=["timestamp"])
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    return df


def add_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["future_close_1"] = df["close"].shift(-1)
    df["future_close_3"] = df["close"].shift(-3)
    df["future_close_5"] = df["close"].shift(-5)

    df["y_1"] = (df["future_close_1"] > df["close"]).astype(int)
    df["y_3"] = (df["future_close_3"] > df["close"]).astype(int)
    df["y_5"] = (df["future_close_5"] > df["close"]).astype(int)

    df = df.drop(columns=["future_close_1", "future_close_3", "future_close_5"])
    df = df.dropna()
    return df


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required data file missing: {path}")
    df = pd.read_csv(path)
    expected_cols = {"timestamp", "open", "high", "low", "close", "volume"}
    if not expected_cols.issubset(df.columns):
        raise ValueError(f"Input file {path} missing required columns {expected_cols}")

    numeric_cols = ["open", "high", "low", "close", "volume"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=numeric_cols)

    return df


def save_features() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for key, input_path in INPUT_FILES.items():
        try:
            raw_df = _load_csv(input_path)
            features_df = build_features(raw_df)
            labeled_df = add_labels(features_df)
        except Exception as exc:
            logging.error("Failed to process %s: %s", key, exc)
            continue

        output_path = OUTPUT_FILES[key]
        labeled_df.to_csv(output_path, index=False)
        logging.info("Saved processed dataset (%s rows) to %s", len(labeled_df), output_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    save_features()
