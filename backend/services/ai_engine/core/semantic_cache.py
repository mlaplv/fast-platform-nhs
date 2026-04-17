import json
import hashlib
import logging
from typing import Optional
from backend.services.xohi_memory import xohi_memory

logger = logging.getLogger("api-gateway")

class SemanticCacheService:
    """
    Elite V2.2: Semantic Cache for AI Results.
    Reduces LLM costs and latency by caching idempotent agent results.
    """
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl

    def _generate_key(self, agent_id: str, payload: dict[str, object] | list[object] | str) -> str:
        """Hàm băm tạo key duy nhất dựa trên agent_id và nội dung yêu cầu."""
        payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()[:16]
        return f"ai:cache:{agent_id}:{payload_hash}"

    async def get_cached_result(self, agent_id: str, payload: dict[str, object] | list[object] | str) -> Optional[dict[str, object]]:
        """Kiểm tra xem kết quả đã có trong cache chưa."""
        if not xohi_memory._use_redis:
            return None
            
        if isinstance(payload, dict) and payload.get("force") is True:
            return None
            
        key = self._generate_key(agent_id, payload)
        try:
            data = await xohi_memory.client.get(key)
            if data:
                logger.info(f"✨ [SemanticCache] Hit! Found cached result for {agent_id}")
                return json.loads(data)
        except Exception as e:
            logger.debug(f"[SemanticCache] Get failed: {e}")
        return None

    async def set_cached_result(self, agent_id: str, payload: dict[str, object] | list[object] | str, result: dict[str, object]):
        """Lưu kết quả vào cache."""
        if not xohi_memory._use_redis:
            return
            
        key = self._generate_key(agent_id, payload)
        try:
            await xohi_memory.client.set(
                key, 
                json.dumps(result, ensure_ascii=False), 
                ex=self.ttl
            )
            logger.debug(f"📥 [SemanticCache] Result cached for {agent_id}")
        except Exception as e:
            logger.debug(f"[SemanticCache] Set failed: {e}")

semantic_cache = SemanticCacheService()
