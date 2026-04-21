import logging
import uuid
import asyncio
from typing import List, Dict, Union, Optional, TypedDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("api-gateway")

class KnowledgeSearchResult(TypedDict):
    id: str
    question: str
    answer: str
    match_score: float

class KnowledgeVectorService:
    """
    Elite V2.2: Hybrid Semantic Search for Support Knowledge.
    Integrates pgvector with Trinity Encoder.
    """
    def __init__(self):
        self._encoder = None

    @property
    def encoder(self):
        if self._encoder is None:
            from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
            self._encoder = get_shared_encoder()
        return self._encoder

    async def search_semantic(self, db_session: AsyncSession, query: str, tenant_id: str = "default", limit: int = 5) -> List[KnowledgeSearchResult]:
        """Layered Hybrid Search: pgvector (<=>) + Semantic Match Score."""
        try:
            model = self.encoder
            if not model:
                from backend.services.ai_engine.core.encoder_singleton import warmup_encoder
                logger.info("[KNOWLEDGE-VECTOR] Encoder not ready. Attempting emergency warmup...")
                await warmup_encoder()
                model = self.encoder
                if not model:
                    logger.warning("[KNOWLEDGE-VECTOR] Encoder STILL not ready after warmup.")
                    return []

            # 1. Generate Embeddings
            loop = asyncio.get_running_loop()
            vectors = await loop.run_in_executor(None, lambda: list(model.embed([query])))
            if not vectors: return []
            vector_str = f"[{','.join(map(str, vectors[0]))}]"

            # 2. Advanced pgvector Query (Elite Pattern)
            sql = text("""
                SELECT k.id, k.question, k.answer, e.embedding <=> CAST(:v AS vector) AS cosine_distance
                FROM support_knowledge k
                JOIN support_knowledge_embeddings e ON k.id = e.knowledge_id
                WHERE k.deleted_at IS NULL
                  AND k.is_active = TRUE
                  AND k.tenant_id = :tid
                ORDER BY cosine_distance ASC
                LIMIT :lim;
            """)

            res = await db_session.execute(sql, {"tid": tenant_id, "v": vector_str, "lim": limit})
            rows = res.mappings().all()

            return [
                {
                    "id": str(r["id"]),
                    "question": str(r["question"]),
                    "answer": str(r["answer"]),
                    "match_score": round(1.0 - float(r["cosine_distance"] or 1.0), 3)
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"[KNOWLEDGE-VECTOR] Search Failed: {e}")
            return []

    async def upsert_embedding(self, db_session: AsyncSession, knowledge_id: str, content: str, tenant_id: str = "default") -> None:
        """Atomic Vector Injection (Elite V2.2)."""
        try:
            model = self.encoder
            if not model: return

            loop = asyncio.get_running_loop()
            vectors = await loop.run_in_executor(None, lambda: list(model.embed([content])))
            if not vectors: return
            
            vector_str = f"[{','.join(map(str, vectors[0]))}]"

            sql = text("""
                INSERT INTO support_knowledge_embeddings (id, knowledge_id, embedding, created_at, updated_at, tenant_id)
                VALUES (:id, :kid, CAST(:v AS vector), NOW(), NOW(), :tid)
                ON CONFLICT (knowledge_id)
                DO UPDATE SET embedding = CAST(:v AS vector), updated_at = NOW(), tenant_id = :tid;
            """)
            await db_session.execute(sql, {"id": str(uuid.uuid4()), "kid": knowledge_id, "v": vector_str, "tid": tenant_id})
        except Exception as e:
            logger.warning(f"[KNOWLEDGE-VECTOR] Upsert Failed: {e}")

# Service Provider
async def provide_knowledge_vector_service() -> KnowledgeVectorService:
    return KnowledgeVectorService()

knowledge_vector_service = KnowledgeVectorService()
