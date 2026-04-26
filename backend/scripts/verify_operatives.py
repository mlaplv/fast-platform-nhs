import asyncio
import logging
import sys
import os
from typing import Dict, List, Optional

# Add backend to path
sys.path.append(os.getcwd())

from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.services.xohi.creative_studio.handlers.analyst import AdHocContent

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-suite")

async def test_operatives():
    logger.info("🧪 [TEST] Bắt đầu kiểm tra hệ thống Operative Elite V2.2...")
    
    test_content = "Đây là một đoạn văn bản thử nghiệm về sản phẩm kem dưỡng da Beppin Body từ Nhật Bản. Sản phẩm giúp làm trắng da và mịn màng."
    test_topic = "Beppin Body Whitening"
    
    # 1. Test Copyright
    logger.info("🔍 [TEST 1] Kiểm tra Copyright (PlagiarismCop)...")
    res_copy = await content_factory.analyst.analyze_copyright(
        campaign_id=None,
        campaign_repo=None,
        force=True,
        raw_content=test_content,
        raw_topic=test_topic
    )
    logger.info(f"✅ Copyright Result: Score={res_copy.data.get('uniqueness_score')} | Risk={res_copy.data.get('risk_level')}")

    # 2. Test SEO
    logger.info("📈 [TEST 2] Kiểm tra SEO (SeoAnalyzer)...")
    res_seo = await content_factory.analyst.analyze_seo(
        campaign_id=None,
        campaign_repo=None,
        force=True,
        raw_content=test_content,
        raw_topic=test_topic
    )
    logger.info(f"✅ SEO Result: Score={res_seo.data.get('total_score')} | Grade={res_seo.data.get('grade')}")

    # 3. Test Inspector
    logger.info("🛡️ [TEST 3] Kiểm tra Inspector (AiInspector)...")
    res_insp = await content_factory.analyst.analyze_ai_ready(
        campaign_id=None,
        campaign_repo=None,
        force=True,
        raw_content=test_content,
        raw_topic=test_topic
    )
    logger.info(f"✅ Inspector Result: Score={res_insp.data.get('geo_score')} | Annotations={len(res_insp.data.get('annotations', []))}")

    # 4. Test Booster
    logger.info("🚀 [TEST 4] Kiểm tra Booster (SurgeonBooster)...")
    res_boost = await content_factory.analyst.surgeon_boost(
        raw_content=test_content,
        topic=test_topic
    )
    logger.info(f"✅ Booster Result: Patches={len(res_boost.data.get('patches', []))}")

    # 5. Test Neural Rewrite (Article)
    logger.info("🖋️ [TEST 5] Kiểm tra Neural Rewrite (Article)...")
    res_rewrite_art = await content_factory.analyst.neural_rewrite(
        content=test_content,
        topic=test_topic,
        feedback="Hãy viết lại cho viral hơn.",
        content_type="article"
    )
    logger.info(f"✅ Rewrite (Article) Result: Length={len(res_rewrite_art.data.get('new_content', ''))}")

    # 6. Test Neural Rewrite (Product)
    logger.info("🛍️ [TEST 6] Kiểm tra Neural Rewrite (Product)...")
    res_rewrite_prod = await content_factory.analyst.neural_rewrite(
        content=test_content,
        topic=test_topic,
        feedback="Tập trung vào thông số kỹ thuật.",
        content_type="product"
    )
    logger.info(f"✅ Rewrite (Product) Result: JSON={res_rewrite_prod.data.get('new_content')[:100]}...")

    logger.info("🏆 [DONE] Tất cả các Operative đã được xác minh thành công!")

if __name__ == "__main__":
    asyncio.run(test_operatives())
