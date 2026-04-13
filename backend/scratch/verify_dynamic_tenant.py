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

async def test():
    from backend.database import current_tenant_id
    from backend.services.commerce.product_vector import ProductVectorService
    from backend.services.commerce.product import ProductService
    
    ps = ProductService()
    pvs = ProductVectorService()
    
    engine = create_async_engine(DATABASE_URL)
    
    # Test 1: No context (default fallback 'smartshop')
    print("--- Test 1: No context ---")
    async with engine.connect() as conn:
        results = await pvs.search_semantic(conn, "mic")
        print(f"Results (default): {len(results)}")
        
    # Test 2: Explicit 'smartshop' context
    print("\n--- Test 2: 'smartshop' context ---")
    token = current_tenant_id.set("smartshop")
    try:
        async with engine.connect() as conn:
            results = await pvs.search_semantic(conn, "mic")
            print(f"Results (smartshop): {len(results)}")
    finally:
        current_tenant_id.reset(token)

    # Test 3: 'other' context (should be empty)
    print("\n--- Test 3: 'other' context ---")
    token = current_tenant_id.set("non_existent_tenant")
    try:
        async with engine.connect() as conn:
            results = await pvs.search_semantic(conn, "mic")
            print(f"Results (non_existent): {len(results)}")
    finally:
        current_tenant_id.reset(token)
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test())
