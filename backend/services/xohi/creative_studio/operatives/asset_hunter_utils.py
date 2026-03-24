from __future__ import annotations
import re
import logging
import asyncio
from typing import Optional, Union, cast, Any
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

async def fetch_google_page(query: str, start: int, pair: dict[str, str], override_params: Optional[dict[str, Union[str, int, float, bool]]] = None) -> list[str]:
    """Google Custom Search API Page Fetcher."""
    url = "https://www.googleapis.com/customsearch/v1"
    client = await get_http_client()
    # Support for both override and default SEARCH_LOCALE_PARAMS
    base_p: dict[str, Union[str, int, float, bool]] = cast(dict[str, Union[str, int, float, bool]], SEARCH_LOCALE_PARAMS)
    if override_params is not None:
        base_p = override_params
        
    params: dict[str, Union[str, int, float, bool]] = {"key": pair["key"], "cx": pair["cx"], "q": query, "searchType": "image", "num": 10, "start": start, **base_p}
    response = await client.get(url, params=params, timeout=10.0)
    
    if response.status_code in [429, 403]:
        reason = "unknown"
        try:
            error_data = cast(dict[str, Union[str, dict]], response.json())
            err_list = cast(list[dict[str, str]], error_data.get("error", {}).get("errors", [{}]))
            reason = err_list[0].get("reason", "unknown")
            logger.warning(f"[AssetHunterUtils] SEARCH QUOTA EXCEEDED or Forbidden (Status {response.status_code}, Reason: {reason})")
        except:
            logger.warning(f"[AssetHunterUtils] SEARCH QUOTA EXCEEDED or Forbidden (Status {response.status_code})")
        
    response.raise_for_status()
    # Explicitly cast items for strict typing compliance
    items = cast(list[dict[str, Union[str, dict]]], response.json().get('items', []))
    valid_links: list[str] = []
    for it in items:
        img_data = cast(dict[str, Union[str, int]], it.get('image', {}))
        if int(img_data.get('height', 0)) >= 200 and int(img_data.get('width', 0)) >= 200:
            valid_links.append(cast(str, it['link']))
    return valid_links
