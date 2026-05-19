import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

db_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"
engine = create_async_engine(db_url)

async def dump_metadata():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, name, product_metadata FROM product_bases WHERE deleted_at IS NULL"))
        rows = res.fetchall()
        for r in rows:
            meta = r[2] or {}
            print(f"ID: {r[0]} | Name: {r[1]}")
            print(f"  product_metadata: {json.dumps(meta, indent=2, ensure_ascii=False)}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(dump_metadata())
