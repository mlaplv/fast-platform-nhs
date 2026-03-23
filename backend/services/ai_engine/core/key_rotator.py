import os
import logging
import time
import random
import asyncio
import redis.asyncio as redis
from typing import Optional, List, Dict

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
    DISCOVERED_MODELS_KEY = "ai:bridge:discovered:v75"
    BASE_COOLDOWN, MAX_COOLDOWN = 60, 86400
    MAX_RPM = int(os.getenv("GEMINI_MAX_RPM", 2))
    MAX_TPM = int(os.getenv("GEMINI_MAX_TPM", 800000))

    _instance: Optional["SmartKeyRotator"] = None
    def __new__(cls):
        if cls._instance is None: cls._instance = super().__new__(cls); cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        self._initialized, self.keys, self.index, self._use_redis, self.client = True, [], 0, False, None
        try:
            self.client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)
            self._use_redis = True
        except Exception as e: logger.warning(f"[KeyRotator] Redis unavailable: {e}")

    async def get_key(self, model_name: str = "gemini-1.5-flash", session_id: Optional[str] = None) -> str:
        """Model-Aware Key Selection with Weighted Random Choice."""
        if not self.keys: return ""
        if not self._use_redis or not self.client: return self.get_next_key()
        
        candidates, weights, now = [], [], time.time()
        for idx, key in enumerate(self.keys):
            kid = self._get_key_id(key)
            if await self.client.exists(f"{self.BLACKLIST_PREFIX}{kid}") or await self.is_model_daily_exhausted(key, model_name): continue
            
            meta = await self.client.hgetall(f"{self.METADATA_PREFIX}{kid}")
            fail, last, health = int(meta.get("fail_count", 0)), float(meta.get("last_used", 0)), int(meta.get("health_score", 100))
            if fail > 0 and now - last < min(self.BASE_COOLDOWN * (2**(fail-1)), self.MAX_COOLDOWN): continue
            
            try:
                await self.client.zremrangebyscore(f"{self.TPM_PREFIX}{kid}", 0, now - 60)
                tpm_ms = await self.client.zrangebyscore(f"{self.TPM_PREFIX}{kid}", now - 60, now)
                if len(tpm_ms) >= self.MAX_RPM or sum(int(m.split(":")[1]) for m in tpm_ms if ":" in m) >= self.MAX_TPM: continue
            except: pass
            
            candidates.append(idx); weights.append(health)

        if not candidates:
            # Fallback check logic for precise error reporting
            bl_count = 0
            for k in self.keys:
                if await self.client.exists(f"{self.BLACKLIST_PREFIX}{self._get_key_id(k)}"):
                    bl_count += 1
            if bl_count == len(self.keys): raise Exception("AUTH_ERROR: All keys blacklisted.")
            raise Exception(f"QUOTA/COOLDOWN: No keys for '{model_name}'.")

        chosen_idx = random.choices(candidates, weights=weights, k=1)[0]
        chosen_key = self.keys[chosen_idx]
        await self.client.hset(f"{self.METADATA_PREFIX}{self._get_key_id(chosen_key)}", "last_used", now)
        self.index = chosen_idx
        await asyncio.sleep(random.uniform(0.05, 0.15)); return chosen_key

key_rotator = SmartKeyRotator()
