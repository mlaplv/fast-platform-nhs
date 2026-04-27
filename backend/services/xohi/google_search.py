import os
import json
import httpx
import logging
import random
import time
import asyncio
import redis.asyncio as redis
from typing import List, Dict, Any, Optional, cast, Tuple

from backend.services.xohi.creative_studio.operatives.shared_search_cache import get_or_fetch

logger = logging.getLogger("xohi-search")

class GoogleSearchService:
    """
    [ELITE V2.2] Intelligent Google Search Engine.
    - Singleton Pattern (R101)
    - Shared In-Process Cache (V90.0)
    - Redis-backed Key Rotation (Smart Selection)
    - Automatic 429/500 Cooldown Management
    """
    REDIS_PREFIX = "ai:search:v1:meta:"
    COOLDOWN_BASE = 300 # 5 minutes cooldown on failure
    
    _instance: Optional["GoogleSearchService"] = None

    def __new__(cls) -> "GoogleSearchService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
            
        self.api_keys: List[str] = []
        self.cxs: List[str] = []
        self._use_redis: bool = False
        self.redis: Optional[redis.Redis] = None
        
        try:
            self.api_keys = json.loads(os.getenv("GOOGLE_SEARCH_KEYS", "[]"))
            self.cxs = json.loads(os.getenv("GOOGLE_SEARCH_CXS", "[]"))
            
            # Initialize Redis connection
            self.redis = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)
            self._use_redis = True
        except Exception as e:
            logger.warning(f"[GoogleSearch] Redis unavailable or keys missing: {e}")
        
        self._initialized = True

    def _get_key_id(self, key: str) -> str:
        return f"{key[:8]}...{key[-4:]}"

    async def _select_best_key(self) -> Tuple[str, str, int]:
        """Intelligent key selection based on health and cooldown (SmartKeyRotator Style)."""
        if not self.api_keys:
            return "", "", -1
            
        now = time.time()
        candidates: List[int] = []
        weights: List[int] = []
        
        if not self._use_redis or not self.redis:
            idx = random.randint(0, len(self.api_keys) - 1)
            return self.api_keys[idx], self.cxs[idx] if idx < len(self.cxs) else self.cxs[0], idx

        # Fetch metadata for all keys in a pipeline
        async with self.redis.pipeline() as pipe:
            for api_key in self.api_keys:
                pipe.hgetall(f"{self.REDIS_PREFIX}{self._get_key_id(api_key)}")
            responses = await pipe.execute()

        for idx, meta_raw in enumerate(responses):
            meta = cast(Dict[str, str], meta_raw)
            fail_count = int(meta.get("fail_count", 0))
            last_used = float(meta.get("last_used", 0))
            health = int(meta.get("health_score", 100))
            
            # Circuit Breaker: Exponential backoff
            if fail_count > 0:
                cooldown = min(self.COOLDOWN_BASE * (2 ** (fail_count - 1)), 86400)
                if now - last_used < cooldown:
                    continue
            
            candidates.append(idx)
            weights.append(health)

        if not candidates:
            logger.warning("[GoogleSearch] All keys are in cooldown. Forcing first key.")
            return self.api_keys[0], self.cxs[0], 0

        chosen_idx = random.choices(candidates, weights=weights, k=1)[0]
        return self.api_keys[chosen_idx], self.cxs[chosen_idx] if chosen_idx < len(self.cxs) else self.cxs[0], chosen_idx

    async def _track_success(self, api_key: str) -> None:
        if self._use_redis and self.redis:
            kid = self._get_key_id(api_key)
            async with self.redis.pipeline() as pipe:
                pipe.hset(f"{self.REDIS_PREFIX}{kid}", "fail_count", 0)
                pipe.hset(f"{self.REDIS_PREFIX}{kid}", "health_score", 100)
                pipe.hset(f"{self.REDIS_PREFIX}{kid}", "last_used", time.time())
                await pipe.execute()

    async def _track_failure(self, api_key: str, status_code: int) -> None:
        if self._use_redis and self.redis:
            kid = self._get_key_id(api_key)
            meta = await self.redis.hgetall(f"{self.REDIS_PREFIX}{kid}")
            fail_count = int(meta.get("fail_count", 0)) + 1
            health = max(0, int(meta.get("health_score", 100)) - 20)
            
            async with self.redis.pipeline() as pipe:
                pipe.hset(f"{self.REDIS_PREFIX}{kid}", "fail_count", fail_count)
                pipe.hset(f"{self.REDIS_PREFIX}{kid}", "health_score", health)
                pipe.hset(f"{self.REDIS_PREFIX}{kid}", "last_used", time.time())
                await pipe.execute()

    async def search(self, query: str, num: int = 10) -> List[Dict[str, Any]]:
        """
        [ELITE V2.2] High-performance search with Shared Cache and Smart Rotation.
        """
        async def _perform_search() -> List[Dict[str, Any]]:
            api_key, cx, idx = await self._select_best_key()
            if not api_key: return []

            url = "https://www.googleapis.com/customsearch/v1"
            params = {"key": api_key, "cx": cx, "q": query, "num": num, "gl": "vn", "hl": "vi"}

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        await self._track_success(api_key)
                        data = resp.json()
                        items = data.get("items", [])
                        return [{
                            "title": item.get("title"),
                            "link": item.get("link"),
                            "snippet": item.get("snippet"),
                            "displayLink": item.get("displayLink"),
                            "pagemap": item.get("pagemap", {})
                        } for item in items]
                    
                    elif resp.status_code in [429, 403]:
                        logger.warning(f"Google Search Key {idx} limit reached ({resp.status_code}).")
                        await self._track_failure(api_key, resp.status_code)
                        return await _perform_search()
                    else:
                        logger.error(f"Google Search failed with status {resp.status_code} for key {idx}")
                        await self._track_failure(api_key, resp.status_code)
            except Exception as e:
                logger.error(f"Google Search error with key {idx}: {e}")
                await self._track_failure(api_key, 500)
            return []

        return await get_or_fetch(query, _perform_search, num=num)

google_search_service: GoogleSearchService = GoogleSearchService()
