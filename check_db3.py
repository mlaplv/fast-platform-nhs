import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import json

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform")
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        result = await session.execute(text("SELECT id, name, product_metadata FROM product_bases WHERE name ILIKE '%Beppin%';"))
        products = result.all()
        for p in products:
            p_id, name, meta = p
            print(f"Product: {name}")
            print(f"Metadata: {json.dumps(meta, ensure_ascii=False, indent=2)}")

asyncio.run(main())
