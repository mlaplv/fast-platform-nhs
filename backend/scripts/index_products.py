import asyncio
import os
import sys
import logging
import uuid
import numpy as np
from sqlalchemy import select, text
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.database.alchemy_config import alchemy_config
from backend.database.models import ProductBase, ProductEmbedding
from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder, warmup_encoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("product-indexer")

BATCH_SIZE = 50

async def index_products():
    """
    Phase 77.2: Deep Memory Indexer.
    Scans all products and generates Hex-encoded embeddings for RAG.
    Optimized for 2GB RAM VPS with batching.
    """
    print("🚀 Starting Product Deep Memory Indexing...")

    # 1. Warmup Encoder
    await warmup_encoder()
    encoder = get_shared_encoder()
    if not encoder:
        logger.error("❌ Failed to load encoder. Aborting.")
        return

    session_maker = alchemy_config.create_session_maker()

    async with session_maker() as session:
        # 2. Count products needing indexing
        # We look for products without an embedding OR we can just re-index all to be safe for Phase 77.2
        count_stmt = select(ProductBase.id).where(ProductBase.deleted_at.is_(None))
        result = await session.execute(count_stmt)
        all_ids = result.scalars().all()
        total = len(all_ids)

        print(f"📦 Found {total} products to index.")

        loop = asyncio.get_running_loop()

        for i in tqdm(range(0, total, BATCH_SIZE)):
            batch_ids = all_ids[i:i+BATCH_SIZE]

            # Fetch batch data
            stmt = select(ProductBase).where(ProductBase.id.in_(batch_ids))
            res = await session.execute(stmt)
            products = res.scalars().all()

            texts_to_embed = []
            valid_products = []

            for p in products:
                content = f"{p.name} {p.description or ''}".strip()
                if content:
                    texts_to_embed.append(content)
                    valid_products.append(p)

            if not texts_to_embed:
                continue

            try:
                # Generate embeddings in batch
                embeddings = await loop.run_in_executor(None, lambda: list(encoder.embed(texts_to_embed)))

                for p, emb in zip(valid_products, embeddings):
                    vector_np = np.array(emb, dtype=np.float32)

                    # Phase 76.4: Pre-normalization for Zero-Allocation Dot Product
                    norm = np.linalg.norm(vector_np)
                    if norm > 0:
                        vector_np = vector_np / norm

                    vector_hex = vector_np.tobytes().hex()

                    # Upsert using raw SQL for speed and bypass ORM overhead
                    sql = text("""
                        INSERT INTO product_embeddings (id, product_base_id, embedding, created_at, updated_at)
                        VALUES (:id, :product_id, :vector, NOW(), NOW())
                        ON CONFLICT (product_base_id)
                        DO UPDATE SET embedding = :vector, updated_at = NOW();
                    """)
                    await session.execute(sql, {
                        "id": str(uuid.uuid4()),
                        "product_id": p.id,
                        "vector": vector_hex
                    })

                await session.commit()
            except Exception as e:
                logger.error(f"❌ Batch starting at {i} failed: {e}")
                await session.rollback()

    print("✨ Product Deep Memory Indexing complete!")

if __name__ == "__main__":
    asyncio.run(index_products())
