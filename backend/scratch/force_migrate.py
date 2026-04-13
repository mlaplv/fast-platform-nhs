import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

load_dotenv("/home/lv/Desktop/fast-platform-core/.env")
DATABASE_URL = os.getenv("DATABASE_URL").replace("db:5432", "localhost:5432").replace("postgresql://", "postgresql+asyncpg://", 1)

async def main():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("FORCE MIGRATE: smartshop -> micsmo.com")
        await conn.execute(text("UPDATE product_bases SET tenant_id = 'micsmo.com';"))
        await conn.execute(text("UPDATE categories SET tenant_id = 'micsmo.com';"))
        await conn.execute(text("UPDATE articles SET tenant_id = 'micsmo.com';"))
        
        res = await conn.execute(text("SELECT tenant_id, count(*) FROM product_bases GROUP BY tenant_id;"))
        print(f"NEW distribution: {res.all()}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
