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
        print("--- HOMEPAGE DATA STATUS ---")
        # 1. Check total products for micsmo.com
        res = await conn.execute(text("SELECT count(*) FROM product_bases WHERE tenant_id = 'micsmo.com'"))
        print(f"Total products (micsmo.com): {res.scalar()}")
        
        # 2. Check stock > 0
        res = await conn.execute(text("SELECT count(*) FROM product_bases WHERE tenant_id = 'micsmo.com' AND stock > 0"))
        active_stock = res.scalar()
        print(f"Products with stock > 0: {active_stock}")
        
        # 3. Check is_ai_featured
        res = await conn.execute(text("SELECT count(*) FROM product_bases WHERE tenant_id = 'micsmo.com' AND is_ai_featured = true"))
        featured = res.scalar()
        print(f"Featured products: {featured}")
        
        # 4. Check intersection (Featured & Active Stock)
        res = await conn.execute(text("SELECT id, name, stock, is_ai_featured, status FROM product_bases WHERE tenant_id = 'micsmo.com' AND is_ai_featured = true AND stock > 0 AND status = 'ACTIVE'"))
        rows = res.all()
        print(f"Intersection (Featured & Active & Stock>0): {len(rows)}")
        for r in rows:
            print(f"  - {r.name} (Stock: {r.stock}, Featured: {r.is_ai_featured})")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
