import logging
import time
import random
from typing import Optional, Dict

logger = logging.getLogger("key-metrics")

class KeyMetricsMixin:
    async def mark_unhealthy(self, key: str, reason: str = "rate_limit", session_id: Optional[str] = None):
        """Circuit Breaker Logic using Hash ID."""
        if not self._use_redis: return
        kid = self._get_key_id(key); reason_lower = reason.lower(); now = time.time()
        
        if "auth_hard" in reason_lower or any(p in reason_lower for p in ["invalid", "disabled", "expired"]):
            await self.client.set(f"{self.BLACKLIST_PREFIX}{kid}", reason, ex=self.MAX_COOLDOWN * 30)
            logger.error(f"[KeyRotator] Key {kid[:8]} PERMANENTLY BLACKLISTED: {reason}"); return
            
        if "auth_soft" in reason_lower or any(p in reason_lower for p in ["401", "403"]):
            await self.client.set(f"{self.BLACKLIST_PREFIX}{kid}", f"SOFT_AUTH: {reason}", ex=600) # 10m cooldown
            logger.warning(f"[KeyRotator] Key {kid[:8]} in 10m cooldown (Soft Auth Failure)."); return

        if "daily" in reason_lower or "quota" in reason_lower:
             await self.client.set(f"{self.BLACKLIST_PREFIX}{kid}", f"DAILY: {reason}", ex=self.MAX_COOLDOWN)
             logger.warning(f"[KeyRotator] Key {kid[:8]} hit DAILY QUOTA."); return

        if reason_lower == "rate_limit" or "429" in reason_lower:
            await self.track_tokens(key, 100); await self.client.hset(f"{self.METADATA_PREFIX}{kid}", "last_used", now); return

        fail = await self.client.hincrby(f"{self.METADATA_PREFIX}{kid}", "fail_count", 1)
        await self.client.hset(f"{self.METADATA_PREFIX}{kid}", mapping={"health_score": max(0, 100 - (fail * 20)), "last_used": now})

    async def set_success(self, key: str, session_id: Optional[str] = None):
        if not self._use_redis: return
        await self.client.hset(f"{self.METADATA_PREFIX}{self._get_key_id(key)}", mapping={"fail_count": 0, "health_score": 100})

    async def track_tokens(self, key: str, tokens: int):
        if not self._use_redis or tokens <= 0: return
        kid, now = self._get_key_id(key), time.time()
        member = f"{now}:{tokens}:{random.randint(10000, 99999)}"
        try:
            async with self.client.pipeline() as pipe:
                pipe.zadd(f"{self.TPM_PREFIX}{kid}", {member: now}); pipe.zremrangebyscore(f"{self.TPM_PREFIX}{kid}", 0, now - 60)
                await pipe.execute()
        except: pass

    async def mark_model_daily(self, key: str, model_name: str):
        if not self._use_redis or not self.client: return
        kid, m_slug = self._get_key_id(key), str(model_name).replace("/", "_").replace("-", "_")[:40]
        await self.client.set(f"{self.MODEL_DAILY_PREFIX}{kid}:{m_slug}", "DAILY_EXHAUSTED", ex=self.MAX_COOLDOWN)

    async def is_model_daily_exhausted(self, key: str, model_name: str) -> bool:
        if not self._use_redis or not self.client: return False
        kid, m_slug = self._get_key_id(key), str(model_name).replace("/", "_").replace("-", "_")[:40]
        return bool(await self.client.exists(f"{self.MODEL_DAILY_PREFIX}{kid}:{m_slug}"))

    async def mark_model_poisoned(self, model_name: str, reason: str = "404"):
        if not self._use_redis or not self.client: return
        m_slug = model_name.replace("/", "_").replace("-", "_")[:40]
        await self.client.set(f"{self.POISON_PREFIX}{m_slug}", reason, ex=self.MAX_COOLDOWN)

    async def is_model_poisoned(self, model_name: str) -> bool:
        if not self._use_redis or not self.client: return False
        m_slug = model_name.replace("/", "_").replace("-", "_")[:40]
        return bool(await self.client.exists(f"{self.POISON_PREFIX}{m_slug}"))

    async def reset_health(self) -> int:
        if not self._use_redis or not self.client: return 0
        cleared = 0
        for prefix in [self.BLACKLIST_PREFIX, self.METADATA_PREFIX, self.MODEL_DAILY_PREFIX, self.TPM_PREFIX]:
            async for k in self.client.scan_iter(f"{prefix}*"):
                if prefix == self.METADATA_PREFIX: await self.client.hset(k, mapping={"fail_count": 0, "health_score": 100})
                else: await self.client.delete(k)
                cleared += 1
        await self.load_keys(); return cleared
