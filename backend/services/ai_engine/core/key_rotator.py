import os
import logging
import time
import random
import asyncio
import redis.asyncio as redis
from typing import Optional, List, Dict, cast

# Mixins (CNS V5.5 Modularization)
from backend.services.ai_engine.core.key_metrics import KeyMetricsMixin
from backend.services.ai_engine.core.key_loader import KeyLoaderMixin

logger = logging.getLogger("api-gateway")

class SmartKeyRotator(KeyMetricsMixin, KeyLoaderMixin):
    """
    R101/R106: Intelligent Key Management for LLM Tiers.
    Modularized to comply with Martial Law (<300 lines).
    """
    METADATA_PREFIX = "ai:key:v70:meta:"
    TPM_PREFIX = "ai:key:v70:tpm:"
    BLACKLIST_PREFIX = "ai:key:v70:black:"
    MODEL_DAILY_PREFIX = "ai:key:v70:daily:"
    POISON_PREFIX = "ai:model:v75:poison:"
    MODEL_METADATA_PREFIX = "ai:model:v75:meta:"
    MODEL_CAPABILITY_PREFIX = "ai:model:v75:cap:"
    DISCOVERED_MODELS_KEY = "ai:bridge:discovered:v75"
    BASE_COOLDOWN, MAX_COOLDOWN = 60, 86400
    MAX_RPM = int(os.getenv("GEMINI_MAX_RPM", 10))
    MAX_TPM = int(os.getenv("GEMINI_MAX_TPM", 1000000))

    _instance: Optional["SmartKeyRotator"] = None
    def __new__(cls):
        if cls._instance is None: cls._instance = super().__new__(cls); cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized: return
        self.keys: List[str] = []
        self.index: int = 0
        self._use_redis: bool = False
        self.client: Optional[redis.Redis] = None
        self._initialized: bool = True
        try:
            self.client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)
            self._use_redis = True
        except Exception as e: logger.warning(f"[KeyRotator] Redis unavailable: {e}")

    async def get_key(self, model_name: str = "gemini-2.0-flash", session_id: Optional[str] = None) -> str:
        """Model-Aware Key Selection with Weighted Random Choice (Pipeline Optimized)."""
        if not self.keys: return ""
        if not self._use_redis or not self.client: return self.get_next_key()
        
        now = time.time()
        candidates: List[int] = []
        weights: List[int] = []
        
        # Elite V2.2: Pipeline Optimization - Reduce Round-Trip-Time (RTT)
        async with self.client.pipeline() as pipe:
            for key in self.keys:
                kid = self._get_key_id(key)
                pipe.exists(f"{self.BLACKLIST_PREFIX}{kid}")
                pipe.exists(f"{self.MODEL_DAILY_PREFIX}{kid}:{model_name.replace('/', '_').replace('-', '_')[:40]}")
                pipe.hgetall(f"{self.METADATA_PREFIX}{kid}")
                # Preliminary TPM cleanup & fetch
                pipe.zremrangebyscore(f"{self.TPM_PREFIX}{kid}", 0, now - 60)
                pipe.zrangebyscore(f"{self.TPM_PREFIX}{kid}", now - 60, now)
            
            responses = await pipe.execute()

        # Step size per key in the responses list: 5 (exists, model_daily, hgetall, zremrange, zrange)
        CHUNK_SIZE = 5
        for idx in range(len(self.keys)):
            r_idx = idx * CHUNK_SIZE
            is_blacklisted = bool(responses[r_idx])
            is_daily_exhausted = bool(responses[r_idx+1])
            meta: Dict[str, str] = cast(Dict[str, str], responses[r_idx+2])
            tpm_ms: List[str] = cast(List[str], responses[r_idx+4])
            
            if is_blacklisted or is_daily_exhausted: continue
            
            fail = int(meta.get("fail_count", 0))
            last = float(meta.get("last_used", 0))
            health = int(meta.get("health_score", 100))
            
            # Circuit Breaker: Exponential backoff check
            if fail > 0 and now - last < min(self.BASE_COOLDOWN * (2**(fail-1)), self.MAX_COOLDOWN): continue
            
            # RPM/TPM Check (Rate-Limit Guard)
            current_tpm = sum(int(m.split(":")[1]) for m in tpm_ms if ":" in m)
            if len(tpm_ms) >= self.MAX_RPM or current_tpm >= self.MAX_TPM: continue
            
            candidates.append(idx)
            weights.append(health)

        if not candidates:
            # Re-check for precise error reporting (Fail-safe)
            total_bl = 0
            for k in self.keys:
                if await self.client.exists(f"{self.BLACKLIST_PREFIX}{self._get_key_id(k)}"): total_bl += 1
            if total_bl == len(self.keys): raise Exception("AUTH_ERROR: All keys blacklisted.")
            raise Exception(f"QUOTA/COOLDOWN: No keys for '{model_name}'.")

        chosen_idx = random.choices(candidates, weights=weights, k=1)[0]
        chosen_key = self.keys[chosen_idx]
        kid: str = self._get_key_id(chosen_key)
        
        # Elite V2.2: Concurrent Reservation (R115)
        # Add a placeholder to TPM set immediately to reserve a slot for this RPM.
        # This prevents other concurrent tasks from picking the same key before track_tokens() is called.
        placeholder: str = f"{now}:0:RESERVED:{random.randint(10000, 99999)}"
        await self.client.zadd(f"{self.TPM_PREFIX}{kid}", {placeholder: now})
        
        await self.client.hset(f"{self.METADATA_PREFIX}{kid}", "last_used", now)
        self.index = chosen_idx
        return chosen_key

key_rotator = SmartKeyRotator()
