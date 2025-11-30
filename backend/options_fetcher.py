import requests
from nsepython import nsefetch

def get_option_chain(symbol="NIFTY"):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol.upper()}"
    try:
        data = nsefetch(url)
        return data
    except Exception as e:
        return {"error": str(e)}
