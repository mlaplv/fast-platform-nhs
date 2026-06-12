"""
SEO Matching Service — 3-Tier AI Fallback
==========================================
Tier 1: pgvector cosine similarity (≥ 0.75 → AUTO_ASSIGN)
Tier 2: PydanticAI classification (≥ 0.70 → AI_SUGGESTED)
Tier 3: UNCLASSIFIED queue (< 0.70 → node exists, no edge, admin reviews)

Design principles:
- Reuses existing encoder singleton (get_shared_encoder) — no new model loading
- Reuses pgvector pattern from ArticleVectorService
- PydanticAI only called when vector score is inconclusive
- All results persisted via SeoGraphService (no direct DB writes here)
"""
import asyncio
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from backend.database.models.seo import SeoNode, SeoPillarEmbedding, SeoLinkType
from backend.database import current_tenant_id
from backend.schemas.seo import (
    RegisterNodeRequest, CreateEdgeRequest, MatchResultResponse
)
from backend.services.seo_graph_service import SeoGraphService
from backend.utils.uid import new_id_default

logger = logging.getLogger("api-gateway")

_VECTOR_AUTO_THRESHOLD = 0.75    # Score >= này → AUTO
_AI_CONFIRM_THRESHOLD = 0.70     # Score >= này → AI_SUGGESTED
_EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"  # Matches shared encoder


