# apps/api-gateway/src/services/xohi_memory.py
"""
XoHi Persistent Memory — Redis-backed context & STT learning.
=============================================================
Replaces in-memory voice_cache with persistent Redis storage.
Keys survive container restarts.

Key Patterns:
    xohi:ctx:{user_id}  → JSON: {last_target, last_timeframe, is_confirming_stt, ...}
    xohi:stt:{user_id}  → Hash: {wrong_word: right_word}  (permanent)
    xohi:profile:{user_id} → JSON: {wake_words, sleep_words, greeting_template, capabilities}
"""
import os
import json
import logging
from typing import Optional, Dict

import redis.asyncio as redis

logger = logging.getLogger("api-gateway")

# Context TTL: 24 hours (conversation context expires)
CTX_TTL = 86400
# STT Dictionary: No TTL (learned corrections are permanent)
STT_TTL = None
# Profile cache TTL: 1 hour (re-fetched from DB periodically)  
PROFILE_TTL = 3600


class XoHiMemory:
    """
    Persistent memory layer for XoHi assistant.
    Wraps Redis for sub-millisecond reads with automatic fallback to dict.
    """

    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self._fallback_cache: Dict[str, dict] = {}
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self._use_redis = True
            logger.info(f"[XoHiMemory] Connected to Redis: {redis_url}")
        except Exception:
            logger.warning("[XoHiMemory] Redis unavailable, using in-memory fallback.")
            # V56.0: Replace MagicMock (returns truthy ghosts) with None
            self.client = None
            self._use_redis = False

    # ═══════════════════════════════════════════════════════
    # CONTEXT: last_target, last_timeframe, STT state
    # ═══════════════════════════════════════════════════════

    async def get_user_context(self, user_id: str) -> dict:
        """Get user's conversation context (last_target, last_timeframe, etc.)."""
        key = f"xohi:ctx:{user_id}"
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis get failed: {e}")

        return self._fallback_cache.get(f"ctx:{user_id}", {})

    async def set_user_context(self, user_id: str, context: dict):
        """Persist user's conversation context."""
        key = f"xohi:ctx:{user_id}"
        try:
            await self.client.set(key, json.dumps(context, ensure_ascii=False), ex=CTX_TTL)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis set failed: {e}")

        self._fallback_cache[f"ctx:{user_id}"] = context

    # ═══════════════════════════════════════════════════════
    # STT DICTIONARY: Learned corrections (permanent)
    # ═══════════════════════════════════════════════════════

    async def get_stt_dictionary(self, user_id: str) -> Dict[str, str]:
        """Get user's learned STT corrections."""
        key = f"xohi:stt:{user_id}"
        try:
            data = await self.client.hgetall(key)
            if data:
                return dict(data)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis hgetall failed: {e}")

        return self._fallback_cache.get(f"stt:{user_id}", {})

    async def learn_stt_correction(self, user_id: str, wrong: str, right: str):
        """Permanently store a learned STT correction."""
        key = f"xohi:stt:{user_id}"
        try:
            await self.client.hset(key, wrong, right)
            logger.info(f"[XoHiMemory] Learned: '{wrong}' → '{right}' for {user_id}")
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis hset failed: {e}")

        # Also update fallback
        if f"stt:{user_id}" not in self._fallback_cache:
            self._fallback_cache[f"stt:{user_id}"] = {}
        self._fallback_cache[f"stt:{user_id}"][wrong] = right

    # ═══════════════════════════════════════════════════════
    # VOICE PROFILE: wake_words, sleep_words, capabilities
    # ═══════════════════════════════════════════════════════

    async def get_voice_profile(self, user_id: str) -> Optional[dict]:
        """Get cached voice profile for a user."""
        key = f"xohi:profile:{user_id}"
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis profile get failed: {e}")

        return self._fallback_cache.get(f"profile:{user_id}")

    async def cache_voice_profile(self, user_id: str, profile: dict):
        """Cache a voice profile from DB into Redis."""
        key = f"xohi:profile:{user_id}"
        try:
            await self.client.set(key, json.dumps(profile, ensure_ascii=False), ex=PROFILE_TTL)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis profile set failed: {e}")

        self._fallback_cache[f"profile:{user_id}"] = profile


# Singleton
xohi_memory = XoHiMemory()
