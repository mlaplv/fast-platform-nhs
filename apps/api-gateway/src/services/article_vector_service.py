import logging
from typing import List, Dict, Union, Optional
from fastembed import TextEmbedding
from src.database import async_session_maker

logger = logging.getLogger("api-gateway")

class ArticleVectorService:
    """
    RAG Nano-Core: Semantic Search Service cho Articles
    Enforces strict pgvector typing via SQLAlchemy/Raw SQL.
    """
    def __init__(self):
        # Mắt Thần Tầng 1: Sử dụng chung model Multilingual
        self.embedding_model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    async def search_semantic(self, query: str, tenant_id: str = "default", limit: int = 5) -> List[Dict[str, object]]:
        try:
            # 1. Embed query
            vectors = list(self.embedding_model.embed([query]))
            embedding_array = vectors[0]

            # 2. Ép kiểu mảng float thành chuỗi chuẩn Vector của Postgres (BẮT BUỘC)
            vector_str = f"[{','.join(map(str, embedding_array))}]"

            # 3. Cú pháp SQL thuần BẮT BUỘC sử dụng (<=>) và Type Casting (::vector)
            raw_query = f"""
                SELECT a.id, a.title, a.slug, a.category, e.embedding <=> '{vector_str}'::vector AS cosine_distance
                FROM "articles" a
                JOIN "article_embeddings" e ON a.id = e.article_id
                WHERE a.deleted_at IS NULL 
                  AND a.tenant_id = $1
                  AND e.tenant_id = $1
                ORDER BY cosine_distance ASC
                LIMIT {limit};
            """

            # Thực thi thông qua SQLAlchemy/Raw
            from src.database import async_session_maker
            async with async_session_maker() as session:
                res = await session.execute(text(raw_query), {"tenant_id": tenant_id})
                results = res.mappings().all()

            # Format Data
            clean_results = [
                {
                    "id": r["id"], 
                    "title": r["title"], 
                    "slug": r["slug"],
                    "category": r["category"],
                    "match_score": round(1.0 - float(r["cosine_distance"]), 3)
                }
                for r in results
            ]
            return clean_results
        except Exception as e:
            logger.error(f"[VECTOR-SEARCH] Article RAG Query Failed: {e}", exc_info=True)
            return []

article_vector_service = ArticleVectorService()
