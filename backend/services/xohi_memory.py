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
import time
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

    async def learn_stt_correction(self, user_id: str, wrong: str, right: str, is_global: bool = True):
        """Permanently store a learned STT correction (normalized) with metadata."""
        norm_wrong = wrong.strip().lower()
        
        # Determine target key
        key = "system:stt_overrides" if is_global else f"xohi:stt:{user_id}"
        meta_key = f"{key}:meta"
        
        try:
            # Update mapping
            await self.client.hset(key, norm_wrong, right.strip())
            
            # Update metadata (Neural Synapse)
            meta_raw = await self.client.hget(meta_key, norm_wrong)
            meta = json.loads(meta_raw) if meta_raw else {"count": 0, "created_at": time.time()}
            meta["count"] += 1
            meta["last_used"] = time.time()
            await self.client.hset(meta_key, norm_wrong, json.dumps(meta))
            
            logger.info(f"[XoHiMemory] Learned {'GLOBAL' if is_global else 'USER'}: '{norm_wrong}' → '{right}' (uses={meta['count']})")
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis hash set failed: {e}")

        # Update fallback
        self._fallback_cache[key] = self._fallback_cache.get(key, {})
        self._fallback_cache[key][norm_wrong] = right

    async def increment_stt_usage(self, wrong_word: str, is_global: bool = True):
        """Neural Aging: Increment usage count and update timestamp."""
        key = "system:stt_overrides" if is_global else "xohi:stt:default" # Simplified
        meta_key = f"{key}:meta"
        try:
            meta_raw = await self.client.hget(meta_key, wrong_word)
            if meta_raw:
                meta = json.loads(meta_raw)
                meta["count"] += 1
                meta["last_used"] = time.time()
                await self.client.hset(meta_key, wrong_word, json.dumps(meta))
        except Exception: pass

    async def get_stt_metadata(self, is_global: bool = True) -> Dict[str, dict]:
        """Fetch all metadata for pruning analysis."""
        key = "system:stt_overrides" if is_global else "xohi:stt:default"
        meta_key = f"{key}:meta"
        try:
            data = await self.client.hgetall(meta_key)
            if data:
                return {k: json.loads(v) for k, v in data.items()}
        except Exception: pass
        return {}

    async def prune_stt_overrides(self, max_size: int = 500, is_global: bool = True):
        """Neural Pruning: Remove low-utility synapses to keep memory lean."""
        key = "system:stt_overrides" if is_global else "xohi:stt:default"
        meta_key = f"{key}:meta"
        
        try:
            metadata = await self.get_stt_metadata(is_global)
            if len(metadata) <= max_size:
                return
            
            # Sort by utility: (count * intensity) / age
            now = time.time()
            # We'll just sort by last_used and count for simplicity (Lightweight)
            # Bottom 20% or those exceeding limit
            items = sorted(
                metadata.items(), 
                key=lambda x: (x[1].get("count", 1), x[1].get("last_used", 0))
            )
            
            to_remove = [k for k, v in items[:len(metadata) - max_size]]
            if to_remove:
                await self.client.hdel(key, *to_remove)
                await self.client.hdel(meta_key, *to_remove)
                logger.info(f"[XoHiMemory] Pruned {len(to_remove)} obsolete STT synapses.")
                
                # Update fallback
                if key in self._fallback_cache:
                    for k in to_remove:
                        self._fallback_cache[key].pop(k, None)
        except Exception as e:
            logger.warning(f"[XoHiMemory] Pruning failed: {e}")

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

    # ═══════════════════════════════════════════════════════
    # SYSTEM LEXICON: Dynamic Configs (2026 Microservices)
    # ═══════════════════════════════════════════════════════

    async def get_system_stt_overrides(self) -> Dict[str, str]:
        key = "system:stt_overrides"
        try:
            data = await self.client.hgetall(key)
            if data:
                return dict(data)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis get system:stt_overrides failed: {e}")
        return self._fallback_cache.get(key, {})

    async def set_system_stt_overrides(self, mapping: dict):
        key = "system:stt_overrides"
        try:
            if mapping:
                await self.client.hset(key, mapping=mapping)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis set system:stt_overrides failed: {e}")
        self._fallback_cache[key] = mapping

    async def delete_system_stt_override(self, wrong_word: str):
        key = "system:stt_overrides"
        try:
            await self.client.hdel(key, wrong_word)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis hdel system:stt_overrides failed: {e}")
        self._fallback_cache.get(key, {}).pop(wrong_word, None)

    async def get_system_stt_stopwords(self) -> list:
        key = "system:stt_stopwords"
        try:
            data = await self.client.smembers(key)
            if data:
                return list(data)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis smembers system:stt_stopwords failed: {e}")
        return self._fallback_cache.get(key, [])

    async def add_system_stt_stopword(self, word: str):
        key = "system:stt_stopwords"
        try:
            await self.client.sadd(key, word)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis sadd system:stt_stopwords failed: {e}")
        if key not in self._fallback_cache:
            self._fallback_cache[key] = set()
        if isinstance(self._fallback_cache[key], list):
            self._fallback_cache[key] = set(self._fallback_cache[key])
        self._fallback_cache[key].add(word)

    async def delete_system_stt_stopword(self, word: str):
        key = "system:stt_stopwords"
        try:
            await self.client.srem(key, word)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis srem system:stt_stopwords failed: {e}")
        if key in self._fallback_cache and isinstance(self._fallback_cache[key], set):
            self._fallback_cache[key].discard(word)

    async def get_system_intent_mapping(self) -> dict:
        key = "system:intent_mapping"
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis get system:intent_mapping failed: {e}")
        return self._fallback_cache.get(key, {})

    async def set_system_intent_mapping(self, mapping: dict):
        key = "system:intent_mapping"
        try:
            await self.client.set(key, json.dumps(mapping, ensure_ascii=False))
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis set system:intent_mapping failed: {e}")
        self._fallback_cache[key] = mapping

    # ═══════════════════════════════════════════════════════
    # ATOMIC AGGREGATION: High-Load Performance (V76.3)
    # ═══════════════════════════════════════════════════════

    async def get_full_orchestrator_context(self, user_id: str) -> dict:
        """
        Atomic Context Fetch — Fetches profile, ctx, and STT dict in 1-2 RTTs.
        Optimized for 1M+ requests scaling (Rule R82.25).
        """
        if not self._use_redis:
            return {
                "profile": self._fallback_cache.get(f"profile:{user_id}", {}),
                "ctx": self._fallback_cache.get(f"ctx:{user_id}", {}),
                "stt": self._fallback_cache.get(f"stt:{user_id}", {}),
                "sys_stt": self._fallback_cache.get("system:stt_overrides", {}),
                "intent_map": self._fallback_cache.get("system:intent_mapping", {})
            }

        keys = [
            f"xohi:profile:{user_id}",
            f"xohi:ctx:{user_id}",
            "system:stt_overrides",
            "system:intent_mapping"
        ]

        try:
            # Use Pipeline for atomic read performance
            async with self.client.pipeline(transaction=False) as pipe:
                pipe.get(keys[0])
                pipe.get(keys[1])
                pipe.hgetall(keys[2])
                pipe.hgetall(f"xohi:stt:{user_id}")
                pipe.get(keys[3])
                results = await pipe.execute()

            profile = json.loads(results[0]) if results[0] else {}
            ctx = json.loads(results[1]) if results[1] else {}
            sys_stt = dict(results[2]) if results[2] else {}
            user_stt = dict(results[3]) if results[3] else {}
            intent_map = json.loads(results[4]) if results[4] else {}

            return {
                "profile": profile,
                "ctx": ctx,
                "stt": {**sys_stt, **user_stt, **ctx.get("stt_dictionary", {})},
                "intent_map": intent_map
            }
        except Exception as e:
            logger.error(f"[XoHiMemory] Atomic Fetch Failed: {e}")
            return {"profile": {}, "ctx": {}, "stt": {}, "intent_map": {}}

    # ═══════════════════════════════════════════════════════
    # CHAT CACHE: Redis-Last-10 (V56.0)
    # ═══════════════════════════════════════════════════════

    async def get_recent_chat(self, user_id: str) -> List[dict]:
        """Get the last 10 chat messages for a user from Redis."""
        key = f"xohi:chat:{user_id}"
        try:
            if self._use_redis:
                data = await self.client.lrange(key, 0, 9)
                if data:
                    # Redis list preserves order (LPUSH makes [9, 8, ... 0])
                    # We want chronological [0...9] if we return the list as is, 
                    # but typically FE wants the newest at the bottom or top.
                    # Controllers will handle sorting to match DB standard (DESC).
                    return [json.loads(m) for m in data]
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis chat get failed: {e}")
        return []

    async def add_chat_to_cache(self, user_id: str, message: dict, limit: int = 10):
        """Push a message to user's Redis chat list and trim to specified limit."""
        key = f"xohi:chat:{user_id}"
        try:
            if self._use_redis:
                await self.client.lpush(key, json.dumps(message, ensure_ascii=False))
                # Trim to limit - 1 (e.g. limit 10 -> index 0-9)
                await self.client.ltrim(key, 0, max(0, limit - 1))
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis chat push failed: {e}")


# Singleton
xohi_memory = XoHiMemory()
