import asyncio
import json
from backend.database.alchemy_config import alchemy_config
from sqlalchemy import select
from backend.database.models import ProductBase

async def main():
    async with alchemy_config.create_session_maker()() as s:
        res = await s.execute(select(ProductBase).where(ProductBase.name.ilike('%Miccosmo%')))
        products = res.scalars().all()
        for p in products:
            if p.market_data:
                print(f"--- Product: {p.name} ---")
                print(json.dumps(p.market_data, ensure_ascii=False, indent=2))

asyncio.run(main())
