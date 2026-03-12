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
    V64.0: Sticky session keys and dynamic RPM/RPD cooldown logic.
    """
    SUCCESS_INDEX_KEY = "ai:key_rotator:last_success_index"
    STICKY_PREFIX = "ai:key_rotator:sticky:"
    UNHEALTHY_PREFIX = "ai:key_rotator:unhealthy:"
    
    # Cooldown durations
    COOLDOWN_MINUTE = 60      # Rate Limit (RPM)
    COOLDOWN_DAILY = 86400    # Quota Exhausted (RPD) - 24 hours

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

    async def get_key(self, session_id: Optional[str] = None) -> str:
        """
        Returns the best key to use. 
        Prioritizes 'Sticky' key for the session, or global successful index.
        """
        if not self.keys: return ""
        
        num_keys = len(self.keys)
        start_index = self.index

        # 1. Attempt to get Sticky Key for this session
        if session_id and self._use_redis:
            try:
                sticky_idx = await self.client.get(f"{self.STICKY_PREFIX}{session_id}")
                if sticky_idx is not None:
                    start_index = int(sticky_idx) % num_keys
                else:
                    # No sticky index yet? Use hash-based stable routing
                    import hashlib
                    hash_val = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
                    start_index = hash_val % num_keys
            except Exception: pass
        elif self._use_redis:
            # Global Orbital Rotation for anonymous sessions
            try:
                global_idx = await self.client.incr(self.SUCCESS_INDEX_KEY)
                start_index = global_idx % num_keys
            except Exception: pass

        # 2. Iterate through keys starting from the best candidate
        for i in range(num_keys):
            current_idx = (start_index + i) % num_keys
            key = self.keys[current_idx]
            
            if self._use_redis:
                try:
                    is_unhealthy = await self.client.get(f"{self.UNHEALTHY_PREFIX}{current_idx}")
                    if is_unhealthy:
                        continue 
                except Exception: pass

            # Foundation: If we found a healthy key, mark it as current
            self.index = current_idx
            
            # If session-based, update sticky mapping in Redis (Short TTL for session)
            if session_id and self._use_redis:
                try:
                    await self.client.set(f"{self.STICKY_PREFIX}{session_id}", current_idx, ex=3600)  # 1h sticky
                except Exception: pass
                
            return key

        # Fallback: All unhealthy? Force the hash-based one if possible, or index 0
        return self.keys[start_index % num_keys]

    async def set_success(self, key: str, session_id: Optional[str] = None):
        """Marks a key as successful."""
        try:
            idx = self.keys.index(key)
            self.index = idx
            if self._use_redis:
                await self.client.set(self.SUCCESS_INDEX_KEY, idx)
                await self.client.delete(f"{self.UNHEALTHY_PREFIX}{idx}")
                if session_id:
                    await self.client.set(f"{self.STICKY_PREFIX}{session_id}", idx, ex=3600)
        except Exception: pass

    async def mark_unhealthy(self, key: str, reason: str = "rate_limit", session_id: Optional[str] = None):
        """Triggers circuit breaker cooldown: 60s for RPM, 24h for RPD."""
        try:
            idx = self.keys.index(key)
            cooldown = self.COOLDOWN_DAILY if "daily" in reason.lower() or "quota" in reason.lower() else self.COOLDOWN_MINUTE
            
            if self._use_redis:
                await self.client.set(f"{self.UNHEALTHY_PREFIX}{idx}", "1", ex=cooldown)
                logger.warning(f"[KeyRotator] Key index {idx} UNHEALTHY. Reason: {reason}. Cooldown: {cooldown}s")
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
