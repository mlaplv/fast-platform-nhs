#!/usr/bin/env python3
import asyncio
import sys
import json
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

sys.path.append("/media/lv/data/fast-platform-core")

from backend.database.models import ProductBase

async def query_db():
    # Construct a local database URL using 127.0.0.1 instead of db container name
    local_db_url = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/fast_platform"
    engine = create_async_engine(local_db_url)
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
    
    async with session_maker() as session:
        stmt = select(ProductBase).where(ProductBase.slug.like("%beppin%"))
        res = await session.execute(stmt)
        products = res.scalars().all()
        if not products:
            print("No product containing 'beppin' found!")
            return
        
        for prod in products:
            print("Product ID:", prod.id)
            print("Product Name:", prod.name)
            print("Product Slug:", prod.slug)
            print("Metadata:")
            print(json.dumps(prod.product_metadata or {}, indent=2, ensure_ascii=False))
            print("-" * 50)
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(query_db())
