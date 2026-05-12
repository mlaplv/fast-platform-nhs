import asyncio
import json
import logging
import os
import signal
from datetime import UTC, datetime

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
    def __init__(self):
        self.consumer = RedisStreamConsumer(
            redis_client=xohi_memory.client,
            stream_name="ads:protection:clicks",
            group_name="agentic_investigators",
            consumer_name="worker_1"
        )
        self.ip_svc = IPIntelligenceService()
        self.running = True

    async def start(self):
        logger.info("🚀 [FraudWorker] Starting Agentic Stream Consumer (V3.0)...")
        await self.consumer.setup_group()
        
        while self.running:
            try:
                # Đọc event từ stream (block 2s nếu không có data)
                entries = await self.consumer.consume(count=5, block_ms=2000)
                
                for stream, messages in entries:
                    for msg_id, payload in messages:
                        await self.process_event(msg_id, payload)
                        # Acknowledge sau khi xử lý xong
                        await xohi_memory.client.xack("ads:protection:clicks", "agentic_investigators", msg_id)
            except Exception as e:
                logger.error(f"WORKER_LOOP_ERROR: {e}")
                await asyncio.sleep(5)

    async def process_event(self, msg_id, payload):
        data = json.loads(payload.get("data", "{}"))
        score = float(data.get("score", 0))
        verdict = data.get("verdict", "CLEAN")
        
        # [Elite V3.0] Chiến lược thẩm vấn Vùng xám (0.4 - 0.7)
        # Nếu điểm quá thấp hoặc quá cao, Fast Path đã xử lý xong.
        # Chúng ta chỉ gọi Agent cho những ca cần "suy nghĩ" sâu.
        if 0.35 <= score <= 0.75:
            logger.info(f"🕵️ [Agentic] Investigating Gray-Zone Click: IP={data.get('ip')} Score={score}")
            
            async with alchemy_config.create_session_maker()() as db:
                agent_result = await run_forensic_analysis(db, self.ip_svc, data)
                
                if agent_result:
                    # Cập nhật lại bản án vào DB
                    stmt = update(ClickFraudEvent).where(
                        ClickFraudEvent.gclid == data.get('gclid'),
                        ClickFraudEvent.ip_address == data.get('ip')
                    ).values(
                        verdict=agent_result.verdict,
                        fraud_score=agent_result.fraud_score,
                        reasoning=getattr(agent_result, 'reasoning', None), # Giả sử Agent trả về reasoning
                        updated_at=datetime.now(UTC)
                    )
                    await db.execute(stmt)
                    await db.commit()
                    
                    # Phát tín hiệu về Dashboard qua SSE
                    if agent_result.verdict == "FRAUD":
                        await _hub.broadcast({
                            "type": "NEW_CLICK",
                            "ip": data.get('ip'),
                            "score": agent_result.fraud_score,
                            "verdict": agent_result.verdict,
                            "source": "AGENTIC_V3"
                        })
        else:
            logger.debug(f"⏭️ [FraudWorker] Skipping clear-cut click (Score: {score})")

    def stop(self):
        self.running = False

async def main():
    worker = FraudStreamWorker()
    
    # Handle shutdown signals
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, worker.stop)
        
    await worker.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
