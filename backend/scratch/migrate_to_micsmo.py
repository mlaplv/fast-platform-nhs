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

async def migrate():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("Migrating tenant_id from 'smartshop' to 'micsmo.com'...")
        # 1. Update product_bases
        res = await conn.execute(text("UPDATE product_bases SET tenant_id = 'micsmo.com' WHERE tenant_id = 'smartshop';"))
        print(f"Updated {res.rowcount} products.")
        
        # 2. Update any other tables if necessary (e.g. categories, articles)
        tables = ["categories", "articles", "news_articles", "reviews", "orders"]
        for table in tables:
            try:
                res = await conn.execute(text(f"UPDATE {table} SET tenant_id = 'micsmo.com' WHERE tenant_id = 'smartshop';"))
                print(f"Updated {res.rowcount} records in {table}.")
            except Exception as e:
                # Some tables might not have tenant_id or exist yet
                pass
                
        print("Migration completed.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
