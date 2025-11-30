import yfinance as yf
from async_clients import fetch_json
import asyncio

async def get_global_async():
    loop = asyncio.get_event_loop()

    # run all yfinance calls in parallel threads
    tasks = [
        loop.run_in_executor(None, lambda: yf.Ticker("^NSEI").history(period="2d").Close),
        loop.run_in_executor(None, lambda: yf.Ticker("^NDX").history(period="2d").Close),
        loop.run_in_executor(None, lambda: yf.Ticker("CL=F").history(period="2d").Close),
        loop.run_in_executor(None, lambda: yf.Ticker("USDINR=X").history(period="2d").Close),
    ]

    nifty, nasdaq, crude, usdinr = await asyncio.gather(*tasks)

    def pct_change(series):
        if series is None or len(series) < 2:
            return None, None
        prev, last = float(series.iloc[-2]), float(series.iloc[-1])
        return last, (last - prev) / prev * 100

    return {
        "nifty": pct_change(nifty),
        "nasdaq": pct_change(nasdaq),
        "crude": pct_change(crude),
        "usdinr": pct_change(usdinr),
    }
