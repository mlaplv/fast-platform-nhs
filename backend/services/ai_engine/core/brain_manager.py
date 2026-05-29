import logging
import asyncio
import numpy as np
from typing import List, Dict, Optional, cast, TypedDict
from pydantic import JsonValue
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

    class DuplicateResult(TypedDict):
        type: str
        original_id: str
        duplicate_id: str
        name: str
        reason: str

    @staticmethod
    async def get_semantic_duplicates(db: AsyncSession, threshold: float = 0.92) -> List[DuplicateResult]:
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
    async def get_node_analytics(db: AsyncSession) -> Dict[str, JsonValue]:
        """
        Elite V2.2: Composite knowledge metrics (Optimized via pg_class estimation thưa sếp!).
        """
        from backend.database.models.system import SupportKnowledge, SupportKnowledgeEmbedding

        async def get_count_optimized(model, table_name: str) -> int:
            try:
                # Try Postgres high-speed estimation thưa sếp!
                res = await db.execute(sa_text("SELECT reltuples::bigint FROM pg_class WHERE relname = :table_name"), {"table_name": table_name})
                val = res.scalar()
                if val is not None and val >= 0:
                    return int(val)
            except Exception:
                pass
            
            # Fallback to standard count if pg_class fails (e.g. local SQLite testing)
            try:
                return await db.scalar(select(func.count()).select_from(model)) or 0
            except Exception as e:
                logger.error(f"[BrainManager] Optimized count fallback failed for {table_name}: {e}")
                return 0

        total_p = await get_count_optimized(ProductBase, "product_bases")
        total_a = await get_count_optimized(Article, "articles")
        total_k = await get_count_optimized(SupportKnowledge, "support_knowledge")

        emb_p = await get_count_optimized(ProductEmbedding, "product_embeddings")
        emb_a = await get_count_optimized(ArticleEmbedding, "article_embeddings")
        emb_k = await get_count_optimized(SupportKnowledgeEmbedding, "support_knowledge_embeddings")
        
        total_entities = total_p + total_a + total_k
        total_embeddings = emb_p + emb_a + emb_k
        coverage = (total_embeddings / total_entities) * 100 if total_entities > 0 else 100.0
        
        # Calculate real database size for vectors
        try:
            size_p = await db.scalar(sa_text("SELECT pg_total_relation_size('product_embeddings')")) or 0
            size_a = await db.scalar(sa_text("SELECT pg_total_relation_size('article_embeddings')")) or 0
            size_k = await db.scalar(sa_text("SELECT pg_total_relation_size('support_knowledge_embeddings')")) or 0
            total_size_bytes = size_p + size_a + size_k
        except Exception:
            # Fallback if unsupported (e.g. SQLite)
            total_size_bytes = total_embeddings * 3072 # 768 float32
        
        return {
            "total_entities": total_entities,
            "total_embeddings": total_embeddings,
            "coverage": round(coverage, 1),
            "storage_bytes": total_size_bytes
        }

    @staticmethod
    async def get_graph_nodes(db: AsyncSession) -> Dict[str, List[Dict]]:
        """
        Elite V2.2: Get lightweight topology of the entire Brain Matrix (Products, Articles, & Support Knowledge).
        """
        from backend.database.models.system import SupportKnowledge

        stmt_p = select(ProductBase.id, ProductBase.name, ProductBase.category_id)
        p_nodes = (await db.execute(stmt_p)).all()
        
        stmt_a = select(Article.id, Article.title, Article.category_id)
        a_nodes = (await db.execute(stmt_a)).all()

        stmt_k = select(SupportKnowledge.id, SupportKnowledge.question, SupportKnowledge.product_id).where(SupportKnowledge.deleted_at.is_(None))
        k_nodes = (await db.execute(stmt_k)).all()

        nodes = []
        # Core
        nodes.append({"id": "core", "label": "CORTEX CORE", "type": "core"})
        
        # Helen Learning Seed Templates (Elite V3.5)
        nodes.append({
            "id": "node_seed_templates",
            "label": "SEED TEMPLATES",
            "type": "template",
            "parent": "core"
        })
        
        # Product Hub
        nodes.append({"id": "hub_product", "label": "PRODUCTS", "type": "hub"})
        # Article Hub
        nodes.append({"id": "hub_article", "label": "ARTICLES", "type": "hub"})
        # Knowledge Hub
        nodes.append({"id": "hub_knowledge", "label": "KNOWLEDGE", "type": "hub"})

        product_ids = set()
        for p in p_nodes:
            product_ids.add(str(p[0]))
            nodes.append({
                "id": f"p_{p[0]}",
                "label": p[1][:25] + "..." if len(p[1]) > 25 else p[1],
                "type": "product",
                "parent": "hub_product"
            })
            
        for a in a_nodes:
            nodes.append({
                "id": f"a_{a[0]}",
                "label": a[1][:25] + "..." if len(a[1]) > 25 else a[1],
                "type": "article",
                "parent": "hub_article"
            })

        for k in k_nodes:
            parent_id = "hub_knowledge"
            if k[2] and str(k[2]) in product_ids:
                # Direct contextual linking to its associated Product Node!
                parent_id = f"p_{k[2]}"
            
            nodes.append({
                "id": f"k_{k[0]}",
                "label": k[1][:25] + "..." if len(k[1]) > 25 else k[1],
                "type": "knowledge",
                "parent": parent_id
            })
            
        return {"nodes": nodes}

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
                loop = asyncio.get_running_loop()
                vec = (await loop.run_in_executor(None, lambda: list(encoder.embed([text_input]))))[0]
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
                loop = asyncio.get_running_loop()
                vec = (await loop.run_in_executor(None, lambda: list(encoder.embed([text_input]))))[0]
                # [Elite V2.2] Surgical Fix: Use CAST() to avoid double-colon bind param conflict
                await db.execute(sa_text(
                    "INSERT INTO article_embeddings (id, article_id, embedding, created_at, updated_at) "
                    "VALUES (:id, :a_id, CAST(:emb AS vector), NOW(), NOW())"
                ), {"id": f"aemb_{a.id}", "a_id": a.id, "emb": str(vec.tolist())})
                await db.commit()
            except Exception as e:
                logger.error(f"[BrainManager] Failed A-emb {a.id}: {e}")
                await db.rollback()

        # SupportKnowledge Batch Sync (Elite RAG Integration)
        from backend.database.models.system import SupportKnowledge, SupportKnowledgeEmbedding
        stmt = select(SupportKnowledge).where(
            SupportKnowledge.deleted_at.is_(None),
            ~SupportKnowledge.id.in_(select(SupportKnowledgeEmbedding.knowledge_id))
        )
        missing_k = (await db.execute(stmt)).scalars().all()
        for k in missing_k:
            try:
                text_input = f"{k.question} {k.answer}"
                loop = asyncio.get_running_loop()
                vec = (await loop.run_in_executor(None, lambda: list(encoder.embed([text_input]))))[0]
                import uuid
                await db.execute(sa_text(
                    "INSERT INTO support_knowledge_embeddings (id, knowledge_id, embedding, created_at, updated_at, tenant_id) "
                    "VALUES (:id, :k_id, CAST(:emb AS vector), NOW(), NOW(), :tid)"
                ), {"id": str(uuid.uuid4()), "k_id": str(k.id), "emb": str(vec.tolist()), "tid": k.tenant_id or "default"})
                await db.commit()
            except Exception as e:
                logger.error(f"[BrainManager] Failed K-emb {k.id}: {e}")
                await db.rollback()

    @staticmethod
    async def purge_orphans(db: AsyncSession):
        """
        Clean up embeddings where the parent entity is gone.
        """
        from backend.database.models.system import SupportKnowledge, SupportKnowledgeEmbedding
        # Purge product embeddings
        await db.execute(delete(ProductEmbedding).where(~ProductEmbedding.product_base_id.in_(select(ProductBase.id))))
        # Purge article embeddings
        await db.execute(delete(ArticleEmbedding).where(~ArticleEmbedding.article_id.in_(select(Article.id))))
        # Purge knowledge embeddings
        await db.execute(delete(SupportKnowledgeEmbedding).where(~SupportKnowledgeEmbedding.knowledge_id.in_(select(SupportKnowledge.id))))
        await db.commit()
        logger.info("[BrainManager] Purge complete.")

brain_manager = BrainManager()
