import asyncio
import os
import sys
import logging
import uuid
import numpy as np
from sqlalchemy import select, text
from tqdm import tqdm
from dotenv import load_dotenv

# Add project root to path
ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(ROOT_DIR)

# Load environment variables from .env
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from backend.database.alchemy_config import alchemy_config
from backend.database.models import Article, ArticleEmbedding
from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder, warmup_encoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("article-indexer")

BATCH_SIZE = 50

async def index_articles():
    """
    Phase 77.2: Article Deep Memory Indexer.
    Scans all articles and generates Hex-encoded embeddings for RAG.
    """
    print("🚀 Starting Article Deep Memory Indexing...")

    # 1. Warmup Encoder
    await warmup_encoder()
    encoder = get_shared_encoder()
    if not encoder:
        logger.error("❌ Failed to load encoder. Aborting.")
        return

    session_maker = alchemy_config.create_session_maker()

    async with session_maker() as session:
        # 2. Count articles needing indexing
        count_stmt = select(Article.id).where(Article.deleted_at.is_(None))
        result = await session.execute(count_stmt)
        all_ids = result.scalars().all()
        total = len(all_ids)

        print(f"📄 Found {total} articles to index.")

        loop = asyncio.get_event_loop()

        for i in tqdm(range(0, total, BATCH_SIZE)):
            batch_ids = all_ids[i:i+BATCH_SIZE]

            # Fetch batch data
            stmt = select(Article).where(Article.id.in_(batch_ids))
            res = await session.execute(stmt)
            articles = res.scalars().all()

            texts_to_embed = []
            valid_articles = []

            for a in articles:
                # Combine title and content for better semantic retrieval
                content = f"{a.title} {a.excerpt or ''} {a.content or ''}".strip()
                if content:
                    # Limit content length to avoid embedding overhead if needed,
                    # but paraphrase-multilingual handles up to 128 tokens well.
                    texts_to_embed.append(content[:1000])
                    valid_articles.append(a)

            if not texts_to_embed:
                continue

            try:
                # Generate embeddings in batch
                embeddings = await loop.run_in_executor(None, lambda: list(encoder.embed(texts_to_embed)))

                for a, emb in zip(valid_articles, embeddings):
                    vector_np = np.array(emb, dtype=np.float32)

                    # Phase 76.4: Pre-normalization for Zero-Allocation Dot Product
                    norm = np.linalg.norm(vector_np)
                    if norm > 0:
                        vector_np = vector_np / norm

                    vector_hex = vector_np.tobytes().hex()

                    # Upsert using raw SQL
                    sql = text("""
                        INSERT INTO article_embeddings (id, article_id, embedding, created_at, updated_at)
                        VALUES (:id, :article_id, :vector, NOW(), NOW())
                        ON CONFLICT (article_id)
                        DO UPDATE SET embedding = :vector, updated_at = NOW();
                    """)
                    await session.execute(sql, {
                        "id": str(uuid.uuid4()),
                        "article_id": a.id,
                        "vector": vector_hex
                    })

                await session.commit()
            except Exception as e:
                logger.error(f"❌ Batch starting at {i} failed: {e}")
                await session.rollback()

    print("✨ Article Deep Memory Indexing complete!")

if __name__ == "__main__":
    asyncio.run(index_articles())
