import requests
from textblob import TextBlob
import re

USER_AGENT = {"User-Agent": "Mozilla/5.0"}

# Words that indicate **non-financial** news (we want to skip)
BLOCK_KEYWORDS = [
    "movie", "film", "trailer", "box office", "song", "album",
    "bollywood", "hollywood", "web series", "episode", "tv show",
]

# Words that indicate **financial/market** context (we want to keep)
FINANCE_KEYWORDS = [
    "nifty", "sensex", "banknifty", "market", "markets", "shares",
    "stock", "stocks", "equity", "derivative", "f&o", "results",
    "q1", "q2", "q3", "q4", "quarter", "profit", "loss", "rbi",
    "rate", "inflation", "ipo", "listing", "fii", "dii",
    "nifty50", "nifty bank", "nifty next 50", "nifty midcap",
    "nifty smallcap", "nifty fin service", "nifty it", "nifty pharma", "nifty auto", "nifty metal",
    "nifty energy", "nifty psu bank",
    "grey market", "acquisition", "dividend", "shareholding",
]


def _looks_financial(headline: str) -> bool:
    h = headline.lower()
    if any(bad in h for bad in BLOCK_KEYWORDS):
        return False
    return any(fin in h for fin in FINANCE_KEYWORDS)


def fetch_google_news_raw(query: str):
    """Google News RSS (free, no key) - returns list of dicts with title and link."""
    url = (
        f"https://news.google.com/rss/search?"
        f"q={query}+when:1d&hl=en-IN&gl=IN&ceid=IN:en"
    )
    r = requests.get(url, headers=USER_AGENT, timeout=7)
    if r.status_code != 200:
        return []

    import xml.etree.ElementTree as ET
    root = ET.fromstring(r.text)
    headlines = []
    for item in root.iter("item"):
        title_elem = item.find("title")
        link_elem = item.find("link")
        if title_elem is not None and title_elem.text:
            headlines.append({
                "title": title_elem.text.strip(),
                "link": link_elem.text.strip() if link_elem is not None and link_elem.text else ""
            })
    return headlines


def fetch_filtered_news(query: str, max_items: int = 10):
    """Fetch and filter news, returning list of dicts with {title, link}."""
    raw = fetch_google_news_raw(query)
    # Filter based on title text
    filtered = [h for h in raw if _looks_financial(h.get("title", "") if isinstance(h, dict) else h)]
    if len(filtered) < 3:
        # fall back to raw (maybe low-volume day for that sector)
        filtered = raw
    return filtered[:max_items]


def analyze_sentiment(headlines: list):
    """Return sentiment (-1..+1) and simple summary string.
    
    Args:
        headlines: List of dicts with {title, link} or list of strings
    """
    if not headlines:
        return 0.0, "No major news found for today."

    scores = []
    for h in headlines:
        # Handle both dict format {"title": "..."} and plain string format
        text = h.get("title", "") if isinstance(h, dict) else h
        if text:
            blob = TextBlob(text)
            scores.append(blob.sentiment.polarity)  # -1..+1

    if not scores:
        return 0.0, "No major news found for today."
    
    avg = sum(scores) / len(scores)

    if avg > 0.2:
        summary = "News flow is broadly positive."
    elif avg < -0.2:
        summary = "News flow is broadly negative."
    else:
        summary = "News flow looks mixed / neutral."

    return round(avg, 3), summary
