# apps/api-gateway/src/services/xohi_memory.py
"""
XoHi Persistent Memory — Redis-backed context & STT learning.
Modularized for Martial Law (<300 LOC).
"""
import os
import json
import logging
from typing import Optional, Dict, List, Union

try:
    import redis.asyncio as redis
except ImportError:
    from redis import asyncio as redis

from .memory_stt import STTMemoryMixin
from .memory_sys import SystemMemoryMixin

logger = logging.getLogger("api-gateway")

# TTLs
CTX_TTL = 86400
PROFILE_TTL = 3600

class XoHiMemory(STTMemoryMixin, SystemMemoryMixin):
    """
    Persistent memory layer for XoHi assistant.
    Modularized architecture: inherited STT and System logic.
    """

    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self._fallback_cache: Dict[str, object] = {}
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self._use_redis = True
            logger.info(f"[XoHiMemory] Connected to Redis: {redis_url}")
        except Exception:
            logger.warning("[XoHiMemory] Redis unavailable, using in-memory fallback.")
            self.client = None
            self._use_redis = False

    # ═══════════════════════════════════════════════════════
    # CONTEXT & PROFILE
    # ═══════════════════════════════════════════════════════

    async def get_user_context(self, user_id: str) -> dict:
        key = f"xohi:ctx:{user_id}"
        try:
            data = await self.client.get(key)
            if data: return json.loads(data)
        except Exception as e: logger.debug(f"[XoHiMemory] Redis get failed: {e}")
        return self._fallback_cache.get(f"ctx:{user_id}", {})

    async def set_user_context(self, user_id: str, context: dict):
        key = f"xohi:ctx:{user_id}"
        try: await self.client.set(key, json.dumps(context, ensure_ascii=False), ex=CTX_TTL)
        except Exception as e: logger.debug(f"[XoHiMemory] Redis set failed: {e}")
        self._fallback_cache[f"ctx:{user_id}"] = context

    async def get_voice_profile(self, user_id: str) -> Optional[dict]:
        key = f"xohi:profile:{user_id}"
        try:
            data = await self.client.get(key)
            if data: return json.loads(data)
        except Exception as e: logger.debug(f"[XoHiMemory] Redis profile get failed: {e}")
        return self._fallback_cache.get(f"profile:{user_id}")

    async def cache_voice_profile(self, user_id: str, profile: dict):
        key = f"xohi:profile:{user_id}"
        try: await self.client.set(key, json.dumps(profile, ensure_ascii=False), ex=PROFILE_TTL)
        except Exception as e: logger.debug(f"[XoHiMemory] Redis profile set failed: {e}")
        self._fallback_cache[f"profile:{user_id}"] = profile

    # ═══════════════════════════════════════════════════════
    # ATOMIC AGGREGATION & CHAT CACHE
    # ═══════════════════════════════════════════════════════

    async def get_full_orchestrator_context(self, user_id: str) -> dict:
        if not self._use_redis:
            return {
                "profile": self._fallback_cache.get(f"profile:{user_id}", {}),
                "ctx": self._fallback_cache.get(f"ctx:{user_id}", {}),
                "stt": {**self._fallback_cache.get("system:stt_overrides", {}), **self._fallback_cache.get(f"stt:{user_id}", {})},
                "intent_map": self._fallback_cache.get("system:intent_mapping", {})
            }

        try:
            async with self.client.pipeline(transaction=False) as pipe:
                pipe.get(f"xohi:profile:{user_id}")
                pipe.get(f"xohi:ctx:{user_id}")
                pipe.hgetall("system:stt_overrides")
                pipe.hgetall(f"xohi:stt:{user_id}")
                pipe.get("system:intent_mapping")
                res = await pipe.execute()

            profile = json.loads(res[0]) if res[0] else {}
            ctx = json.loads(res[1]) if res[1] else {}
            stt = {**(dict(res[2]) if res[2] else {}), **(dict(res[3]) if res[3] else {}), **ctx.get("stt_dictionary", {})}
            intent_map = json.loads(res[4]) if res[4] else {}
            return {"profile": profile, "ctx": ctx, "stt": stt, "intent_map": intent_map}
        except Exception as e:
            logger.error(f"[XoHiMemory] Atomic Fetch Failed: {e}")
            return {"profile": {}, "ctx": {}, "stt": {}, "intent_map": {}}

    async def get_recent_chat(self, user_id: str) -> List[dict]:
        key = f"xohi:chat:{user_id}"
        try:
            if self._use_redis:
                data = await self.client.lrange(key, 0, 9)
                if data: return [json.loads(m) for m in data]
        except Exception as e: logger.debug(f"[XoHiMemory] Redis chat get failed: {e}")
        return []

    async def add_chat_to_cache(self, user_id: str, message: dict, limit: int = 10):
        key = f"xohi:chat:{user_id}"
        try:
            if self._use_redis:
                await self.client.lpush(key, json.dumps(message, ensure_ascii=False))
                await self.client.ltrim(key, 0, max(0, limit - 1))
        except Exception as e: logger.debug(f"[XoHiMemory] Redis chat push failed: {e}")

    async def delete_pattern(self, pattern: str):
        try:
            if self._use_redis:
                keys = await self.client.keys(pattern)
                if keys: await self.client.delete(*keys)
        except Exception as e: logger.warning(f"[XoHiMemory] Redis pattern delete failed: {e}")

    async def clear_article_cache(self):
        await self.delete_pattern("articles:count:*")

    # ═══════════════════════════════════════════════════════
    # KNOWLEDGE BASE LAYER 1 (CACHE) — Elite V2.2
    # ═══════════════════════════════════════════════════════
    async def get_kb_layer1(self, key: str = "support:kb:layer1") -> Optional[str]:
        """Elite V2.2: Fetch Layer 1 Knowledge Index from Redis."""
        try:
            if self._use_redis:
                data = await self.client.get(key)
                if data: return data
        except Exception as e: logger.debug(f"[XoHiMemory] KB Layer 1 get failed: {e}")
        return None

    async def set_kb_layer1(self, content: str, key: str = "support:kb:layer1", ttl: int = 3600):
        """Elite V2.2: Cache Layer 1 Knowledge Index (Default 1h)."""
        try:
            if self._use_redis:
                await self.client.set(key, content, ex=ttl)
        except Exception as e: logger.debug(f"[XoHiMemory] KB Layer 1 set failed: {e}")

    async def clear_kb_cache(self):
        """Elite V2.2: Purge all KB related cache."""
        await self.delete_pattern("support:kb:*")

# Singleton
xohi_memory = XoHiMemory()
