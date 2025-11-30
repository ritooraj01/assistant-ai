"""Utilities to download 5 minute OHLCV data for Indian indices using yfinance."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

import pandas as pd
import yfinance as yf

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SYMBOLS: Dict[str, str] = {
    "nifty": "^NSEI",
    "banknifty": "^NSEBANK",
}
INTERVAL = "5m"
LOOKBACK_MONTHS = 9  # default ~ 9 months window
MAX_INTRADAY_DAYS = 59  # Yahoo Finance limit for <=30m intervals


def _download_symbol(symbol_name: str, ticker: str, start: datetime, end: datetime) -> pd.DataFrame:
    """Download OHLCV data for a given symbol between dates."""
    logging.info("Downloading %s (%s) data from %s to %s", symbol_name, ticker, start.date(), end.date())
    try:
        df = yf.download(ticker, start=start, end=end, interval=INTERVAL, progress=False, auto_adjust=False)
    except Exception as exc:  # pragma: no cover - defensive: network errors etc.
        logging.exception("Failed to download %s: %s", symbol_name, exc)
        raise

    if df.empty:
        raise ValueError(f"No data returned for {symbol_name} ({ticker}).")

    df.index = df.index.tz_localize(None)
    df = df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume",
        }
    )
    df = df[["open", "high", "low", "close", "volume"]]
    df = df.reset_index().rename(columns={"Datetime": "timestamp"})
    return df


def download_all(months: int = LOOKBACK_MONTHS) -> None:
    """Download data for all configured symbols and save as CSV."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    end = datetime.utcnow()
    requested_days = 30 * months
    lookback_days = min(requested_days, MAX_INTRADAY_DAYS)

    if requested_days > MAX_INTRADAY_DAYS:
        logging.warning(
            "Requested lookback of %s days exceeds Yahoo's %s-day intraday limit. Using last %s days instead.",
            requested_days,
            MAX_INTRADAY_DAYS,
            lookback_days,
        )

    start = end - timedelta(days=lookback_days)

    for key, ticker in SYMBOLS.items():
        try:
            df = _download_symbol(key, ticker, start=start, end=end)
        except Exception as exc:
            logging.error("Skipping %s due to error: %s", key, exc)
            continue

        output_path = DATA_DIR / f"{key}_5m.csv"
        df.to_csv(output_path, index=False)
        logging.info("Saved %s rows to %s", len(df), output_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    download_all()
