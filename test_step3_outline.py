import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from backend.database.models import ContentCampaign
from backend.services.xohi.creative_studio.operatives.creative_pen import CreativePen
import uuid

async def main():
    pen = CreativePen()
    mock_campaign = ContentCampaign(
        id=str(uuid.uuid4()),
        status="PROCESSING",
        current_step=3,
        gold_metadata={
            "title": "Bí quyết chọn Máy Lọc Nước cho Gia Đình",
            "primary_keyword": "máy lọc nước gia đình",
            "secondary_keywords": ["nước sạch", "công nghệ RO", "bảo vệ sức khỏe"],
            "persona": "Chuyên gia gia dụng thân thiện, thấu hiểu"
        },
        assets_data=[
            "https://example.com/may-loc-nuoc-1.jpg",
            "https://example.com/may-loc-nuoc-2.jpg"
        ]
    )
    
    print("Testing CreativePen (Step 3 - Outline)...")
    try:
        outline = await pen.generate_outline(mock_campaign)
        print("\n--- RESULTS ---")
        for idx, section in enumerate(outline.sections):
            print(f"[{idx+1}] {section['heading']}")
            print(f"    {section['content']}")
            print("-" * 20)
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