class SeoMatchingService:
    """
    Orchestrates the 3-tier matching pipeline for new articles/products.
    """

    def __init__(self):
        self._graph_svc = SeoGraphService()

    def _get_encoder(self):
        from backend.services.ai_engine.core.encoder_singleton import get_shared_encoder
        return get_shared_encoder()

    # ─── Public Entry Point ────────────────────────────────────────────────────

    async def match_entity(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: str,
        title: str,
        content_excerpt: str,
        slug: str,
        url: Optional[str] = None,
    ) -> MatchResultResponse:
        """
        Main matching pipeline. Call khi entity mới được publish.
        1. Đảm bảo node được đăng ký vào seo_nodes
        2. Chạy 3-tier matching với các Pillar hiện tại
        3. Persist kết quả
        """
        tenant = current_tenant_id.get() or "default"

        # Step 1: Register node (upsert)
        ai_summary = f"{title}. {content_excerpt[:300]}" if content_excerpt else title
        node = await self._graph_svc.register_node(db, RegisterNodeRequest(
            entity_type=entity_type,
            entity_id=entity_id,
            is_pillar=False,
            node_label=title,
            node_slug=slug,
            node_url=url,
            ai_summary=ai_summary,
        ))
        await db.flush()  # Ensure node.id available

        # Step 2: Load all active Pillar nodes with embeddings
        pillars = await self._get_active_pillars(db, tenant)
        if not pillars:
            logger.info(f"[SeoMatch] No pillars found for tenant {tenant}. Node {node.id} → UNCLASSIFIED")
            return MatchResultResponse(
                node_id=node.id,
                matched_pillar_id=None,
                match_tier="unclassified",
                ai_confidence=None,
                ai_reasoning="Không có Pillar nào được đăng ký trong hệ thống.",
            )

        # Step 3: Tier 1 — pgvector cosine similarity
        best_pillar_id, vector_score = await self._vector_match(db, ai_summary, tenant)

        if best_pillar_id and vector_score >= _VECTOR_AUTO_THRESHOLD:
            await self._create_cluster_edge(
                db, node.id, best_pillar_id,
                link_type=SeoLinkType.PILLAR_CLUSTER,
                confidence=vector_score,
                reasoning=f"pgvector cosine similarity: {vector_score:.3f}",
                is_confirmed=False,
            )
            logger.info(f"[SeoMatch] Tier1 AUTO: {node.id} → {best_pillar_id} (score={vector_score:.3f})")
            return MatchResultResponse(
                node_id=node.id,
                matched_pillar_id=best_pillar_id,
                match_tier="auto",
                ai_confidence=vector_score,
                ai_reasoning=f"pgvector auto-match (score={vector_score:.3f})",
            )

        # Step 4: Tier 2 — PydanticAI classification
        ai_result = await self._pydantic_ai_match(title, content_excerpt, pillars)

        if ai_result and ai_result["confidence"] >= _AI_CONFIRM_THRESHOLD:
            await self._create_cluster_edge(
                db, node.id, ai_result["pillar_node_id"],
                link_type=SeoLinkType.AI_SUGGESTED,
                confidence=ai_result["confidence"],
                reasoning=ai_result.get("reasoning", ""),
                is_confirmed=False,
            )
            logger.info(f"[SeoMatch] Tier2 AI_SUGGESTED: {node.id} → {ai_result['pillar_node_id']} (conf={ai_result['confidence']:.2f})")
            return MatchResultResponse(
                node_id=node.id,
                matched_pillar_id=ai_result["pillar_node_id"],
                match_tier="ai_suggested",
                ai_confidence=ai_result["confidence"],
                ai_reasoning=ai_result.get("reasoning"),
            )

        # Step 5: Tier 3 — UNCLASSIFIED (node exists, no edge, admin reviews)
        logger.info(f"[SeoMatch] Tier3 UNCLASSIFIED: {node.id} — no confident match found")
        return MatchResultResponse(
            node_id=node.id,
            matched_pillar_id=None,
            match_tier="unclassified",
            ai_confidence=ai_result["confidence"] if ai_result else None,
            ai_reasoning="Confidence score quá thấp. Vui lòng phân loại thủ công trong SEO Graph.",
        )

    # ─── Tier 1: pgvector ────────────────────────────────────────────────────

    async def _vector_match(self, db: AsyncSession, text_to_embed: str, tenant: str) -> tuple[Optional[str], float]:
        """
        So sánh cosine similarity với tất cả Pillar embeddings.
        Trả về (best_pillar_node_id, score) hoặc (None, 0.0).
        """
        try:
            encoder = self._get_encoder()
            if not encoder:
                return None, 0.0

            loop = asyncio.get_running_loop()
            vectors = await loop.run_in_executor(None, lambda: list(encoder.embed([text_to_embed])))
            if not vectors:
                return None, 0.0

            vec_str = "[" + ",".join(map(str, vectors[0].tolist())) + "]"

            raw_sql = text("""
                SELECT sn.id AS node_id,
                       spe.embedding <=> CAST(:v AS vector) AS cosine_distance
                FROM seo_nodes sn
                JOIN seo_pillar_embeddings spe ON sn.id = spe.node_id
                WHERE sn.is_pillar = TRUE
                  AND sn.tenant_id = :tid
                  AND sn.deleted_at IS NULL
                ORDER BY cosine_distance ASC
                LIMIT 1
            """)
            res = await db.execute(raw_sql, {"v": vec_str, "tid": tenant})
            row = res.mappings().first()
            if not row:
                return None, 0.0

            score = round(1.0 - float(row["cosine_distance"] or 1.0), 3)
            return str(row["node_id"]), score

        except Exception as e:
            logger.error(f"[SeoMatch] pgvector match failed: {e}")
            return None, 0.0

    # ─── Tier 2: PydanticAI ──────────────────────────────────────────────────

    async def _pydantic_ai_match(
        self, title: str, excerpt: str, pillars: list[dict]
    ) -> Optional[dict]:
        """
        PydanticAI classification với strict output schema.
        Input: tiêu đề + excerpt của entity mới + danh sách pillars
        Output: { pillar_node_id, confidence, reasoning } hoặc None nếu fail
        
        Fail-safe: bất kỳ exception nào đều return None (→ Tier 3)
        """
        try:
            from pydantic_ai import Agent
            from pydantic import BaseModel

            class PillarMatch(BaseModel):
                pillar_node_id: str
                confidence: float
                reasoning: str

            pillar_list_text = "\n".join(
                f"- ID: {p['id']} | Topic: {p['pillar_topic'] or p['label']}"
                for p in pillars[:20]  # Cap at 20 để tránh context overflow
            )

            system_prompt = (
                "Bạn là chuyên gia SEO. Nhiệm vụ của bạn là phân loại một bài viết vào đúng Pillar Page. "
                "Chỉ trả về JSON theo schema được yêu cầu. Nếu không chắc chắn, đặt confidence < 0.70."
            )

            user_msg = (
                f"Bài viết mới:\nTiêu đề: {title}\nTóm tắt: {excerpt[:400]}\n\n"
                f"Danh sách Pillar Pages:\n{pillar_list_text}\n\n"
                f"Hãy chọn Pillar phù hợp nhất và trả về confidence score (0.0-1.0)."
            )

            # Use LiteLLM via PydanticAI
            from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
            model_name = trinity_bridge.get_default_model() if hasattr(trinity_bridge, "get_default_model") else "gemini-1.5-flash"

            agent: Agent[None, PillarMatch] = Agent(
                model=model_name,
                system_prompt=system_prompt,
                result_type=PillarMatch,
            )

            result = await asyncio.wait_for(
                agent.run(user_msg),
                timeout=15.0  # Hard timeout — tránh treo request
            )
            match = result.data

            # Validate pillar_node_id thực sự tồn tại trong danh sách
            valid_ids = {p["id"] for p in pillars}
            if match.pillar_node_id not in valid_ids:
                logger.warning(f"[SeoMatch] AI hallucinated pillar_node_id: {match.pillar_node_id}")
                return None

            return {
                "pillar_node_id": match.pillar_node_id,
                "confidence": round(match.confidence, 3),
                "reasoning": match.reasoning,
            }

        except asyncio.TimeoutError:
            logger.warning("[SeoMatch] PydanticAI timeout — falling back to Tier 3")
            return None
        except Exception as e:
            logger.error(f"[SeoMatch] PydanticAI failed: {e}")
            return None

    # ─── Helpers ─────────────────────────────────────────────────────────────

    async def _get_active_pillars(self, db: AsyncSession, tenant: str) -> list[dict]:
        rows = (await db.execute(
            select(SeoNode).where(
                SeoNode.is_pillar == True,
                SeoNode.tenant_id == tenant,
                SeoNode.deleted_at.is_(None),
            )
        )).scalars().all()
        return [{"id": n.id, "label": n.node_label, "pillar_topic": n.pillar_topic} for n in rows]

    async def _create_cluster_edge(
        self,
        db: AsyncSession,
        node_id: str,
        pillar_id: str,
        link_type: SeoLinkType,
        confidence: float,
        reasoning: str,
        is_confirmed: bool,
    ):
        from backend.database.models.seo import SeoEdge
        from backend.utils.uid import new_id_default
        tenant = current_tenant_id.get() or "default"

        existing = await db.scalar(
            select(SeoEdge).where(
                SeoEdge.source_node_id == pillar_id,
                SeoEdge.target_node_id == node_id,
                SeoEdge.tenant_id == tenant,
            )
        )
        if existing:
            existing.link_type = link_type
            existing.ai_confidence = confidence
            existing.ai_reasoning = reasoning
            existing.is_confirmed = is_confirmed
            return

        db.add(SeoEdge(
            id=new_id_default(),
            source_node_id=pillar_id,
            target_node_id=node_id,
            link_type=link_type.value,
            ai_confidence=confidence,
            ai_reasoning=reasoning,
            is_confirmed=is_confirmed,
            tenant_id=tenant,
        ))

    async def upsert_pillar_embedding(self, db: AsyncSession, node_id: str, label: str, summary: Optional[str]) -> None:
        """
        Tạo/cập nhật pgvector embedding cho Pillar node.
        Gọi ngay khi node được designate is_pillar=True.
        """
        import hashlib
        text_to_embed = f"{label} {summary or ''}".strip()
        content_hash = hashlib.md5(text_to_embed.encode()).hexdigest()

        # Check if already up-to-date
        existing = await db.scalar(
            select(SeoPillarEmbedding).where(SeoPillarEmbedding.node_id == node_id)
        )
        if existing and existing.content_hash == content_hash:
            return  # No change

        encoder = self._get_encoder()
        if not encoder:
            logger.warning(f"[SeoMatch] Encoder not ready, skipping pillar embedding for {node_id}")
            return

        loop = asyncio.get_running_loop()
        vectors = await loop.run_in_executor(None, lambda: list(encoder.embed([text_to_embed])))
        if not vectors:
            return

        vec_str = "[" + ",".join(map(str, vectors[0].tolist())) + "]"

        sql = text("""
            INSERT INTO seo_pillar_embeddings (id, node_id, embedding, content_hash, model_name, created_at, updated_at)
            VALUES (:id, :node_id, CAST(:vec AS vector), :hash, :model, NOW(), NOW())
            ON CONFLICT (node_id)
            DO UPDATE SET embedding = CAST(:vec AS vector), content_hash = :hash, updated_at = NOW()
        """)
        await db.execute(sql, {
            "id": new_id_default(),
            "node_id": node_id,
            "vec": vec_str,
            "hash": content_hash,
            "model": _EMBED_MODEL_NAME,
        })
        logger.info(f"[SeoMatch] Pillar embedding upserted for node {node_id}")


# ─── DI Provider ──────────────────────────────────────────────────────────────

async def provide_seo_matching_service() -> SeoMatchingService:
    return SeoMatchingService()


seo_matching_service = SeoMatchingService()
