# apps/api-gateway/src/services/embedding_indexer.py
"""
Embedding Indexer — Auto-index products/articles into pgvector.
================================================================
Scans database for records without embeddings and creates them.
Uses content_hash to detect changes and re-embed when needed.

Usage:
    docker compose exec api python3 -c "
        from backend.services.embedding_indexer import EmbeddingIndexer
        import asyncio; asyncio.run(EmbeddingIndexer().run())
    "
"""
import hashlib
import logging
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("api-gateway")


class EmbeddingIndexer:
    """
    Batch + incremental embedding indexer for RAG.
    Uses fastembed (same model as SemanticRouter) for consistency.
    """

    def __init__(self):
        # V56.0: Use shared encoder singleton
        pass

    def _get_encoder(self):
        """Delegates to shared singleton (V56.0: merged 3 instances → 1)."""
        from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
        return get_shared_encoder()

    @staticmethod
    def _content_hash(text: str) -> str:
        """SHA256 hash of content to detect changes."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def run(self, session: AsyncSession):
        """
        Main entry: index all unembedded products and articles.
        """
        await self._index_products(session)
        await self._index_articles(session)

    async def _index_products(self, session):
        """Embed all products that don't have an embedding or whose content changed."""
        from sqlalchemy import text

        # Find products without embeddings or with stale hashes
        result = await session.execute(text("""
            SELECT p.id, p.name, p.description
            FROM product_bases p
            LEFT JOIN product_embeddings pe ON p.id = pe.product_base_id
            WHERE p.deleted_at IS NULL
            AND (pe.id IS NULL OR pe.content_hash != md5(COALESCE(p.name, '') || ' ' || COALESCE(p.description, '')))
            LIMIT 100
        """))
        rows = result.fetchall()

        if not rows:
            logger.info("[EmbeddingIndexer] Products: all up to date.")
            return

        encoder = self._get_encoder()
        texts = [f"{r.name} {r.description or ''}" for r in rows]

        # Embed in thread pool (CPU-bound, R1.8)
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, lambda: list(encoder.embed(texts))
        )

        for row, emb in zip(rows, embeddings):
            content = f"{row.name} {row.description or ''}"
            content_h = self._content_hash(content)
            vec_str = "[" + ",".join(map(str, emb.tolist())) + "]"

            await session.execute(text("""
                INSERT INTO product_embeddings (id, product_base_id, embedding, content_hash, created_at, updated_at)
                VALUES (:id, :pid, CAST(:vec AS vector), :hash, NOW(), NOW())
                ON CONFLICT (product_base_id)
                DO UPDATE SET embedding = CAST(:vec AS vector), content_hash = :hash, updated_at = NOW()
            """), {"id": str(uuid.uuid4()), "pid": row.id, "vec": vec_str, "hash": content_h})

        await session.commit()
        logger.info(f"[EmbeddingIndexer] Products: indexed {len(rows)} records.")

    async def _index_articles(self, session):
        """Embed all articles that don't have an embedding or whose content changed."""
        from sqlalchemy import text

        result = await session.execute(text("""
            SELECT a.id, a.title, a.content
            FROM articles a
            LEFT JOIN article_embeddings ae ON a.id = ae.article_id
            WHERE a.deleted_at IS NULL
            AND (ae.id IS NULL OR ae.content_hash != md5(COALESCE(a.title, '') || ' ' || LEFT(COALESCE(a.content, ''), 500)))
            LIMIT 100
        """))
        rows = result.fetchall()

        if not rows:
            logger.info("[EmbeddingIndexer] Articles: all up to date.")
            return

        encoder = self._get_encoder()
        texts = [f"{r.title} {(r.content or '')[:500]}" for r in rows]

        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, lambda: list(encoder.embed(texts))
        )

        for row, emb in zip(rows, embeddings):
            content = f"{row.title} {(row.content or '')[:500]}"
            content_h = self._content_hash(content)
            vec_str = "[" + ",".join(map(str, emb.tolist())) + "]"

            await session.execute(text("""
                INSERT INTO article_embeddings (id, article_id, embedding, content_hash, created_at, updated_at)
                VALUES (:id, :aid, CAST(:vec AS vector), :hash, NOW(), NOW())
                ON CONFLICT (article_id)
                DO UPDATE SET embedding = CAST(:vec AS vector), content_hash = :hash, updated_at = NOW()
            """), {"id": str(uuid.uuid4()), "aid": row.id, "vec": vec_str, "hash": content_h})

        await session.commit()
        logger.info(f"[EmbeddingIndexer] Articles: indexed {len(rows)} records.")
