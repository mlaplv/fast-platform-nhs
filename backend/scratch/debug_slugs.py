import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

load_dotenv("/home/lv/Desktop/fast-platform-core/.env")
DATABASE_URL = os.getenv("DATABASE_URL").replace("db:5432", "localhost:5432").replace("postgresql://", "postgresql+asyncpg://", 1)

async def check():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        print("--- SLUG DEBUG ---")
        res = await conn.execute(text("SELECT id, name, slug, tenant_id FROM product_bases LIMIT 20;"))
        rows = res.all()
        for r in rows:
            print(f"ID: {r.id} | Tenant: {r.tenant_id} | Slug: {r.slug} | Name: {r.name[:30]}...")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
