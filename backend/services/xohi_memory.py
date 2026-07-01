# apps/api-gateway/src/services/xohi_memory.py
"""
XoHi Persistent Memory — Redis-backed context & STT learning.
Modularized for Martial Law (<300 LOC).
"""
import os
import json
import logging
from typing import Optional, Dict, List, Union
from pydantic import JsonValue

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

def _decrypt_json(data_val: Union[str, bytes]) -> object:
    from backend.utils.security import GeminiSecurity
    try:
        data_str = data_val.decode() if isinstance(data_val, bytes) else str(data_val)
        decrypted = GeminiSecurity.decrypt(data_str)
        if isinstance(decrypted, (dict, list)):
            return decrypted
        if isinstance(decrypted, str):
            try:
                return json.loads(decrypted)
            except Exception:
                return decrypted
        return decrypted
    except Exception:
        try:
            data_str = data_val.decode() if isinstance(data_val, bytes) else str(data_val)
            return json.loads(data_str)
        except Exception:
            return data_val

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

    async def get_user_context(self, user_id: str) -> Dict[str, JsonValue]:
        key = f"xohi:ctx:{user_id}"
        try:
            data = await self.client.get(key)
            if data:
                res = _decrypt_json(data)
                if isinstance(res, dict): return res
        except Exception as e: logger.debug(f"[XoHiMemory] Redis get failed: {e}")
        return self._fallback_cache.get(f"ctx:{user_id}", {})

    async def set_user_context(self, user_id: str, context: Dict[str, JsonValue]):
        key = f"xohi:ctx:{user_id}"
        try:
            from backend.utils.security import GeminiSecurity
            encrypted = GeminiSecurity.encrypt(context)
            await self.client.set(key, encrypted, ex=CTX_TTL)
        except Exception as e: logger.debug(f"[XoHiMemory] Redis set failed: {e}")
        self._fallback_cache[f"ctx:{user_id}"] = context

    async def get_voice_profile(self, user_id: str) -> Optional[Dict[str, JsonValue]]:
        key = f"xohi:profile:{user_id}"
        try:
            data = await self.client.get(key)
            if data:
                res = _decrypt_json(data)
                if isinstance(res, dict): return res
        except Exception as e: logger.debug(f"[XoHiMemory] Redis profile get failed: {e}")
        return self._fallback_cache.get(f"profile:{user_id}")

    async def cache_voice_profile(self, user_id: str, profile: Dict[str, JsonValue]):
        key = f"xohi:profile:{user_id}"
        try:
            from backend.utils.security import GeminiSecurity
            encrypted = GeminiSecurity.encrypt(profile)
            await self.client.set(key, encrypted, ex=PROFILE_TTL)
        except Exception as e: logger.debug(f"[XoHiMemory] Redis profile set failed: {e}")
        self._fallback_cache[f"profile:{user_id}"] = profile

    # ═══════════════════════════════════════════════════════
    # ATOMIC AGGREGATION & CHAT CACHE
    # ═══════════════════════════════════════════════════════

    async def get_full_orchestrator_context(self, user_id: str) -> Dict[str, JsonValue]:
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

            profile_data = res[0].decode() if isinstance(res[0], bytes) else res[0]
            ctx_data = res[1].decode() if isinstance(res[1], bytes) else res[1]

            profile = _decrypt_json(profile_data) if profile_data else {}
            ctx = _decrypt_json(ctx_data) if ctx_data else {}
            stt = {**(dict(res[2]) if res[2] else {}), **(dict(res[3]) if res[3] else {}), **(ctx.get("stt_dictionary", {}) if isinstance(ctx, dict) else {})}
            intent_map = json.loads(res[4]) if res[4] else {}
            
            profile_dict = profile if isinstance(profile, dict) else {}
            ctx_dict = ctx if isinstance(ctx, dict) else {}
            return {"profile": profile_dict, "ctx": ctx_dict, "stt": stt, "intent_map": intent_map}
        except Exception as e:
            logger.error(f"[XoHiMemory] Atomic Fetch Failed: {e}")
            return {"profile": {}, "ctx": {}, "stt": {}, "intent_map": {}}

    async def get_recent_chat(self, user_id: str, limit: int = 20) -> List[Dict[str, JsonValue]]:
        """[Bug #6 Fix] Nhận tham số limit thay vì hardcode 10."""
        key = f"xohi:chat:{user_id}"
        try:
            if self._use_redis:
                data = await self.client.lrange(key, 0, limit - 1)
                if data:
                    res_list = []
                    for m in data:
                        m_str = m.decode() if isinstance(m, bytes) else str(m)
                        dec = _decrypt_json(m_str)
                        if isinstance(dec, dict):
                            res_list.append(dec)
                    return res_list
        except Exception as e: logger.debug(f"[XoHiMemory] Redis chat get failed: {e}")
        return []

    async def add_chat_to_cache(self, user_id: str, message: Dict[str, JsonValue], limit: int = 20):
        """[Bug #5 Fix] Dùng Redis pipeline — 1 round-trip thay vì 2."""
        key = f"xohi:chat:{user_id}"
        try:
            if self._use_redis:
                from backend.utils.security import GeminiSecurity
                encrypted_msg = GeminiSecurity.encrypt(message)
                async with self.client.pipeline(transaction=False) as pipe:
                    pipe.lpush(key, encrypted_msg)
                    pipe.ltrim(key, 0, max(0, limit - 1))
                    await pipe.execute()
        except Exception as e: logger.debug(f"[XoHiMemory] Redis chat push failed: {e}")

    async def delete_pattern(self, pattern: str):
        try:
            if self._use_redis:
                keys = await self.client.keys(pattern)
                if keys: await self.client.delete(*keys)
        except Exception as e: logger.warning(f"[XoHiMemory] Redis pattern delete failed: {e}")

    async def clear_article_cache(self):
        if self._use_redis and self.client:
            try:
                keys = await self.client.smembers("articles:cache_keys")
                if keys:
                    await self.client.delete(*keys)
                await self.client.delete("articles:cache_keys")
            except Exception as e:
                logger.warning(f"[XoHiMemory] clear_article_cache failed: {e}")

    # ═══════════════════════════════════════════════════════
    # THREE-LAYER MEMORY ARCHITECTURE — Elite V2.2
    # ═══════════════════════════════════════════════════════
    
    async def get_kb_index(self) -> str:
        """
        Layer 1: Index (Mục lục).
        Luôn được nạp vào context, chứa các con trỏ ngắn <150 ký tự.
        """
        try:
            if self._use_redis:
                data = await self.client.get("support:kb:index")
                if data: return data
        except Exception as e: logger.debug(f"[XoHiMemory] KB Index get failed: {e}")
        return "Hiện chưa có mục lục kiến thức. Sếp có thể dùng công cụ tìm kiếm bài viết để tra cứu dữ liệu thô."

    async def get_kb_topic(self, topic_id: str) -> Optional[str]:
        """
        Layer 2: Topic Files (Chủ đề).
        Chỉ được gọi (fetch) ra khi AI thực sự cần (thông qua tool).
        """
        try:
            if self._use_redis:
                data = await self.client.get(f"support:kb:topic:{topic_id}")
                if data: return data
        except Exception as e: logger.debug(f"[XoHiMemory] KB Topic {topic_id} get failed: {e}")
        return None

    async def list_kb_topics(self) -> List[Dict[str, str]]:
        """Lấy danh sách các chủ đề hiện có để xây dựng mục lục Layer 1."""
        try:
            if self._use_redis:
                keys = await self.client.keys("support:kb:topic:*")
                topics = []
                for k in keys:
                    tid = k.split(":")[-1]
                    # Lấy 100 ký tự đầu làm snippet cho Index
                    content = await self.client.get(k)
                    snippet = (content[:147] + "...") if content and len(content) > 150 else (content or "")
                    topics.append({"id": tid, "summary": snippet})
                return topics
        except Exception as e: logger.debug(f"[XoHiMemory] List topics failed: {e}")
        return []

    async def refresh_kb_index(self):
        """Tự động xây dựng lại Layer 1 từ các Topic Layer 2."""
        topics = await self.list_kb_topics()
        if not topics:
            index_str = "Hệ thống kiến thức đang trống."
        else:
            index_str = "MỤC LỤC KIẾN THỨC CÓ SẴN:\n" + "\n".join([f"- {t['id']}: {t['summary']}" for t in topics])
        
        await self.set_kb_layer1(index_str, key="support:kb:index")
        return index_str

    async def get_kb_layer1(self, key: str = "support:kb:index") -> Optional[str]:
        """Legacy compatibility wrapper for get_kb_index."""
        return await self.get_kb_index()

    async def set_kb_layer1(self, content: str, key: str = "support:kb:index", ttl: int = 86400):
        """Elite V2.2: Cache Layer 1 Knowledge Index (Default 24h)."""
        try:
            if self._use_redis:
                await self.client.set(key, content, ex=ttl)
        except Exception as e: logger.debug(f"[XoHiMemory] KB Layer 1 set failed: {e}")

    async def clear_kb_cache(self):
        """Elite V2.2: Purge all KB related cache."""
        await self.delete_pattern("support:kb:*")

    async def delete_campaign_memory(self, campaign_id: str, user_id: Optional[str] = None):
        """
        Elite V2.2: Full Resource Disposal.
        Purges pulse cache, analysis results, and optionally user chat logs from Redis.
        """
        try:
            if self._use_redis:
                # 1. Pulse & Progress Caches
                await self.delete_pattern(f"pulse:{campaign_id}*")
                # 2. Analysis & Operative Caches (Structured)
                await self.delete_pattern(f"xohi:analysis:{campaign_id}*")
                # 3. User Chat Cache (Purge recent logs to avoid stale references)
                if user_id:
                    await self.client.delete(f"xohi:chat:{user_id}")
                    
                logger.info(f"[XoHiMemory] Redis Purge complete for campaign: {campaign_id}")
        except Exception as e:
            logger.warning(f"[XoHiMemory] Failed to purge campaign memory: {e}")

    # ═══════════════════════════════════════════════════════
    # ORDER DRAFT PERSISTENCE — Elite V3.6
    # ═══════════════════════════════════════════════════════

    async def get_order_draft(self, session_id: str) -> Optional[Dict[str, object]]:
        """Retrieve the pending order draft for slot-filling context."""
        key = f"support:order_draft:{session_id}"
        try:
            if self._use_redis:
                data = await self.client.get(key)
                if data:
                    res = _decrypt_json(data)
                    if isinstance(res, dict): return res
        except Exception as e: logger.debug(f"[XoHiMemory] Draft get failed: {e}")
        return None

    async def set_order_draft(self, session_id: str, draft_data: Dict[str, object], ttl: int = 180):
        """Persist the pending order draft. [SECURITY] Default TTL=180s (3 min) — chống inventory lockout attack."""
        key = f"support:order_draft:{session_id}"
        try:
            if self._use_redis:
                from backend.utils.security import GeminiSecurity
                encrypted = GeminiSecurity.encrypt(draft_data)
                await self.client.set(key, encrypted, ex=ttl)
                logger.info(f"💾 [XoHiMemory] Draft persisted for SID: {session_id}")
        except Exception as e:
            logger.error(f"[XoHiMemory] Draft set FAILED: {e}")

    async def clear_order_draft(self, session_id: str):
        key = f"support:order_draft:{session_id}"
        try:
            if self._use_redis:
                await self.client.delete(key)
        except Exception as e: logger.debug(f"[XoHiMemory] Draft clear failed: {e}")

# Singleton
xohi_memory = XoHiMemory()
