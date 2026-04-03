import asyncio
import json
from sqlalchemy import select
from backend.database import alchemy_config
from backend.database.models import ProductBase

async def check():
    m = alchemy_config.create_session_maker()
    async with m() as s:
        p = await s.get(ProductBase, 'prod_hoi_nach_hong_son')
        print(f"RAW IMAGES: {p.images}")
        print(f"RAW MOBILE: {p.mobile_images}")
        print(f"RAW TIER: {json.dumps(p.tier_variations, indent=2)}")
        print(f"RAW DESC: {p.description}")

if __name__ == "__main__":
    import os
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"
    asyncio.run(check())
