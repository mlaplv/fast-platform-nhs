import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import json

async def check():
    db_url = os.environ.get('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@db:5432/fast_platform')
    engine = create_async_engine(db_url)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, name, product_metadata, order_count FROM product_bases"))
        rows = res.fetchall()
        for row in rows:
            print(f"ID: {row[0]}, NAME: {row[1]}, ORDER_COUNT: {row[3]}")
            print(f"PRODUCT_METADATA: {json.dumps(row[2], indent=2, ensure_ascii=False)}")
            print("-" * 50)
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
