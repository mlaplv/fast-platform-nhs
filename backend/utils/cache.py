import time
from typing import Any, Optional, Dict
from collections import OrderedDict
import logging

logger = logging.getLogger("xohi.cache")

class ViralCache:
    """
    V61.0: High-performance LRU Cache for Viral traffic.
    Avoids DB hits for frequent state checks on 2GB RAM VPS.
    """
    def __init__(self, maxsize: int = 500, ttl: int = 300):
        self.cache: OrderedDict = OrderedDict()
        self.maxsize = maxsize
        self.ttl = ttl # Default 5 minutes
        self._stats = {"hits": 0, "misses": 0}

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            self._stats["misses"] += 1
            return None
        
        val, expiry = self.cache[key]
        if time.time() > expiry:
            del self.cache[key]
            self._stats["misses"] += 1
            return None
        
        # Move to end (MRU)
        self.cache.move_to_end(key)
        self._stats["hits"] += 1
        return val

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        if len(self.cache) >= self.maxsize:
            self.cache.popitem(last=False) # Remove LRU
        
        expiry = time.time() + (ttl or self.ttl)
        self.cache[key] = (value, expiry)
        self.cache.move_to_end(key)

    def stats(self) -> Dict[str, int]:
        return self._stats

# Global instances for different domains
from backend.constants.agentic import CONTENT_CACHE_MAXSIZE, CONTENT_CACHE_TTL
viral_content_cache = ViralCache(maxsize=CONTENT_CACHE_MAXSIZE, ttl=CONTENT_CACHE_TTL) # Content states cache (1 min)
viral_api_cache = ViralCache(maxsize=1000, ttl=300)   # Generic API responses (5 min)
