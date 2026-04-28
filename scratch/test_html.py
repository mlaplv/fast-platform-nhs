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
    await trinity_bridge.initialize()
    
    cop = PlagiarismCop()
    
    # HTML content
    draft_content = """
<p><strong>Miccosmo Beppin Body Virgin White Serum</strong> là tinh chất dưỡng trắng da toàn thân, đặc biệt cho các vùng da nhạy cảm như nách, bẹn, khuỷu tay.</p>
<p>Sản phẩm chứa chiết xuất nhau thai (Placenta) nồng độ cao, giúp ức chế sản sinh melanin, làm mờ thâm nám và dưỡng da trắng mịn tự nhiên.</p>
"""
    
    # Mock campaign
    campaign = ContentCampaign(
        id="test-adhoc",
        draft_content=draft_content,
        gold_metadata={
            "primary_keyword": "Miccosmo Beppin Body Virgin White Serum"
        }
    )
    
    print("--- STARTING ANALYSIS (HTML) ---")
    # Force use of gemini-2.5-pro
    result = await cop.analyze(campaign, force=True)
    
    print("\n--- RESULT ---")
    print(f"Annotations count: {len(result.annotations)}")
    
    for i, a in enumerate(result.annotations):
        print(f"\nAnnotation {i+1}:")
        print(f"  Text: '{a.text}'")
        
        # Check if text is exactly in draft
        if a.text in draft_content:
            print("  MATCH: EXACT ✅")
        else:
            print("  MATCH: FAILED ❌ (Not found in draft)")
            # Try to see if it's a normalized match
            import re
            clean_a = re.sub(r'<[^>]+>', '', a.text)
            clean_d = re.sub(r'<[^>]+>', '', draft_content)
            if clean_a in clean_d:
                print("  MATCH: NORMALIZED ✅ (Tags were removed by AI)")
            else:
                print("  MATCH: ABSOLUTELY FAILED ❌")
    
    print("\n--- DONE ---")

if __name__ == "__main__":
    asyncio.run(test())
