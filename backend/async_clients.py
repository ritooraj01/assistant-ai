import httpx
import asyncio

client = httpx.AsyncClient(timeout=10.0)

async def fetch_json(url, headers=None):
    try:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        return r.json()
    except:
        return None

async def fetch_text(url, headers=None):
    try:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        return r.text
    except:
        return None
