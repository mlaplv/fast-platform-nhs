import json
import time
import logging
from typing import Dict, Any

logger = logging.getLogger("api-gateway")

class STTMemoryMixin:
    """Mixin for STT Dictionary & Neural Pruning logic."""
    
    async def get_stt_dictionary(self, user_id: str) -> Dict[str, str]:
        key = f"xohi:stt:{user_id}"
        try:
            data = await self.client.hgetall(key)
            if data: return dict(data)
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis hgetall failed: {e}")
        return self._fallback_cache.get(f"stt:{user_id}", {})

    async def learn_stt_correction(self, user_id: str, wrong: str, right: str, is_global: bool = True):
        norm_wrong = wrong.strip().lower()
        key = "system:stt_overrides" if is_global else f"xohi:stt:{user_id}"
        meta_key = f"{key}:meta"
        try:
            await self.client.hset(key, norm_wrong, right.strip())
            meta_raw = await self.client.hget(meta_key, norm_wrong)
            meta = json.loads(meta_raw) if meta_raw else {"count": 0, "created_at": time.time()}
            if isinstance(meta, dict):
                meta["count"] = meta.get("count", 0) + 1
                meta["last_used"] = time.time()
                await self.client.hset(meta_key, norm_wrong, json.dumps(meta))
                logger.info(f"[XoHiMemory] Learned {'GLOBAL' if is_global else 'USER'}: '{norm_wrong}' -> '{right}' (uses={meta['count']})")
        except Exception as e:
            logger.debug(f"[XoHiMemory] Redis hash set failed: {e}")
        self._fallback_cache[key] = self._fallback_cache.get(key, {})
        self._fallback_cache[key][norm_wrong] = right

    async def increment_stt_usage(self, wrong_word: str, is_global: bool = True):
        key = "system:stt_overrides" if is_global else "xohi:stt:default"
        meta_key = f"{key}:meta"
        try:
            meta_raw = await self.client.hget(meta_key, wrong_word)
            if meta_raw:
                meta = json.loads(meta_raw)
                meta["count"] += 1
                meta["last_used"] = time.time()
                await self.client.hset(meta_key, wrong_word, json.dumps(meta))
        except Exception as e:
            logger.debug(f"[XohiMemory] Context set failed: {e}")

    async def get_stt_metadata(self, is_global: bool = True) -> Dict[str, dict]:
        key = "system:stt_overrides" if is_global else "xohi:stt:default"
        meta_key = f"{key}:meta"
        try:
            data = await self.client.hgetall(meta_key)
            if data: return {k: json.loads(v) for k, v in data.items()}
        except Exception as e:
            logger.debug(f"[XohiMemory] Context set failed: {e}")
        return {}

    async def prune_stt_overrides(self, max_size: int = 500, is_global: bool = True):
        key = "system:stt_overrides" if is_global else "xohi:stt:default"
        meta_key = f"{key}:meta"
        try:
            metadata = await self.get_stt_metadata(is_global)
            if len(metadata) <= max_size: return
            items = sorted(metadata.items(), key=lambda x: (x[1].get("count", 1), x[1].get("last_used", 0)))
            num_to_remove = len(metadata) - max_size
            to_remove = [items[i][0] for i in range(num_to_remove) if i < len(items)]
            if to_remove:
                await self.client.hdel(key, *to_remove)
                await self.client.hdel(meta_key, *to_remove)
                logger.info(f"[XoHiMemory] Pruned {len(to_remove)} obsolete STT synapses.")
                if key in self._fallback_cache:
                    for k in to_remove: self._fallback_cache[key].pop(k, None)
        except Exception as e:
            logger.warning(f"[XoHiMemory] Pruning failed: {e}")
