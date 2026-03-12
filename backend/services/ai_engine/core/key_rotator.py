import os
import json
import logging
import time
import redis.asyncio as redis
from typing import Optional

logger = logging.getLogger("api-gateway")

class SmartKeyRotator:
    """
    R101/R106: Intelligent Key Management for LLM Tiers.
    V63.0: Redis-backed state for sticky success and circuit breaking.
    """
    SUCCESS_INDEX_KEY = "ai:key_rotator:last_success_index"
    UNHEALTHY_PREFIX = "ai:key_rotator:unhealthy:"
    COOLDOWN_SECONDS = 300  # 5 minutes

    def __init__(self):
        raw_keys = os.getenv("GEMINI_API_KEY", "")
        self.keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        self.index = 0
        self._use_redis = False
        self.client = None

        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self._use_redis = True
            logger.info(f"[KeyRotator] Connected to Redis for shared state.")
        except Exception as e:
            logger.warning(f"[KeyRotator] Redis unavailable, using local memory: {e}")

        if not self.keys:
            logger.warning("[KeyRotator] No GEMINI_API_KEY found in environment!")

    async def get_key(self) -> str:
        """
        Returns the best key to use. 
        Prioritizes the last successful key, skipping unhealthy ones.
        """
        if not self.keys:
            return ""

        # Try to start from the last successful index known globally
        start_index = self.index
        if self._use_redis:
            try:
                global_idx = await self.client.get(self.SUCCESS_INDEX_KEY)
                if global_idx is not None:
                    start_index = int(global_idx) % len(self.keys)
            except Exception: pass

        # Iterate through keys starting from the best one
        for i in range(len(self.keys)):
            current_idx = (start_index + i) % len(self.keys)
            key = self.keys[current_idx]
            
            # Check if key is in cooldown
            if self._use_redis:
                try:
                    is_unhealthy = await self.client.get(f"{self.UNHEALTHY_PREFIX}{current_idx}")
                    if is_unhealthy:
                        continue 
                except Exception: pass

            # Update our local index for the next call if this works
            self.index = current_idx
            return key

        # If all keys are unhealthy, force return the first one as a last resort
        return self.keys[0]

    async def set_success(self, key: str):
        """Marks a key as successful, updating the global 'sticky' index."""
        try:
            idx = self.keys.index(key)
            self.index = idx
            if self._use_redis:
                await self.client.set(self.SUCCESS_INDEX_KEY, idx)
                # Clear unhealthy status if it was set
                await self.client.delete(f"{self.UNHEALTHY_PREFIX}{idx}")
        except Exception: pass

    async def mark_unhealthy(self, key: str):
        """Triggers circuit breaker cooldown for a failing key."""
        try:
            idx = self.keys.index(key)
            if self._use_redis:
                # Set a cooldown key in Redis
                await self.client.set(f"{self.UNHEALTHY_PREFIX}{idx}", "1", ex=self.COOLDOWN_SECONDS)
                logger.warning(f"[KeyRotator] Key index {idx} marked UNHEALTHY (Cooldown: {self.COOLDOWN_SECONDS}s)")
        except Exception: pass

    def get_count(self) -> int:
        return len(self.keys)

    def get_all_keys(self) -> list[str]:
        """Legacy support for multi-key iteration (V60.0)"""
        return self.keys

    def get_next_key(self) -> str:
        """Simple round-robin without unhealthy check (V56.0 compat)"""
        if not self.keys: return ""
        key = self.keys[self.index]
        self.index = (self.index + 1) % len(self.keys)
        return key
