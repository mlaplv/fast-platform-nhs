import asyncio
import os
import sys
import logging

# Add workspace to path
sys.path.append("/home/lv/Desktop/fast-platform-core")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")

from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop
from backend.database.models import ContentCampaign

async def test():
    await trinity_bridge.initialize()
    
    cop = PlagiarismCop()
    
    # Mock campaign
    campaign = ContentCampaign(
        id="test-adhoc",
        draft_content="Kem chống nắng giúp bảo vệ da khỏi tia UV. Tuy nhiên, nếu dùng không đúng cách sẽ gây sạm da. Hãy bôi kem chống nắng trước khi ra ngoài 20 phút.",
        gold_metadata={
            "primary_keyword": "cách dùng kem chống nắng"
        }
    )
    
    print("--- STARTING ANALYSIS ---")
    # Force re-analysis
    result = await cop.analyze(campaign, force=True)
    
    print("\n--- RESULT ---")
    print(f"Uniqueness Score: {result.uniqueness_score}")
    print(f"Risk Level: {result.risk_level}")
    print(f"Annotations count: {len(result.annotations)}")
    for i, a in enumerate(result.annotations):
        print(f"Annotation {i+1}: [{a.type}] '{a.text[:50]}...' -> {a.message if hasattr(a, 'message') else a.reason}")
    
    print("\n--- DONE ---")

if __name__ == "__main__":
    asyncio.run(test())
