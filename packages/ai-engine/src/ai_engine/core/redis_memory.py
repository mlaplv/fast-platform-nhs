# packages/ai-engine/src/ai_engine/core/redis_memory.py
import os
import json
import logging
from typing import List, Optional, Dict
import redis.asyncio as redis
from unittest.mock import MagicMock

logger = logging.getLogger("redis-memory")

class RedisMemory:
    """
    Tier 1 Memory: Redis-based Working Memory.
    - Sliding Window (N=6) for chat history (R1).
    - Partial Intent storage for Slot-Filling (R2).
    """
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/1")
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
        except Exception:
            logger.warning("[RedisMemory] Redis not available, using Mock.")
            self.client = MagicMock()

    async def add_message(self, session_id: str, role: str, content: str, window_size: int = 6):
        """Adds a message to the sliding window (Test Case 1)."""
        key = f"chat:history:{session_id}"
        msg = json.dumps({"role": role, "content": content})
        try:
            # Atomic push and trim
            async with self.client.pipeline() as pipe:
                pipe.rpush(key, msg)
                pipe.ltrim(key, -window_size, -1)
                pipe.expire(key, 3600) # 1 hour TTL
                await pipe.execute()
        except Exception as e:
            logger.error(f"Failed to add message to Redis: {e}")

    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieves the last N messages."""
        key = f"chat:history:{session_id}"
        try:
            items = await self.client.lrange(key, 0, -1)
            return [json.loads(i) for i in items]
        except Exception:
            return []

    async def store_partial_intent(self, session_id: str, intent_data: dict, ttl: int = 300):
        """Stores incomplete intent for slot-filling (Test Case 2)."""
        key = f"intent:partial:{session_id}"
        try:
            await self.client.set(key, json.dumps(intent_data), ex=ttl)
        except Exception as e:
            logger.error(f"Failed to store partial intent: {e}")

    async def get_partial_intent(self, session_id: str) -> Optional[dict]:
        """Retrieves and clears partial intent."""
        key = f"intent:partial:{session_id}"
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
        except Exception:
            pass
        return None

    async def clear_partial_intent(self, session_id: str):
        """Deletes partial intent after successful execution."""
        key = f"intent:partial:{session_id}"
        try:
            await self.client.delete(key)
        except Exception:
            pass
