import asyncio
import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.database.repositories import OrderRepository
from backend.services.data_injector import data_injector
from backend.database import current_tenant_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-revenue")

async def test_fetch():
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/fast_platform")
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Mock tenant ID if needed
        current_tenant_id.set("micsmo.com")
        
        repo = OrderRepository(session=session)
        logger.info("Fetching revenue series...")
        try:
            res = await data_injector._fetch_revenue_series(order_repo=repo)
            logger.info("RESULT SUCCESS")
            print(res)
        except Exception as e:
            logger.error(f"FETCH FAILED: {e}", exc_info=True)
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_fetch())
