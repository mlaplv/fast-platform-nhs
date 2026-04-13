import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

load_dotenv("/home/lv/Desktop/fast-platform-core/.env")
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
if "db:5432" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("db:5432", "localhost:5432")

async def fix():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        # Standardize tenant_id to 'smartshop' for all products (already done but good to be sure)
        await conn.execute(text("UPDATE product_bases SET tenant_id = 'smartshop' WHERE tenant_id IS NULL OR tenant_id = 'default';"))
        print("Data standardized.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix())
