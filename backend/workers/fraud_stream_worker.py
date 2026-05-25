import asyncio
import json
import logging
import os
import signal
from datetime import UTC, datetime
from typing import Dict, List, Tuple, Union, cast

from sqlalchemy import update
from backend.database.alchemy_config import alchemy_config
from backend.database.models.ads import ClickFraudEvent
from backend.services.xohi_memory import xohi_memory
from backend.core.stream_handler import RedisStreamConsumer
from backend.agents.fraud_investigator import run_forensic_analysis
from backend.services.ads_protection.ip_intelligence_service import IPIntelligenceService
from backend.controllers.ads_protection import _hub

logger = logging.getLogger("fraud-worker")

class FraudStreamWorker:
    """
    [ELITE V2.2] High-Performance Agentic Stream Consumer for Ads Protection Click Telemetry.
    Implements concurrent processing and strict memory safeguards to support 2GB VPS constraints.
    """
    
    def __init__(self) -> None:
        self.consumer = RedisStreamConsumer(
            redis_client=xohi_memory.client,
            stream_name="ads:protection:clicks",
            group_name="agentic_investigators",
            consumer_name="worker_1"
        )
        self.ip_svc = IPIntelligenceService()
        self.running: bool = True

    async def start(self) -> None:
        """
        Kích hoạt luồng tiêu thụ song song (High-Throughput Concurrent Loop).
        """
        logger.info("🚀 [FraudWorker] Starting Agentic Stream Consumer (V3.0 Concurrent Mode)...")
        await self.consumer.setup_group()
        
        while self.running:
            try:
                # Đọc event từ stream (block tối đa 2s nếu không có dữ liệu)
                entries = await self.consumer.consume(count=5, block_ms=2000)
                
                tasks: List[asyncio.Task[None]] = []
                for stream, messages in entries:
                    for msg_id, payload in messages:
                        # Chạy xử lý song song thông qua Task list để tối ưu I/O throughput
                        t = asyncio.create_task(self.handle_msg_with_ack(msg_id, payload))
                        tasks.append(t)
                
                if tasks:
                    await asyncio.gather(*tasks)
                    
            except Exception as e:
                logger.error(f"❌ [FraudWorker] Loop execution error: {e}")
                await asyncio.sleep(5)

    async def handle_msg_with_ack(self, msg_id: Union[bytes, str], payload: Dict[Union[bytes, str], Union[bytes, str]]) -> None:
        """
        Hàm bao gói xử lý song song kèm Acknowledge (XACK) đảm bảo an toàn sự kiện.
        """
        msg_str = msg_id.decode("utf-8") if isinstance(msg_id, bytes) else msg_id
        try:
            await self.process_event(msg_str, payload)
        except Exception as e:
            logger.error(f"❌ [FraudWorker] Message processing failed for {msg_str}: {e}")
        finally:
            # Luôn XACK để giải phóng RAM trong Redis Stream
            stream_name = "ads:protection:clicks"
            group_name = "agentic_investigators"
            await xohi_memory.client.xack(stream_name, group_name, msg_str)

    async def process_event(self, msg_id: str, payload: Dict[Union[bytes, str], Union[bytes, str]]) -> None:
        """
        Xử lý nghiệp vụ click và thẩm định Agentic forensic.
        """
        # Hỗ trợ giải mã an toàn cả hai định dạng Redis (Bytes/String)
        data_bytes = payload.get("data") or payload.get(b"data")
        if not data_bytes:
            logger.warning(f"⚠️ [FraudWorker] Event payload contains empty data key: {payload}")
            return
            
        data_str = data_bytes.decode("utf-8") if isinstance(data_bytes, bytes) else cast(str, data_bytes)
        data: Dict[str, Union[str, float, int]] = json.loads(data_str)
        
        score: float = float(data.get("score", 0.0))
        verdict: str = str(data.get("verdict", "CLEAN"))
        ip: str = str(data.get("ip", ""))
        gclid: str = str(data.get("gclid", ""))
        
        if not ip or not gclid:
            logger.warning(f"⚠️ [FraudWorker] Skipping event {msg_id}: Missing critical key (ip={ip}, gclid={gclid})")
            return

        # [Elite V3.0] Chiến lược thẩm vấn Vùng xám (0.35 - 0.75)
        # Chỉ triệu hồi Agent suy nghĩ sâu khi điểm rơi vào vùng xám nghi vấn để tối ưu hóa chi phí & CPU
        if 0.35 <= score <= 0.75:
            logger.info(f"🕵️ [Agentic] Investigating Gray-Zone Click: IP={ip} Score={score:.4f}")
            
            async with alchemy_config.create_session_maker()() as db:
                agent_result = await run_forensic_analysis(db, self.ip_svc, data)
                
                if agent_result:
                    # Cập nhật lại kết luận điều tra vào DB
                    stmt = update(ClickFraudEvent).where(
                        ClickFraudEvent.gclid == gclid,
                        ClickFraudEvent.ip_address == ip
                    ).values(
                        verdict=agent_result.verdict,
                        fraud_score=agent_result.fraud_score,
                        reasoning=getattr(agent_result, 'reasoning', None),
                        updated_at=datetime.now(UTC)
                    )
                    await db.execute(stmt)
                    await db.commit()
                    
                    # Phát tín hiệu về Dashboard an ninh qua Server-Sent Events (SSE)
                    if agent_result.verdict == "FRAUD":
                        await _hub.broadcast({
                            "type": "NEW_CLICK",
                            "ip": ip,
                            "score": agent_result.fraud_score,
                            "verdict": agent_result.verdict,
                            "source": "AGENTIC_V3"
                        })
        else:
            logger.debug(f"⏭️ [FraudWorker] Skipping clear-cut click (Score: {score:.2f})")

    def stop(self) -> None:
        self.running = False


async def main() -> None:
    worker = FraudStreamWorker()
    
    # Đăng ký tắt ứng dụng an toàn (Graceful Shutdown)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, worker.stop)
        
    await worker.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
