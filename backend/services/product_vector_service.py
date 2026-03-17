import logging
from typing import List, Dict, Union, Optional
from fastembed import TextEmbedding
from backend.database import async_session_maker

logger = logging.getLogger("api-gateway")

class ProductVectorService:
    """
    RAG Nano-Core: Semantic Search Service
    Enforces strict pgvector typing via SQLAlchemy/Raw SQL.
    """
    def __init__(self):
        # Mắt Thần Tầng 1: Sử dụng chung model Multilingual với Tier 1 Router
        self.embedding_model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    async def search_semantic(self, query: str, tenant_id: str = "default", limit: int = 5) -> List[Dict[str, object]]:
        try:
            # 1. Embed query
            vectors = list(self.embedding_model.embed([query]))
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
            from backend.database import async_session_maker
            async with async_session_maker() as session:
                res = await session.execute(text(raw_query), {"tid": tenant_id, "v": vector_str, "lim": limit})
                results = res.mappings().all()

            # Format Data
            clean_results = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "price": float(r["price"]),
                    "stock": r["stock"],
                    "description": r["description"],
                    "match_score": round(1.0 - float(r["cosine_distance"]), 3)
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
            loop = asyncio.get_running_loop()
            vectors = await loop.run_in_executor(None, lambda: list(self.embedding_model.embed([content])))

            if not vectors:
                return

            vector = vectors[0]
            vector_np = np.array(vector, dtype=np.float32)
            vector_hex = vector_np.tobytes().hex()

            sql = text("""
                INSERT INTO product_embeddings (id, product_base_id, embedding, created_at, updated_at)
                VALUES (:id, :product_id, :vector, NOW(), NOW())
                ON CONFLICT (product_base_id)
                DO UPDATE SET embedding = :vector, updated_at = NOW();
            """)
            await db_session.execute(sql, {"id": str(uuid.uuid4()), "product_id": product_id, "vector": vector_hex})
        except Exception as e:
            logger.error(f"[RAG] Product embedding failed for {product_id}: {e}")

product_vector_service = ProductVectorService()
