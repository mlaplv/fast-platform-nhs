import httpx
import asyncio
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from backend.utils.http_client import get_http_client
from backend.constants.agentic import MAX_SEARCH_RETRY_PER_STEP, SEARCH_CIRCUIT_BREAKER_COOLDOWN_MINUTES

logger = logging.getLogger("api-gateway")

class AssetHunter:
    """
    Step 2: Hunt for images using Google Custom Search API.
    Hardened with Key Rotator and Circuit Breaker (Rule 7).
    """
    def __init__(self, key_pairs: List[Dict[str, str]]):
        """
        key_pairs: List of {"key": "...", "cx": "..."}
        """
        self.key_pairs = key_pairs
        self.current_index = 0
        self.failure_count = 0
        self.cooldown_until: Optional[datetime] = None

    def _get_current_pair(self) -> Dict[str, str]:
        if not self.key_pairs:
            raise Exception("No Google Search API Keys configured.")
        return self.key_pairs[self.current_index]

    def _rotate_key(self):
        self.current_index = (self.current_index + 1) % len(self.key_pairs)
        logger.info(f"[AssetHunter] Rotating to key index {self.current_index}")

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs):
        """Standard entry point for DI Registry (V61.0)."""
        campaign = await repo.get(campaign_id)
        if not campaign: return
        
        query = campaign.topic_data.get("primary_keyword", campaign.source_input)
        urls = await self.fetch_images(query)
        campaign.assets_data = urls
        return urls

    async def fetch_images(self, query: str, num_results: int = 10) -> List[str]:
        """
        Fetches image URLs from Google.
        Hardened with Circuit Breaker and Key Rotation on 429.
        """
        if self.cooldown_until and datetime.utcnow() < self.cooldown_until:
            raise Exception(f"Search Circuit Breaker ACTIVE. Cooldown until {self.cooldown_until}")

        url = "https://www.googleapis.com/customsearch/v1"
        
        # Max attempts = number of keys we have
        attempts = 0
        max_attempts = len(self.key_pairs)

        # R106: Reuse shared HTTP client to save TCP/SSL overhead
        client = await get_http_client()
        while attempts < max_attempts:
                pair = self._get_current_pair()
                try:
                    params = {
                        "key": pair["key"],
                        "cx": pair["cx"],
                        "q": query,
                        "searchType": "image",
                        "num": num_results,
                        "imgSize": "large" 
                    }
                    
                    logger.info(f"[AssetHunter] Searching index {self.current_index} for: {query}")
                    response = await client.get(url, params=params, timeout=10.0)
                    
                    if response.status_code == 429:
                        logger.warning(f"[AssetHunter] Key index {self.current_index} rate limited (429).")
                        self._rotate_key()
                        attempts += 1
                        continue

                    response.raise_for_status()
                    data = response.json()
                    
                    # Success: Reset failure count and return
                    self.failure_count = 0
                    items = data.get('items', [])
                    if not items:
                        search_info = data.get('searchInformation', {})
                        logger.warning(f"[AssetHunter] Key {self.current_index} returned 0 results. Total results from Google: {search_info.get('totalResults')}")
                    
                    urls = [item['link'] for item in items]
                    return urls

                except Exception as e:
                    logger.error(f"[AssetHunter] Error with key {self.current_index}: {e}")
                    self.failure_count += 1
                    self._rotate_key()
                    attempts += 1
                    if attempts >= max_attempts:
                        # R103: Graceful Degradation — Return empty list instead of crashing
                        logger.error("[AssetHunter] All Search API keys exhausted or failed.")
                        from backend.constants.agentic import SEARCH_CIRCUIT_BREAKER_COOLDOWN_MINUTES
                        from datetime import timezone
                        self.cooldown_until = datetime.now(timezone.utc) + timedelta(minutes=SEARCH_CIRCUIT_BREAKER_COOLDOWN_MINUTES)
                    continue
            
        return []
