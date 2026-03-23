import re
import logging
import asyncio
from typing import List, Optional, Dict
from urllib.parse import urlparse, quote, urlunparse
from backend.utils.http_client import get_http_client
from backend.constants.agentic import SEARCH_LOCALE_PARAMS

logger = logging.getLogger("api-gateway")

async def check_asset_url(url: str, sem: asyncio.Semaphore) -> Optional[str]:
    """Parallel Anti-YouTube, HTTPS-Only & Integrity Check (Rule R110-V76)."""
    if not url.startswith("https://"): return None
    skip_domains = ["ytimg.com", "img.youtube.com", "vimeo.com", "fbsbx.com", "fbcdn.net", "instagram.com", "lookaside.instagram.com", "licdn.com"]
    if any(domain in url.lower() for domain in skip_domains): return None

    async with sem:
        try:
            p = urlparse(url)
            s_url = urlunparse(p._replace(path=quote(p.path), query=quote(p.query, safe='/=&?')))
            client = await get_http_client()
            headers = {"User-Agent": "Mozilla/5.0", "Accept": "image/*", "Referer": "https://www.google.com/"}
            resp = await client.head(s_url, timeout=4.0, follow_redirects=True, headers=headers)
            if resp.status_code == 200: return url
            if resp.status_code in [403, 404, 405]:
                async with client.stream("GET", s_url, timeout=4.0, follow_redirects=True, headers=headers) as stream:
                    if stream.status_code == 200: return url
        except: pass
    return None

async def fetch_google_page(query: str, start: int, pair: Dict[str, str]) -> List[str]:
    """Google Custom Search API Page Fetcher."""
    url = "https://www.googleapis.com/customsearch/v1"
    client = await get_http_client()
    try:
        params = {"key": pair["key"], "cx": pair["cx"], "q": query, "searchType": "image", "num": 10, "start": start, **SEARCH_LOCALE_PARAMS}
        response = await client.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        items = response.json().get('items', [])
        valid_links = [it['link'] for it in items if int(it.get('image', {}).get('height', 0)) >= 290 and int(it.get('image', {}).get('width', 0)) >= 290]
        return valid_links
    except Exception as e:
        logger.error(f"[AssetHunterUtils] Fetch failed: {e}")
        return []
