import json
import logging
from datetime import UTC, datetime
from typing import Dict, Optional

from redis.asyncio import Redis

logger = logging.getLogger("fast_platform.streams")

class RedisStreamProducer:
    """
    Xử lý việc đẩy các sự kiện vào Redis Streams (Fast Path).
    MAXLEN được thiết lập để bảo vệ RAM 4GB (tự động dọn dẹp).
    """
    
    def __init__(self, redis_client: Redis, stream_name: str = "ads:protection:clicks"):
        self.redis = redis_client
        self.stream_name = stream_name
        self.max_len = 10000 # Giữ 10k bản ghi mới nhất (~1-2MB RAM)

    async def produce(self, data: Dict[str, object], event_type: str = "CLICK") -> Optional[str]:
        """
        Đẩy event vào stream.
        """
        try:
            payload = {
                "event_type": event_type,
                "timestamp": datetime.now(UTC).isoformat(),
                "data": json.dumps(data)
            }
            
            # XADD key [MAXLEN [~] count] ID field value [field value ...]
            entry_id = await self.redis.xadd(
                name=self.stream_name,
                fields=payload,
                maxlen=self.max_len,
                approximate=True
            )
            
            logger.debug(f"STREAM_PRODUCE: {self.stream_name} id={entry_id}")
            return entry_id
        except Exception as e:
            logger.error(f"STREAM_PRODUCE_ERROR: {e}")
            return None

class RedisStreamConsumer:
    """
    Base class cho các Worker tiêu thụ event từ stream (Slow Path).
    Dùng Consumer Groups để đảm bảo không mất event.
    """
    def __init__(self, redis_client: Redis, stream_name: str, group_name: str, consumer_name: str):
        self.redis = redis_client
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = consumer_name

    async def setup_group(self):
        """Khởi tạo Consumer Group nếu chưa tồn tại."""
        try:
            await self.redis.xgroup_create(self.stream_name, self.group_name, id="0", mkstream=True)
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                logger.error(f"XGROUP_CREATE_ERROR: {e}")

    async def consume(self, count: int = 10, block_ms: int = 2000):
        """Đọc event từ group."""
        try:
            # XREADGROUP GROUP group consumer [COUNT count] [BLOCK milliseconds] STREAMS key [key ...] ID [ID ...]
            entries = await self.redis.xreadgroup(
                groupname=self.group_name,
                consumername=self.consumer_name,
                streams={self.stream_name: ">"},
                count=count,
                block=block_ms
            )
            return entries
        except Exception as e:
            logger.error(f"XREADGROUP_ERROR: {e}")
            return []
