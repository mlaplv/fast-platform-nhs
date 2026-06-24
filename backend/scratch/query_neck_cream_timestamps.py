#!/usr/bin/env python3
import asyncio
import sys
from sqlalchemy import select

# Add parent directory to path
sys.path.append("/media/lv/data/fast-platform-core")

from backend.database.alchemy_config import alchemy_config
from backend.database.models import ProductBase

async def query_db():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        stmt = select(ProductBase).where(ProductBase.slug == "miccosmo-hurry-harry-premium-neck-cream-rich-40gr-kem-duong-sang-co")
        res = await session.execute(stmt)
        prod = res.scalars().first()
        if not prod:
            print("Product not found!")
            return
        
        print("Product ID:", prod.id)
        print("Product Name:", prod.name)
        print("created_at:", prod.created_at)
        print("updated_at:", prod.updated_at)
        
        # If updated_at is None, let's update it to created_at or current timestamp to have a value
        if prod.updated_at is None:
            print("updated_at is NULL in database! Updating to created_at...")
            prod.updated_at = prod.created_at
            await session.commit()
            print("updated_at updated successfully in DB to:", prod.updated_at)

if __name__ == "__main__":
    asyncio.run(query_db())
