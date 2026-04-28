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
from backend.services.xohi.creative_studio.models.schemas import PlagiarismResult
from backend.database.models import ContentCampaign
from pydantic_ai import Agent

async def test():
    await trinity_bridge.initialize()
    
    # Force use of gemini-2.5-pro
    model_name = "gemini-2.5-pro"
    print(f"--- TESTING WITH MODEL: {model_name} ---")
    
    agent = Agent(output_type=PlagiarismResult)
    
    prompt = """
[BÀI VIẾT CỦA BẠN]:
Miccosmo Beppin Body Virgin White Serum là tinh chất dưỡng trắng da toàn thân, đặc biệt cho các vùng da nhạy cảm như nách, bẹn, khuỷu tay. 
Sản phẩm chứa chiết xuất nhau thai (Placenta) nồng độ cao, giúp ức chế sản sinh melanin, làm mờ thâm nám và dưỡng da trắng mịn tự nhiên.

[ĐỐI THỦ CẠNH TRANH]:
Miccosmo Beppin Body Virgin White Serum 30g is a Japanese whitening serum for the body. 
It contains high concentration of Placenta extract to inhibit melanin production and brighten skin.
"""
    
    system_prompt = "Bạn là Thẩm định viên Bản quyền. Hãy so sánh và tìm các đoạn trùng lặp."
    
    try:
        result = await trinity_bridge.run(
            agent=agent,
            prompt=prompt,
            system_prompt=system_prompt,
            model=model_name,
            force=True
        )
        
        print("\n--- RESULT ---")
        print(f"Type: {type(result).__name__}")
        print(f"Score: {getattr(result, 'uniqueness_score', 'N/A')}")
        print(f"Annotations count: {len(getattr(result, 'annotations', []))}")
        
        for i, a in enumerate(getattr(result, 'annotations', [])):
            print(f"  Annotation {i+1}: '{a.text}'")
            
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test())
