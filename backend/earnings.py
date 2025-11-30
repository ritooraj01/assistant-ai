import requests
from datetime import datetime, timedelta

USER_AGENT = {"User-Agent": "Mozilla/5.0"}

def fetch_upcoming_results():
    """
    Fetch upcoming earnings from Moneycontrol's free economic calendar (scrape).
    Returns:
      [
        { "company": "TCS", "date": "2024-10-12", "sector": "IT" },
        ...
      ]
    """
    url = "https://www.moneycontrol.com/stocks/marketinfo/upcoming_results.php"
    r = requests.get(url, headers=USER_AGENT, timeout=8)

    if r.status_code != 200:
        return []

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r.text, "html.parser")

    rows = soup.select("table tbody tr")
    out = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 3:
            continue

        company = cols[0].text.strip()
        date_str = cols[2].text.strip()

        try:
            dt = datetime.strptime(date_str, "%d %b %Y")
        except:
            continue

        out.append({
            "company": company,
            "date": dt.strftime("%Y-%m-%d")
        })

    return out


def sector_event_risk(sector_stocks, earnings_list):
    """
    If companies in the user’s sector have results within 5 days,
    return higher risk.
    """
    today = datetime.today()
    risk = 0.0
    next_date = None
    reasons = []

    for stock in sector_stocks:
        for e in earnings_list:
            if stock.upper() in e["company"].upper():
                dt = datetime.strptime(e["date"], "%Y-%m-%d")
                days = (dt - today).days

                if 0 <= days <= 5:
                    risk += 0.5
                    next_date = e["date"]
                    reasons.append(f"{stock} results on {e['date']} (volatility risk).")

    # clamp risk
    if risk > 1:
        risk = 1.0

    return risk, next_date, reasons
