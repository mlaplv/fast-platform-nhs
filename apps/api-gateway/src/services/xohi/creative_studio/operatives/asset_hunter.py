import httpx
import asyncio
from typing import List, Optional
from datetime import datetime, timedelta

class AssetHunter:
    """
    Step 2: Hunt for images using Google Custom Search API.
    Hardened with Key Rotator and Circuit Breaker.
    """
    def __init__(self, api_keys: List[str], search_engine_id: str):
        self.api_keys = api_keys
        self.search_engine_id = search_engine_id
        self.current_key_index = 0
        self.failure_count = 0
        self.cooldown_until: Optional[datetime] = None

    def _get_next_key(self) -> str:
        """Key Rotator logic."""
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key

    async def fetch_images(self, query: str, num_results: int = 10) -> List[str]:
        """
        Fetches image URLs from Google.
        Hardened with Rule 7: API CIRCUIT BREAKER.
        """
        if self.cooldown_until and datetime.utcnow() < self.cooldown_until:
            raise Exception(f"Circuit Breaker ACTIVE. Cooldown until {self.cooldown_until}")

        url = "https://www.googleapis.com/customsearch/v1"
        
        async with httpx.AsyncClient() as client:
            try:
                params = {
                    "key": self._get_next_key(),
                    "cx": self.search_engine_id,
                    "q": query,
                    "searchType": "image",
                    "num": num_results,
                    "imgSize": "large" # Rule: Only high res
                }
                
                response = await client.get(url, params=params)
                
                if response.status_code == 429: # Rate Limit
                    self.failure_count += 1
                    if self.failure_count >= 5:
                        self.cooldown_until = datetime.utcnow() + timedelta(minutes=15)
                        raise Exception("Circuit Breaker Triggered: Too many 429 errors.")
                    
                    # Try next key immediately (Recursive call or loop)
                    return await self.fetch_images(query, num_results)

                response.raise_for_status()
                data = response.json()
                
                # Reset failure count on success
                self.failure_count = 0
                
                # Rule 2 & 5: Heuristic Filter & Zero Storage
                urls = [item['link'] for item in data.get('items', [])]
                return urls

            except Exception as e:
                self.failure_count += 1
                if self.failure_count >= 5:
                    self.cooldown_until = datetime.utcnow() + timedelta(minutes=15)
                raise e

    async def batch_fetch(self, queries: List[str]) -> List[str]:
        """Rule 1: ASYNC-FIRST: Fetch multiple queries in parallel."""
        tasks = [self.fetch_images(q) for q in queries]
        results = await asyncio.gather(*tasks)
        # Flatten list
        return [url for sublist in results for url in sublist]
