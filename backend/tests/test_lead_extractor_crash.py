import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from backend.database import alchemy_config
from backend.services.commerce.logic.lead_extractor import lead_extractor

async def run():
    maker = alchemy_config.create_session_maker()
    async with maker() as db:
        res = await lead_extractor.extract_and_convert(
            db,
            message="cho 1 miccosmo white label premium placenta wash 110g",
            session_id="test_sim_crash",
            current_product_slug="miccosmo-wash"
        )
        print("RESULT:")
        print(res)

asyncio.run(run())
