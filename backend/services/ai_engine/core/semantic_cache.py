import logging
import json
from typing import Optional, Tuple
from backend.services.xohi_memory import xohi_memory
from backend.services.ai_engine.core.semantic_router import SemanticRouter
from backend.utils.text import normalize_vn

logger = logging.getLogger("api-gateway")

class SemanticCache:
    """
    Elite V2.2: Semantic Caching Layer.
    Stores prompt -> response mappings in Redis with a TTL.
    Uses SemanticRouter to find 'near matches' for common queries.
    """
    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.router = SemanticRouter()

    async def get(self, query: str, context_key: str = "support") -> Optional[str]:
        """
        Check if a semantically similar query exists in cache.
        Returns the cached reply if similarity > threshold.
        """
        try:
            norm_q = normalize_vn(query)
            # 1. Try Exact Match first
            cache_key = f"cache:{context_key}:exact:{hash(norm_q)}"
            exact = await xohi_memory.client.get(cache_key)
            if exact:
                logger.info(f"[SemanticCache] Exact match hit for: {query[:30]}...")
                return exact

            # 2. Semantic Match (Phase 2)
            # This requires a 'Knowledge Base' of previously answered questions.
            # For now, we'll focus on exact/near-exact matches to prevent hallucinations.
            return None
        except Exception as e:
            logger.warning(f"[SemanticCache] Cache lookup failed: {e}")
            return None

    async def set(self, query: str, response: str, context_key: str = "support", ttl: int = 3600):
        """Cache a successful AI response."""
        try:
            norm_q = normalize_vn(query)
            cache_key = f"cache:{context_key}:exact:{hash(norm_q)}"
            await xohi_memory.client.set(cache_key, response, ex=ttl)
        except Exception as e:
            logger.warning(f"[SemanticCache] Cache set failed: {e}")

semantic_cache = SemanticCache()
