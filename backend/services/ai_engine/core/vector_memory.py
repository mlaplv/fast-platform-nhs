import numpy as np
import logging
import asyncio
from typing import List, Optional
from sqlalchemy import text
from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
from backend.database.alchemy_config import alchemy_config

logger = logging.getLogger("api-gateway")

class VectorMemory:
    @staticmethod
    async def search(transcript: str, session=None, context_type: str = "product", limit: int = 3) -> str:
        """
        Phase 77: Semantic RAG Search.
        Calculates cosine similarity in-memory for speed and 2GB RAM safety.
        """
        encoder = get_shared_encoder()
        if not encoder:
            return "Hệ thống tri thức đang khởi động, sếp đợi em chút ạ."

        loop = asyncio.get_event_loop()
        try:
            query_vec = (await loop.run_in_executor(None, lambda: list(encoder.embed([transcript]))))[0]
            query_vec = np.array(query_vec, dtype=np.float32)

            # Pre-normalize query vector
            q_norm = np.linalg.norm(query_vec)
            if q_norm > 0:
                query_vec = query_vec / q_norm
        except Exception as e:
            logger.error(f"[VectorMemory] Embedding failed: {e}")
            return ""

        # Handle session creation if not provided
        own_session = False
        if session is None:
            session_maker = alchemy_config.create_session_maker()
            session = session_maker()
            own_session = True

        try:
            results_text = []
            if context_type == "product":
                # Fetch all product embeddings via raw SQL join
                sql = text("""
                    SELECT p.name, p.price, p.stock, pe.embedding
                    FROM product_bases p
                    JOIN product_embeddings pe ON p.id = pe.product_base_id
                    WHERE p.deleted_at IS NULL
                """)
                result = await session.execute(sql)
                rows = result.all()
                if not rows: return ""

                # Phase 77.3: Vectorized Matrix Search
                embs = []
                metadata = []
                for name, price, stock, emb_data in rows:
                    try:
                        if isinstance(emb_data, str):
                            vec = np.frombuffer(bytes.fromhex(emb_data), dtype=np.float32)
                        else:
                            vec = np.frombuffer(emb_data, dtype=np.float32)

                        if vec.shape[0] == query_vec.shape[0]:
                            embs.append(vec)
                            metadata.append(f"- {name}: Giá {price:,.0f}đ (Kho còn {stock})")
                    except Exception: continue

                if not embs: return ""

                # Stack into Matrix (N x D)
                matrix = np.stack(embs)
                # Normalize matrix rows: M = M / ||M||
                m_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
                m_norms[m_norms == 0] = 1.0
                matrix = matrix / m_norms

                # Compute all scores: scores = M . q
                scores = np.dot(matrix, query_vec)

                # Get Top-K indices
                top_indices = np.argsort(scores)[::-1][:limit]
                results_text = [metadata[i] for i in top_indices if scores[i] > 0.1]

            elif context_type == "article":
                sql = text("""
                    SELECT a.title, a.category, ae.embedding
                    FROM articles a
                    JOIN article_embeddings ae ON a.id = ae.article_id
                    WHERE a.deleted_at IS NULL
                """)
                result = await session.execute(sql)
                rows = result.all()
                if not rows: return ""

                embs = []
                metadata = []
                for title, cat, emb_data in rows:
                    try:
                        if isinstance(emb_data, str):
                            vec = np.frombuffer(bytes.fromhex(emb_data), dtype=np.float32)
                        else:
                            vec = np.frombuffer(emb_data, dtype=np.float32)

                        if vec.shape[0] == query_vec.shape[0]:
                            embs.append(vec)
                            metadata.append(f"- [{cat}] {title}")
                    except Exception: continue

                if not embs: return ""

                matrix = np.stack(embs)
                m_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
                m_norms[m_norms == 0] = 1.0
                matrix = matrix / m_norms

                scores = np.dot(matrix, query_vec)
                top_indices = np.argsort(scores)[::-1][:limit]
                results_text = [metadata[i] for i in top_indices if scores[i] > 0.1]

            if not results_text:
                return ""

            return "\n".join(results_text)
        except Exception as e:
            logger.error(f"[VectorMemory] Search failed: {e}")
            return ""
        finally:
            if own_session:
                await session.close()
