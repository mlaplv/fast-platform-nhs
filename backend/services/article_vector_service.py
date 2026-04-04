import logging
from typing import List, Dict, Union, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
from backend.database import async_session_maker

logger = logging.getLogger("api-gateway")

class ArticleVectorService:
    """
    RAG Nano-Core: Semantic Search Service cho Articles
    Enforces strict pgvector typing via SQLAlchemy/Raw SQL.
    """
    def __init__(self):
        # [GHOST MODE] Service-local state only
        self._embedding_model = None

    @property
    def embedding_model(self):
        """Lazy loader (V76.2: Trinity Boot)"""
        if self._embedding_model is None:
            from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
            self._embedding_model = get_shared_encoder()
        return self._embedding_model

    async def search_semantic(self, db_session: AsyncSession, query: str, tenant_id: str = "default", limit: int = 5) -> List[Dict[str, object]]:
        try:
            model = self.embedding_model
            if not model:
                logger.warning("[VECTOR-SEARCH] Article Encoder not ready. Skipping semantic search.")
                return []

            # 1. Embed query
            vectors = list(model.embed([query]))
            embedding_array = vectors[0]

            # 2. Ép kiểu mảng float thành chuỗi chuẩn Vector của Postgres (BẮT BUỘC)
            vector_str = f"[{','.join(map(str, embedding_array))}]"

            # 3. Cú pháp SQL thuần BẮT BUỘC sử dụng (<=>) và Type Casting (::vector)
            raw_query = """
                SELECT a.id, a.title, a.slug, a.category, e.embedding <=> CAST(:v AS vector) AS cosine_distance
                FROM "articles" a
                JOIN "article_embeddings" e ON a.id = e.article_id
                WHERE a.deleted_at IS NULL
                  AND a.tenant_id = :tid
                ORDER BY cosine_distance ASC
                LIMIT :lim;
            """

            # Thực thi thông qua SQLAlchemy/Raw
            from sqlalchemy import text
            res = await db_session.execute(text(raw_query), {"tid": tenant_id, "v": vector_str, "lim": limit})
            results = res.mappings().all()

            # Format Data
            clean_results = [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "slug": r["slug"],
                    "category": r["category"],
                    "match_score": round(1.0 - float(r["cosine_distance"] or 1.0), 3)
                }
                for r in results
            ]
            return clean_results
        except Exception as e:
            logger.error(f"[VECTOR-SEARCH] Article RAG Query Failed: {e}", exc_info=True)
            return []

    async def upsert_article_embedding(self, db_session, article_id: str, title: str, content: Optional[str]) -> None:
        """Helper to generate and store pgvector embedding (Service-Centric)."""
        import uuid
        import asyncio
        from sqlalchemy import text
        from backend.database import current_tenant_id

        try:
            text_to_embed = f"{title}\n{content or ''}".strip()

            # Rule 1.10: Run CPU-bound embedding in executor
            model = self.embedding_model
            if not model:
                logger.warning(f"[RAG] Encoder not ready. Skipping embedding for article {article_id}")
                return

            loop = asyncio.get_running_loop()
            vectors = await loop.run_in_executor(None, lambda: list(model.embed([text_to_embed])))

            if not vectors:
                return

            vector = vectors[0].tolist()
            vector_str = "[" + ",".join(map(str, vector)) + "]"
            tenant = current_tenant_id.get() or "default"

            sql = text("""
                INSERT INTO article_embeddings (id, article_id, embedding, created_at, updated_at)
                VALUES (:id, :article_id, CAST(:vector AS vector), NOW(), NOW())
                ON CONFLICT (article_id)
                DO UPDATE SET embedding = CAST(:vector AS vector), updated_at = NOW();
            """)
            await db_session.execute(sql, {
                "id": str(uuid.uuid4()),
                "article_id": article_id,
                "vector": vector_str
            })
        except Exception as e:
            logger.error(f"[RAG] Article embedding failed for {article_id}: {e}")

# ==========================================
# SERVICE PROVIDERS (V76.2 DI PATTERN)
# ==========================================

async def provide_article_vector_service() -> ArticleVectorService:
    """Standard Litestar Provider for ArticleVectorService."""
    return ArticleVectorService()
