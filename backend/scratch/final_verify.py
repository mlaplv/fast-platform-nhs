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

async def verify():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        print("--- DB Verification ---")
        res = await conn.execute(text("SELECT tenant_id, count(*) FROM product_bases GROUP BY tenant_id;"))
        print(f"Tenant Distribution: {res.all()}")
        
        res = await conn.execute(text("SELECT count(*) FROM product_bases WHERE stock <= 0;"))
        out_of_stock = res.scalar()
        print(f"Products with stock <= 0: {out_of_stock}")
        
    from backend.database import current_tenant_id
    from backend.services.commerce.product import ProductService
    from backend.services.commerce.product_vector import ProductVectorService
    
    ps = ProductService()
    pvs = ProductVectorService()
    
    # Mock context
    current_tenant_id.set("micsmo.com")
    
    print("\n--- Service Verification (Search 'mic') ---")
    async with engine.connect() as conn:
        # 1. ProductService.list_products
        results = await ps.list_products(conn, search="mic", status="ACTIVE")
        print(f"ProductService Results: {len(results.data)}")
        for i, p in enumerate(results.data):
            print(f"  {i+1}. {p.name} (Stock: {p.stock})")
            if p.stock <= 0:
                print("  ERROR: Out of stock product found in results!")
                
        # 2. ProductVectorService.search_semantic
        v_results = await pvs.search_semantic(conn, "mic")
        print(f"Semantic Results: {len(v_results)}")
        for i, p in enumerate(v_results):
            print(f"  {i+1}. {p['name']} (Stock: {p['stock']})")
            if p['stock'] <= 0:
                print("  ERROR: Out of stock product found in semantic results!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify())
