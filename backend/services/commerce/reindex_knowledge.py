import asyncio
import logging
import sys
import os
from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Setup path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.database.models.system import SupportKnowledge
from backend.services.commerce.knowledge_vector import knowledge_vector_service
from backend.services.ai_engine.core.encoder_singleton import warmup_encoder
from backend.utils.uid import new_id

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
    
    model = knowledge_vector_service.encoder
    if not model:
        logger.error("❌ Model not available after warmup. Exiting.")
        return

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
        
        # 3. Batch processing (Elite Resource Discipline)
        BATCH_SIZE = 100
        count = 0
        items_list = list(items)
        
        for batch_start in range(0, len(items_list), BATCH_SIZE):
            batch = items_list[batch_start : batch_start + BATCH_SIZE]
            batch_contents = [f"{item.question} {item.answer}" for item in batch]
            
            logger.info(f"🧬 Batch encoding {len(batch_contents)} items...")
            loop = asyncio.get_running_loop()
            vectors_iter = await loop.run_in_executor(None, lambda: list(model.embed(batch_contents)))
            vectors = list(vectors_iter)
            
            logger.info(f"💾 Upserting pre-computed vectors to Postgres...")
            for i, item in enumerate(batch):
                if i >= len(vectors):
                    break
                vector_str = f"[{','.join(map(str, vectors[i]))}]"
                sql = text("""
                    INSERT INTO support_knowledge_embeddings (id, knowledge_id, embedding, created_at, updated_at, tenant_id)
                    VALUES (:id, :kid, CAST(:v AS vector), NOW(), NOW(), :tid)
                    ON CONFLICT (knowledge_id)
                    DO UPDATE SET embedding = CAST(:v AS vector), updated_at = NOW(), tenant_id = :tid;
                """)
                await db.execute(sql, {"id": new_id(), "kid": item.id, "v": vector_str, "tid": item.tenant_id or "default"})
                count += 1
            
            await db.commit()
            logger.info(f"✨ Committed batch. Processed {count}/{len(items_list)} items.")
            
        logger.info(f"✅ Re-indexing completed. {count}/{len(items_list)} items successfully indexed.")

if __name__ == "__main__":
    asyncio.run(reindex_all())
