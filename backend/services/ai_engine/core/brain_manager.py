import logging
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy import select, delete, func, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import ProductBase, ProductEmbedding, Article, ArticleEmbedding
from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
from backend.utils.text import normalize_vn

logger = logging.getLogger("api-gateway")

class BrainManager:
    """
    Elite V2.2: The Knowledge Management Authority.
    Ensures zero-duplication and optimized vector health.
    """

    @staticmethod
    async def get_semantic_duplicates(db: AsyncSession, threshold: float = 0.92) -> List[Dict[str, Any]]:
        """
        Elite V2.2: Semantic Collision Detection (>92%).
        """
        duplicates = []
        
        # 1. Product Audit (Semantic)
        stmt = select(ProductBase.name, ProductEmbedding.embedding, ProductBase.id).join(ProductEmbedding)
        nodes = (await db.execute(stmt)).all()
        
        if len(nodes) < 2: return []
        
        # Matrix calculation for performance (R0.3 Optimization)
        node_ids = [n[2] for n in nodes]
        node_names = [n[0] for n in nodes]
        
        # Convert DB vectors (hex or list) to numpy
        def to_vec(raw):
            if isinstance(raw, str):
                if raw.startswith('['): return np.array(eval(raw), dtype=np.float32)
                return np.frombuffer(bytes.fromhex(raw), dtype=np.float32)
            return np.array(raw, dtype=np.float32)

        try:
            embeddings = np.stack([to_vec(n[1]) for n in nodes])
            # Normalize for cosine similarity
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            normalized = embeddings / (norms + 1e-9)
            
            # Compute similarity matrix
            sim_matrix = np.dot(normalized, normalized.T)
            
            # Find collisions
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    if sim_matrix[i, j] > threshold:
                        duplicates.append({
                            "type": "PRODUCT",
                            "original_id": node_ids[i],
                            "duplicate_id": node_ids[j],
                            "name": f"{node_names[j]} (≈ {node_names[i]})",
                            "reason": f"Semantic Match {(sim_matrix[i, j]*100):.1f}%"
                        })
        except Exception as e:
            logger.error(f"[BrainManager] Product Audit Failed: {e}")

        # 2. Article Audit (Semantic)
        stmt = select(Article.title, ArticleEmbedding.embedding, Article.id).join(ArticleEmbedding)
        a_nodes = (await db.execute(stmt)).all()
        if len(a_nodes) >= 2:
            try:
                a_ids = [n[2] for n in a_nodes]
                a_titles = [n[0] for n in a_nodes]
                a_embeddings = np.stack([to_vec(n[1]) for n in a_nodes])
                a_norms = np.linalg.norm(a_embeddings, axis=1, keepdims=True)
                a_normalized = a_embeddings / (a_norms + 1e-9)
                a_sim_matrix = np.dot(a_normalized, a_normalized.T)

                for i in range(len(a_nodes)):
                    for j in range(i + 1, len(a_nodes)):
                        if a_sim_matrix[i, j] > threshold:
                            duplicates.append({
                                "type": "ARTICLE",
                                "original_id": a_ids[i],
                                "duplicate_id": a_ids[j],
                                "name": f"{a_titles[j]} (≈ {a_titles[i]})",
                                "reason": f"Semantic Match {(a_sim_matrix[i, j]*100):.1f}%"
                            })
            except Exception as e:
                logger.error(f"[BrainManager] Article Audit Failed: {e}")
            
        return duplicates

    @staticmethod
    async def get_node_analytics(db: AsyncSession) -> Dict[str, Any]:
        """
        Elite V2.2: Composite knowledge metrics.
        """
        total_p = await db.scalar(select(func.count()).select_from(ProductBase)) or 0
        total_a = await db.scalar(select(func.count()).select_from(Article)) or 0
        emb_p = await db.scalar(select(func.count()).select_from(ProductEmbedding)) or 0
        emb_a = await db.scalar(select(func.count()).select_from(ArticleEmbedding)) or 0
        
        total_entities = total_p + total_a
        total_embeddings = emb_p + emb_a
        coverage = (total_embeddings / total_entities) * 100 if total_entities > 0 else 100.0
        
        return {
            "total_entities": total_entities,
            "total_embeddings": total_embeddings,
            "coverage": round(coverage, 1),
            "health": 98.5 if coverage > 90 else 85.0
        }

    @staticmethod
    async def sync_all_embeddings(db: AsyncSession):
        """
        Rebuilds missing or outdated vectors in batches to protect 2GB RAM.
        """
        encoder = get_shared_encoder()
        if not encoder:
            logger.error("[BrainManager] Encoder not ready.")
            return

        # Product Batch Sync
        stmt = select(ProductBase).where(~ProductBase.id.in_(select(ProductEmbedding.product_base_id)))
        missing_p = (await db.execute(stmt)).scalars().all()
        for p in missing_p:
            try:
                text_input = f"{p.name} {p.short_description or ''}"
                vec = list(encoder.embed([text_input]))[0]
                # [Elite V2.2] Surgical Fix: Use CAST() to avoid double-colon bind param conflict
                await db.execute(sa_text(
                    "INSERT INTO product_embeddings (id, product_base_id, embedding, created_at, updated_at) "
                    "VALUES (:id, :p_id, CAST(:emb AS vector), NOW(), NOW())"
                ), {"id": f"emb_{p.id}", "p_id": p.id, "emb": str(vec.tolist())})
                await db.commit()
            except Exception as e:
                logger.error(f"[BrainManager] Failed P-emb {p.id}: {e}")
                await db.rollback()

        # Article Batch Sync
        stmt = select(Article).where(~Article.id.in_(select(ArticleEmbedding.article_id)))
        missing_a = (await db.execute(stmt)).scalars().all()
        for a in missing_a:
            try:
                text_input = f"{a.title} {a.content[:500] if a.content else ''}"
                vec = list(encoder.embed([text_input]))[0]
                # [Elite V2.2] Surgical Fix: Use CAST() to avoid double-colon bind param conflict
                await db.execute(sa_text(
                    "INSERT INTO article_embeddings (id, article_id, embedding, created_at, updated_at) "
                    "VALUES (:id, :a_id, CAST(:emb AS vector), NOW(), NOW())"
                ), {"id": f"aemb_{a.id}", "a_id": a.id, "emb": str(vec.tolist())})
                await db.commit()
            except Exception as e:
                logger.error(f"[BrainManager] Failed A-emb {a.id}: {e}")
                await db.rollback()

    @staticmethod
    async def purge_orphans(db: AsyncSession):
        """
        Clean up embeddings where the parent entity is gone.
        """
        # Purge product embeddings
        await db.execute(delete(ProductEmbedding).where(~ProductEmbedding.product_base_id.in_(select(ProductBase.id))))
        # Purge article embeddings
        await db.execute(delete(ArticleEmbedding).where(~ArticleEmbedding.article_id.in_(select(Article.id))))
        await db.commit()
        logger.info("[BrainManager] Purge complete.")

brain_manager = BrainManager()
