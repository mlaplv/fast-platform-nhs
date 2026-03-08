import httpx
import asyncio
from typing import List, Optional
from datetime import datetime, timedelta

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

        async with httpx.AsyncClient() as client:
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
                    urls = [item['link'] for item in data.get('items', [])]
                    return urls

                except Exception as e:
                    logger.error(f"[AssetHunter] Error with key {self.current_index}: {e}")
                    self.failure_count += 1
                    self._rotate_key()
                    attempts += 1
                    if attempts >= max_attempts:
                        # Trip circuit breaker if all keys fail
                        self.cooldown_until = datetime.utcnow() + timedelta(minutes=15)
                        raise e
            
            raise Exception("All Search API keys exhausted or failed.")
