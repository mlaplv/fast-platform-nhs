
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

async def check():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        print(f"{'ID':<25} | {'Status':<10} | {'Tenant':<10} | {'Vector':<6} | {'Name'}")
        print("-" * 100)
        res = await conn.execute(text("""
            SELECT p.id, p.status, p.tenant_id, p.name, (e.id IS NOT NULL) as has_embedding
            FROM product_bases p 
            LEFT JOIN product_embeddings e ON p.id = e.product_base_id
            ORDER BY p.status, p.name;
        """))
        for row in res:
            print(f"{row[0]:<25} | {row[1]:<10} | {row[2]:<10} | {str(row[4]):<6} | {row[3]}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
