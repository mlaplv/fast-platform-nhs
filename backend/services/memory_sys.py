import json
import logging
from typing import Dict, List

logger = logging.getLogger("api-gateway")

class SystemMemoryMixin:
    """Mixin for System Lexicon, Stopwords, and Intent Mapping."""

    async def get_system_stt_overrides(self) -> Dict[str, str]:
        key = "system:stt_overrides"
        try:
            data = await self.client.hgetall(key)
            if data: return dict(data)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis get system:stt_overrides failed: {e}")
        return self._fallback_cache.get(key, {})

    async def set_system_stt_overrides(self, mapping: dict):
        key = "system:stt_overrides"
        try:
            if mapping: await self.client.hset(key, mapping=mapping)
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
            if data: return list(data)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis smembers system:stt_stopwords failed: {e}")
        return list(self._fallback_cache.get(key, []))

    async def add_system_stt_stopword(self, word: str):
        key = "system:stt_stopwords"
        try:
            await self.client.sadd(key, word)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis sadd system:stt_stopwords failed: {e}")
        if key not in self._fallback_cache: self._fallback_cache[key] = set()
        target = self._fallback_cache[key]
        if isinstance(target, list): target = set(target); self._fallback_cache[key] = target
        if isinstance(target, set): target.add(word)

    async def delete_system_stt_stopword(self, word: str):
        key = "system:stt_stopwords"
        try:
            await self.client.srem(key, word)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis srem system:stt_stopwords failed: {e}")
        target = self._fallback_cache.get(key)
        if isinstance(target, set): target.discard(word)

    async def get_system_intent_mapping(self) -> dict:
        key = "system:intent_mapping"
        try:
            data = await self.client.get(key)
            if data: return json.loads(data)
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

    async def get_semantic_centroids(self) -> Dict[str, bytes]:
        key = "system:semantic_centroids"
        try:
            if self._use_redis: return await self.client.hgetall(key)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis get semantic_centroids failed: {e}")
        return {}

    async def update_semantic_centroid(self, intent: str, vector_bytes: bytes):
        key = "system:semantic_centroids"
        try:
            if self._use_redis: await self.client.hset(key, intent, vector_bytes)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis set semantic_centroid failed: {e}")
