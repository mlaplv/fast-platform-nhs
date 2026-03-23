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
            resp = await client.head(s_url, timeout=3.0, follow_redirects=True, headers=headers)
            
            def is_valid_img(headers):
                ctype = headers.get("Content-Type", "").lower()
                # CNS V82.50: Strict Image + Size check. clen=0 fallback to prevent int() error.
                clen = int(headers.get("Content-Length") or 0)
                # Skip small placeholders/trackers (< 1KB) and non-images or HTML-clothed redirects
                return "image" in ctype and clen > 1024 and "text/html" not in ctype

            if resp.status_code == 200 and is_valid_img(resp.headers):
                return url
                
            if resp.status_code in [200, 403, 404, 405]:
                # Fallback to GET stream if HEAD is blocked or inconclusive
                async with client.stream("GET", s_url, timeout=4.0, follow_redirects=True, headers=headers) as stream:
                    if stream.status_code == 200 and is_valid_img(stream.headers):
                        return url
        except: 
            pass
    return None

async def fetch_google_page(query: str, start: int, pair: Dict[str, str], override_params: Optional[Dict] = None) -> List[str]:
    """Google Custom Search API Page Fetcher."""
    url = "https://www.googleapis.com/customsearch/v1"
    client = await get_http_client()
    base_params = override_params if override_params is not None else SEARCH_LOCALE_PARAMS
    params = {"key": pair["key"], "cx": pair["cx"], "q": query, "searchType": "image", "num": 10, "start": start, **base_params}
    response = await client.get(url, params=params, timeout=10.0)
    
    if response.status_code in [429, 403]:
        logger.warning(f"[AssetHunterUtils] SEARCH QUOTA EXCEEDED or Forbidden (Status {response.status_code})")
        
    response.raise_for_status()
    items = response.json().get('items', [])
    valid_links = [it['link'] for it in items if int(it.get('image', {}).get('height', 0)) >= 200 and int(it.get('image', {}).get('width', 0)) >= 200]
    return valid_links
