import logging
import time
import random
from typing import Optional, Dict

logger = logging.getLogger("key-metrics")

class KeyMetricsMixin:
    async def mark_unhealthy(self, key: str, reason: str = "rate_limit", session_id: Optional[str] = None) -> None:
        """Circuit Breaker Logic using Hash ID."""
        if not self._use_redis: return
        kid: str = self._get_key_id(key); reason_lower: str = reason.lower(); now: float = time.time()
        
        # Elite V2.2: Hard Auth failure - Immediate long blacklist
        if any(p in reason_lower for p in ["auth_hard", "invalid", "disabled", "expired"]):
            await self.client.set(f"{self.BLACKLIST_PREFIX}{kid}", reason, ex=self.MAX_COOLDOWN * 30)
            logger.error(f"[KeyRotator] Key {kid[:8]} PERMANENTLY BLACKLISTED: {reason}"); return
            
        # Elite V2.2: Soft Auth / Region failure - 2-strike rule (Smart Cooldown)
        if any(p in reason_lower for p in ["auth_soft", "forbidden", "401", "403"]):
            soft_fails = await self.client.hincrby(f"{self.METADATA_PREFIX}{kid}", "soft_fail_count", 1)
            if soft_fails >= 2:
                await self.client.set(f"{self.BLACKLIST_PREFIX}{kid}", f"SOFT_AUTH: {reason}", ex=600) # 10m cooldown
                logger.info(f"[KeyRotator] Key {kid[:8]} on 10m cooldown (Recurring Soft Failure).")
            else:
                await self.client.hset(f"{self.METADATA_PREFIX}{kid}", "last_used", now)
                logger.info(f"[KeyRotator] Key {kid[:8]} soft failure ({soft_fails}/2). Retrying next...")
            return

        if "daily" in reason_lower or "quota" in reason_lower:
             await self.client.set(f"{self.BLACKLIST_PREFIX}{kid}", f"DAILY: {reason}", ex=self.MAX_COOLDOWN)
             logger.warning(f"[KeyRotator] Key {kid[:8]} hit DAILY QUOTA."); return

        if reason_lower == "rate_limit" or "429" in reason_lower:
            await self.track_tokens(key, 500)
            # Falling through to increment fail_count and trigger backoff.

        fail = await self.client.hincrby(f"{self.METADATA_PREFIX}{kid}", "fail_count", 1)
        await self.client.hset(f"{self.METADATA_PREFIX}{kid}", mapping={"health_score": max(0, 100 - (fail * 20)), "last_used": now})

    async def set_success(self, key: str, session_id: Optional[str] = None) -> None:
        if not self._use_redis: return
        await self.client.hset(f"{self.METADATA_PREFIX}{self._get_key_id(key)}", mapping={"fail_count": 0, "soft_fail_count": 0, "health_score": 100})

    async def track_tokens(self, key: str, tokens: int) -> None:
        if not self._use_redis or tokens <= 0: return
        kid: str = self._get_key_id(key)
        now: float = time.time()
        member: str = f"{now}:{tokens}:{random.randint(10000, 99999)}"
        try:
            async with self.client.pipeline() as pipe:
                pipe.zadd(f"{self.TPM_PREFIX}{kid}", {member: now}); pipe.zremrangebyscore(f"{self.TPM_PREFIX}{kid}", 0, now - 60)
                await pipe.execute()
        except: pass

    async def mark_model_daily(self, key: str, model_name: str) -> None:
        if not self._use_redis or not self.client: return
        kid: str = self._get_key_id(key)
        m_slug: str = str(model_name).replace("/", "_").replace("-", "_")[:40]
        await self.client.set(f"{self.MODEL_DAILY_PREFIX}{kid}:{m_slug}", "DAILY_EXHAUSTED", ex=self.MAX_COOLDOWN)

    async def is_model_daily_exhausted(self, key: str, model_name: str) -> bool:
        if not self._use_redis or not self.client: return False
        kid, m_slug = self._get_key_id(key), str(model_name).replace("/", "_").replace("-", "_")[:40]
        return bool(await self.client.exists(f"{self.MODEL_DAILY_PREFIX}{kid}:{m_slug}"))

    async def mark_model_poisoned(self, model_name: str, reason: str = "404") -> None:
        if not self._use_redis or not self.client: return
        m_slug: str = model_name.replace("/", "_").replace("-", "_")[:40]
        await self.client.set(f"{self.POISON_PREFIX}{m_slug}", reason, ex=self.MAX_COOLDOWN)

    async def is_model_poisoned(self, model_name: str) -> bool:
        if not self._use_redis or not self.client: return False
        m_slug = model_name.replace("/", "_").replace("-", "_")[:40]
        return bool(await self.client.exists(f"{self.POISON_PREFIX}{m_slug}"))

    async def mark_model_capability(self, model_name: str, capability: str) -> None:
        """Elite V2.2: Persist model capability (LEGACY, AGENTIC, ELITE)."""
        if not self._use_redis or not self.client: return
        m_slug = model_name.replace("/", "_").replace("-", "_")[:40]
        await self.client.set(f"{self.MODEL_CAPABILITY_PREFIX}{m_slug}", capability, ex=self.MAX_COOLDOWN)

    async def get_model_capability(self, model_name: str) -> str:
        if not self._use_redis or not self.client: return "LEGACY"
        m_slug = model_name.replace("/", "_").replace("-", "_")[:40]
        val = await self.client.get(f"{self.MODEL_CAPABILITY_PREFIX}{m_slug}")
        return val if val else "LEGACY"

    async def save_model_metadata(self, model_name: str, metadata: dict) -> None:
        if not self._use_redis or not self.client: return
        m_slug = model_name.replace("/", "_").replace("-", "_")[:40]
        import json
        await self.client.set(f"{self.MODEL_METADATA_PREFIX}{m_slug}", json.dumps(metadata), ex=self.MAX_COOLDOWN)

    async def get_model_metadata(self, model_name: str) -> dict:
        if not self._use_redis or not self.client: return {}
        m_slug = model_name.replace("/", "_").replace("-", "_")[:40]
        import json
        val = await self.client.get(f"{self.MODEL_METADATA_PREFIX}{m_slug}")
        return json.loads(val) if val else {}

    async def reset_health(self, preserve_daily: bool = False) -> int:
        if not self._use_redis or not self.client: return 0
        cleared = 0
        prefixes = [self.BLACKLIST_PREFIX, self.METADATA_PREFIX, self.TPM_PREFIX]
        if not preserve_daily:
            prefixes.append(self.MODEL_DAILY_PREFIX)
            prefixes.append(self.POISON_PREFIX)
            
        for prefix in prefixes:
            async for k in self.client.scan_iter(f"{prefix}*"):
                if prefix == self.METADATA_PREFIX: await self.client.hset(k, mapping={"fail_count": 0, "health_score": 100})
                else: await self.client.delete(k)
                cleared += 1
        await self.load_keys(); return cleared
