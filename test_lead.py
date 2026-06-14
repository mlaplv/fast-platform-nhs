import asyncio
import logging
import sys
from backend.database import async_session_maker
from backend.services.commerce.logic.lead_extractor import LeadExtractor

logging.basicConfig(level=logging.INFO)

async def test():
    async with async_session_maker() as db:
        try:
            lead_data = await LeadExtractor.extract_and_convert(
                db=db,
                message="0949901122, 336/44 Nguyễn Văn Luông, Phú Lâm",
                session_id="test_session_123_new",
                current_product_slug=None,
                cart_text=""
            )
            print("LEAD DATA:", lead_data)
        except Exception as e:
            print("EXCEPTION CAUGHT:", e)
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
