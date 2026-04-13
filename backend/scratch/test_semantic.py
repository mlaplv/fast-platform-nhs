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
    from backend.services.commerce.product_vector import ProductVectorService
    service = ProductVectorService()
    
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        print("Testing Semantic Search for 'mic' with tenant 'smartshop'...")
        results = await service.search_semantic(conn, "mic", tenant_id="smartshop")
        print(f"Results: {len(results)}")
        for r in results:
            print(f"- {r['name']} (Score: {r['match_score']})")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test())
