import asyncio
import logging
import sys
import os
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Setup path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.database.models.system import SupportKnowledge
from backend.services.commerce.knowledge_vector import knowledge_vector_service
from backend.services.ai_engine.core.encoder_singleton import warmup_encoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reindex-surgical")

# Load environment from .env if possible
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/fast_platform")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def reindex_all():
    logger.info("🚀 Starting Surgical Knowledge Re-indexing...")
    
    # 1. Warmup Encoder
    logger.info("⏳ Initializing Trinity Encoder (FastEmbed)...")
    await warmup_encoder(max_retries=3)
    
    async with AsyncSessionLocal() as db:
        # 2. Fetch all active knowledge
        stmt = select(SupportKnowledge).where(
            and_(
                SupportKnowledge.deleted_at == None,
                SupportKnowledge.is_active == True
            )
        )
        result = await db.execute(stmt)
        items = result.scalars().all()
        
        logger.info(f"📦 Found {len(items)} knowledge items to re-index.")
        
        # 3. Upsert Embeddings
        count = 0
        for item in items:
            content = f"{item.question} {item.answer}"
            logger.info(f"  - Re-indexing [{item.id}]: {item.question[:50]}...")
            try:
                await knowledge_vector_service.upsert_embedding(db, item.id, content, tenant_id=item.tenant_id)
                count += 1
            except Exception as e:
                logger.error(f"  ❌ Failed for {item.id}: {e}")
        
        await db.commit()
        logger.info(f"✅ Re-indexing completed. {count}/{len(items)} items processed.")

if __name__ == "__main__":
    asyncio.run(reindex_all())
