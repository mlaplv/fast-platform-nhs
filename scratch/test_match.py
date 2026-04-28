import asyncio
import os
import sys
import logging
# Add workspace to path
sys.path.append("/app")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")

from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop
from backend.database.models import ContentCampaign

async def test():
    # Force initialization to pick up new models
    await trinity_bridge.initialize()
    
    cop = PlagiarismCop()
    
    # Text from a real source to trigger plagiarism
    draft_content = """
Miccosmo Beppin Body Virgin White Serum là tinh chất dưỡng trắng da toàn thân, đặc biệt cho các vùng da nhạy cảm như nách, bẹn, khuỷu tay. 
Sản phẩm chứa chiết xuất nhau thai (Placenta) nồng độ cao, giúp ức chế sản sinh melanin, làm mờ thâm nám và dưỡng da trắng mịn tự nhiên.
Ngoài ra, tinh chất còn chứa các thành phần dưỡng ẩm như tinh chất lô hội và lá dâu tằm, giúp da luôn mềm mại, không gây kích ứng.
"""
    
    # Mock campaign
    campaign = ContentCampaign(
        id="test-adhoc",
        draft_content=draft_content,
        gold_metadata={
            "primary_keyword": "Miccosmo Beppin Body Virgin White Serum"
        }
    )
    
    print("--- STARTING ANALYSIS ---")
    # Force re-analysis with the new model
    result = await cop.analyze(campaign, force=True)
    
    print("\n--- RESULT ---")
    print(f"Uniqueness Score: {result.uniqueness_score}")
    print(f"Risk Level: {result.risk_level}")
    print(f"Annotations count: {len(result.annotations)}")
    
    for i, a in enumerate(result.annotations):
        print(f"\nAnnotation {i+1}:")
        print(f"  Type: {a.type}")
        print(f"  Text (len={len(a.text)}): '{a.text}'")
        print(f"  Reason: {a.reason}")
        
        # Check if text is exactly in draft
        if a.text in draft_content:
            print("  MATCH: EXACT ✅")
        else:
            print("  MATCH: FAILED ❌ (Not found in draft)")
    
    print("\n--- DONE ---")

if __name__ == "__main__":
    asyncio.run(test())
