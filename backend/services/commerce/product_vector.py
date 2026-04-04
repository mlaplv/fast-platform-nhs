import logging
from typing import List, Dict, Union, Optional, TypedDict
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
from backend.database import async_session_maker

logger = logging.getLogger("api-gateway")

class SemanticSearchResult(TypedDict):
    id: str
    name: str
    price: float
    stock: int
    description: Optional[str]
    match_score: float

class ProductVectorService:
    """
    RAG Nano-Core: Semantic Search Service
    Enforces strict pgvector typing via SQLAlchemy/Raw SQL.
    """
    def __init__(self):
        # [GHOST MODE] Service-local state only
        self._embedding_model = None

    @property
    def embedding_model(self):
        """Lazy loader for the embedding model."""
        if self._embedding_model is None:
            from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
            self._embedding_model = get_shared_encoder()
        return self._embedding_model

    async def search_semantic(self, db_session: AsyncSession, query: str, tenant_id: str = "default", limit: int = 5) -> List[SemanticSearchResult]:
        try:
            model = self.embedding_model
            if not model:
                logger.warning("[VECTOR-SEARCH] Encoder not ready. Skipping semantic search.")
                return []

            # 1. Embed query
            vectors = list(model.embed([query]))
            embedding_array = vectors[0]

            # 2. Ép kiểu mảng float thành chuỗi chuẩn Vector của Postgres (BẮT BUỘC)
            vector_str = f"[{','.join(map(str, embedding_array))}]"

            # 3. Cú pháp SQL thuần BẮT BUỘC sử dụng (<=>) và Type Casting (::vector)
            raw_query = """
                SELECT p.id, p."name", p."price", p."stock", p."description", e.embedding <=> :v::vector AS cosine_distance
                FROM "product_bases" p
                JOIN "product_embeddings" e ON p.id = e."productBaseId"
                WHERE p."deleted_at" IS NULL
                  AND p.tenant_id = :tid
                  AND e.tenant_id = :tid
                ORDER BY cosine_distance ASC
                LIMIT :lim;
            """

            # Thực thi thông qua SQLAlchemy/Raw
            from sqlalchemy import text
            res = await db_session.execute(text(raw_query), {"tid": tenant_id, "v": vector_str, "lim": limit})
            results = res.mappings().all()

            # Format Data
            clean_results: List[SemanticSearchResult] = [
                {
                    "id": str(r["id"]),
                    "name": str(r["name"]),
                    "price": float(r["price"]),
                    "stock": int(r["stock"]),
                    "description": str(r["description"]) if r["description"] else None,
                    "match_score": round(1.0 - float(r["cosine_distance"] or 1.0), 3)
                }
                for r in results
            ]
            return clean_results
        except Exception as e:
            logger.error(f"[VECTOR-SEARCH] RAG Query Failed: {e}", exc_info=True)
            return []

    async def upsert_product_embedding(self, db_session, product_id: str, name: str, description: Optional[str]) -> None:
        """Helper to generate and store pgvector embedding (Service-Centric)."""
        import uuid
        import asyncio
        import numpy as np
        from sqlalchemy import text

        try:
            content = f"{name} {description or ''}".strip()
            # Elite V2.2: Use local model and check readiness
            model = self.embedding_model
            if not model:
                logger.warning(f"[RAG] Product Encoder not ready. Skipping embedding for {product_id}")
                return

            loop = asyncio.get_running_loop()
            vectors = await loop.run_in_executor(None, lambda: list(model.embed([content])))

            if not vectors:
                return

            vector = vectors[0]
            vector_str = f"[{','.join(map(str, vector))}]"

            sql = text("""
                INSERT INTO product_embeddings (id, product_base_id, embedding, created_at, updated_at)
                VALUES (:id, :product_id, CAST(:vector AS vector), NOW(), NOW())
                ON CONFLICT (product_base_id)
                DO UPDATE SET embedding = CAST(:vector AS vector), updated_at = NOW();
            """)
            await db_session.execute(sql, {"id": str(uuid.uuid4()), "product_id": product_id, "vector": vector_str})
        except Exception as e:
            logger.warning(f"[RAG] Product embedding failed for {product_id}: {e}")

# ==========================================
# SERVICE PROVIDERS (V76.2 DI PATTERN)
# ==========================================

async def provide_product_vector_service() -> ProductVectorService:
    """Standard Litestar Provider for ProductVectorService."""
    return ProductVectorService()
