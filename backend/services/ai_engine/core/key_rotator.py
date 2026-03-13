import os
import logging
import time
import random
import hashlib
import asyncio
import redis.asyncio as redis
from typing import Optional, List, Dict

logger = logging.getLogger("api-gateway")

class SmartKeyRotator:
    """
    R101/R106: Intelligent Key Management for LLM Tiers.
    V70.0: Weighted Random Selection, Exponential Backoff, and TPM Tracking.
    """
    SUCCESS_INDEX_KEY = "ai:key_rotator:last_success_index"
    ROUND_ROBIN_KEY = "ai:key_rotator:round_robin_counter"
    STICKY_PREFIX = "ai:key_rotator:sticky:"
    
    # New V70.0 Redis Keys
    METADATA_PREFIX = "ai:key:v70:meta:"    # Hash: fail_count, last_used, health_score
    TPM_PREFIX = "ai:key:v70:tpm:"         # ZSET for sliding window token tracking
    BLACKLIST_PREFIX = "ai:key:v70:black:"  # Set/Key for dead keys

    # Cooldown settings
    BASE_COOLDOWN = 60
    MAX_COOLDOWN = 86400  # 24h
    
    _instance: Optional["SmartKeyRotator"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        raw_keys = os.getenv("GEMINI_API_KEY", "")
        self.keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        self.index = 0
        self._use_redis = False
        self.client: Optional[redis.Redis] = None

        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self._use_redis = True
            logger.info(f"[KeyRotator] V70.0 Connected to Redis. Keys loaded: {len(self.keys)}")
        except Exception as e:
            logger.warning(f"[KeyRotator] Redis unavailable, using local memory (DEGRADED): {e}")

        if not self.keys:
            logger.warning("[KeyRotator] No GEMINI_API_KEY found in environment!")

    def _get_key_id(self, key: str) -> str:
        """Standardize key identification via Hashing to survive pool reordering."""
        return hashlib.md5(key.encode()).hexdigest()[:16]

    async def get_key(self, session_id: Optional[str] = None) -> str:
        """
        V70.1: Weighted Random Selection with Key-Hash based tracking.
        """
        if not self.keys: return ""
        if not self._use_redis: return self.get_next_key()

        num_keys = len(self.keys)
        candidate_indices = []
        weights = []
        now = time.time()

        # R1.2 Gather health data for all candidate keys
        for idx, key in enumerate(self.keys):
            kid = self._get_key_id(key)
            
            # 1. Check Blacklist
            if await self.client.exists(f"{self.BLACKLIST_PREFIX}{kid}"):
                continue

            # 2. Check Cooldown/Health
            meta = await self.client.hgetall(f"{self.METADATA_PREFIX}{kid}")
            fail_count = int(meta.get("fail_count", 0))
            last_used = float(meta.get("last_used", 0))
            health_score = int(meta.get("health_score", 100))

            if fail_count > 0:
                cooldown = min(self.BASE_COOLDOWN * (2 ** (fail_count - 1)), self.MAX_COOLDOWN)
                if now - last_used < cooldown:
                    continue 

            # 3. Calculate Weight
            idle_time = now - last_used
            weight = (idle_time + 1) * (health_score / 100.0)
            
            candidate_indices.append(idx)
            weights.append(weight)

        if not candidate_indices:
            logger.warning("[KeyRotator] No healthy keys available. Using raw rotation.")
            return self.get_next_key()

        # 4. Weighted Random Choice
        chosen_idx = random.choices(candidate_indices, weights=weights, k=1)[0]
        chosen_key = self.keys[chosen_idx]
        chosen_kid = self._get_key_id(chosen_key)
        
        # 5. Micro-Jitter (Standard Anti-Scraping)
        await asyncio.sleep(random.uniform(0.1, 0.25))

        # 6. Update last_used by Hash ID
        await self.client.hset(f"{self.METADATA_PREFIX}{chosen_kid}", "last_used", now)
        self.index = chosen_idx
        
        return chosen_key

    async def set_success(self, key: str, session_id: Optional[str] = None):
        """Marks a key as successful, resets fail_count using Hash ID."""
        if not self._use_redis: return
        kid = self._get_key_id(key)
        try:
            await self.client.hset(f"{self.METADATA_PREFIX}{kid}", mapping={
                "fail_count": 0,
                "health_score": 100
            })
        except Exception:
            pass

    async def mark_unhealthy(self, key: str, reason: str = "rate_limit", session_id: Optional[str] = None):
        """Circuit Breaker Logic using Hash ID."""
        if not self._use_redis: return
        kid = self._get_key_id(key)
        reason_lower = reason.lower()
        
        # 1. Critical Failures -> Blacklist
        if any(p in reason_lower for p in ["auth", "invalid", "disabled", "expired", "401", "403"]):
            await self.client.set(f"{self.BLACKLIST_PREFIX}{kid}", reason, ex=self.MAX_COOLDOWN * 30)
            logger.error(f"[KeyRotator] Key {key[:10]}... BLACKLISTED. Reason: {reason}")
            return

        # 2. Transient Failures -> Backoff
        fail_count = await self.client.hincrby(f"{self.METADATA_PREFIX}{kid}", "fail_count", 1)
        await self.client.hset(f"{self.METADATA_PREFIX}{kid}", "health_score", max(0, 100 - (fail_count * 20)))
        logger.warning(f"[KeyRotator] Key {key[:10]}... fail_count={fail_count}. Reason: {reason}")

    async def track_tokens(self, key: str, tokens: int):
        """Track tokens for TPM management using Hash ID."""
        if not self._use_redis or tokens <= 0: return
        kid = self._get_key_id(key)
        now = time.time()
        try:
            async with self.client.pipeline() as pipe:
                pipe.zadd(f"{self.TPM_PREFIX}{kid}", {str(now): now})
                pipe.zremrangebyscore(f"{self.TPM_PREFIX}{kid}", 0, now - 60)
                await pipe.execute()
        except Exception:
            pass

    def set_keys(self, keys: List[str]):
        """Standardized Pool Update."""
        self.keys = keys
        logger.info(f"[KeyRotator] Cognitive pool updated with {len(keys)} keys.")

    def get_count(self) -> int:
        return len(self.keys)

    def get_next_key(self) -> str:
        if not self.keys: return ""
        key = self.keys[self.index]
        self.index = (self.index + 1) % len(self.keys)
        return key

# Module-level singleton
key_rotator = SmartKeyRotator()
