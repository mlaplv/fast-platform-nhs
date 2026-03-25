import asyncio
import os
import logging
import sys
from unittest.mock import MagicMock, patch, AsyncMock
from dotenv import load_dotenv

# Thêm root dự án vào sys.path
PROJECT_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

# Load .env manually trước khi import bất kỳ module backend nào
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# Mock Redis properly for async await to bypass "redis:6379" issues on host
mock_redis = AsyncMock()
mock_redis.exists.return_value = False 
mock_redis.get.return_value = None
patch('redis.asyncio.from_url', return_value=mock_redis).start()
patch('redis.from_url', return_value=mock_redis).start()

# Mock AI & Search BEFORE imports
from backend.services.xohi.creative_studio.models.schemas import ScoutReport, ScoutHeadline

topic_placeholder = "placeholder"
mock_report = ScoutReport(
    topic=topic_placeholder,
    headlines=[ScoutHeadline(title="Mock Title", type="ADS")],
    semantic_keywords=["mock", "keywords"],
    strategic_analysis="## Mock Analysis",
    ground_truth_summary="Mock OK"
)

# Mock trinity_bridge.run
patch('backend.services.ai_engine.core.trinity_bridge.trinity_bridge.run', 
      new_callable=AsyncMock, 
      return_value=MagicMock(data=mock_report)).start()

# Mock DiscoveryHunter.search
patch('backend.services.xohi.creative_studio.operatives.discovery_hunter.DiscoveryHunter.search',
      new_callable=AsyncMock,
      return_value="Mock Search Context").start()

from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.database.alchemy_config import alchemy_config
from backend.database.models import ContentScout
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-elite")

async def test_scout_cache():
    topic = f"elite_test_topic_{os.urandom(4).hex()}"
    logger.info(f"🚀 [INIT] Bắt đầu kiểm thử Neural Scout Elite (Isolated) cho chủ đề: {topic}")
    
    # Update mock to use the real topic
    mock_report.topic = topic
    
    # 1. Run First Scout (Cache Miss)
    logger.info("--- [Phase 1] Lần Trinh sát đầu tiên (Cache Miss) ---")
    try:
        res1 = await content_factory.analyst.scout(topic)
    except Exception as e:
        logger.error(f"❌ Phase 1 Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    if res1.status != "success":
        logger.error(f"❌ Phase 1 Thất bại: {res1.message}")
        return

    logger.info("✅ Phase 1 Hoàn tất (Real AI/Search Mocked).")
    
    # 2. Check Database Persistence
    logger.info("--- [Phase 2] Kiểm tra Database Persistence ---")
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        stmt = select(ContentScout).where(ContentScout.topic == topic)
        db_res = await session.execute(stmt)
        scout_obj = db_res.scalar_one_or_none()
        if scout_obj:
            logger.info(f"✅ Tìm thấy dữ liệu DB: {scout_obj.topic}")
        else:
            logger.error("❌ Không tìm thấy dữ liệu trong DB!")
            return

    # 3. Run Second Scout (Cache Hit)
    logger.info("--- [Phase 3] Lần Trinh sát thứ hai (Cache Hit) ---")
    res2 = await content_factory.analyst.scout(topic)
    
    cache_hit = False
    for log in res2.data.get("logs", []):
        if "[CACHE HIT]" in log:
            cache_hit = True
            logger.info(f"Log: {log}")
            
    if cache_hit:
        logger.info("✅ Phase 3 [CACHE HIT] Hoàn tất.")
    else:
        logger.error("❌ Phase 3 Thất bại: Không sử dụng Cache!")
        return

    logger.info("🔥🔥 [ELITE V62.2] PERSISTENCE ENGINE ĐÃ CHUẨN CHỈ! 🔥🔥")

if __name__ == "__main__":
    asyncio.run(test_scout_cache())
