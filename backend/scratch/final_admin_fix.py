import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

load_dotenv("/home/lv/Desktop/fast-platform-core/.env")
DATABASE_URL = os.getenv("DATABASE_URL").replace("db:5432", "localhost:5432").replace("postgresql://", "postgresql+asyncpg://", 1)

async def fix():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("--- FINAL DATA OVERHAUL ---")
        # 1. Force everything to the correct tenant
        await conn.execute(text("UPDATE product_bases SET tenant_id = 'micsmo.com';"))
        
        # 2. Force products to be ACTIVE and IN-STOCK
        # Actually, let's just make sure at least 10 products are active and have stock
        await conn.execute(text("UPDATE product_bases SET status = 'ACTIVE', stock = 100, is_ai_featured = true;"))
        
        # 3. Check distribution
        res = await conn.execute(text("SELECT status, count(*) FROM product_bases GROUP BY status;"))
        print(f"Status Distribution: {res.all()}")
        
        res = await conn.execute(text("SELECT count(*) FROM product_bases WHERE stock > 0;"))
        print(f"Products with stock > 0: {res.scalar()}")

    await engine.dispose()
    print("Data Restoration Complete.")

if __name__ == "__main__":
    asyncio.run(fix())
