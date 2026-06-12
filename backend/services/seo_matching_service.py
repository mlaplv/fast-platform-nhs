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
        from backend.services.seo_entity_extractor import SeoEntityExtractor
        self._entity_extractor = SeoEntityExtractor()

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

        # Step 0: Only allow articles in category "Bài viết"
        if entity_type.lower() == "article":
            category_row = await db.execute(
                text("SELECT category FROM articles WHERE id = :id AND deleted_at IS NULL"),
                {"id": entity_id}
            )
            cat = category_row.scalar()
            if cat and cat != "Bài viết":
                logger.info(f"[SeoMatch] Skipping {entity_id} because category is '{cat}' (not 'Bài viết')")
                # Delete any existing SEO node for this article if it exists
                existing = await db.scalar(
                    select(SeoNode).where(
                        SeoNode.entity_type == "ARTICLE",
                        SeoNode.entity_id == entity_id,
                        SeoNode.tenant_id == tenant,
                        SeoNode.deleted_at.is_(None)
                    )
                )
                if existing:
                    await self._graph_svc.soft_delete_node(db, existing.id)
                return MatchResultResponse(
                    node_id="",
                    matched_pillar_id=None,
                    match_tier="unclassified",
                    ai_confidence=0.0,
                    ai_reasoning=f"Bài viết thuộc danh mục '{cat}' không thuộc đối tượng đồ thị SEO.",
                )

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

        # If node is already a Pillar page, preserve status and skip matching
        if node.is_pillar:
            logger.info(f"[SeoMatch] Node {node.id} is already a Pillar. Skip matching.")
            # Still run entity extraction for pillar nodes (async, non-blocking for response)
            asyncio.create_task(
                self._entity_extractor.extract_and_persist(
                    db, node.id, title, content_excerpt, entity_type
                )
            )
            return MatchResultResponse(
                node_id=node.id,
                matched_pillar_id=None,
                match_tier="unclassified",
                ai_confidence=1.0,
                ai_reasoning="Node này đã được thiết lập làm Pillar page.",
            )

        # Step 1b: Run entity extraction to enrich ai_summary with entity context
        # This runs concurrently with the pillar lookup below
        try:
            entities, intent_type = await asyncio.wait_for(
                self._entity_extractor.extract_and_persist(
                    db, node.id, title, content_excerpt, entity_type
                ),
                timeout=25.0,
            )
            # Enrich ai_summary with extracted entities for better vector matching
            if entities:
                entity_names = self._entity_extractor.get_entity_names(entities)
                entity_context = ", ".join(entity_names[:8])
                ai_summary = f"{ai_summary} [{entity_context}]"
                node.ai_summary = ai_summary
            logger.info("[SeoMatch] Entity enrichment done: intent=%s entities=%d", intent_type, len(entities))
        except asyncio.TimeoutError:
            logger.warning("[SeoMatch] Entity extraction timed out — continuing without enrichment")
        except Exception as e:
            logger.warning("[SeoMatch] Entity extraction failed: %s — continuing", e)

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

        # Step 3: Tier 1 — pgvector cosine similarity (with entity-enriched summary)
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
                       CAST(spe.embedding AS vector) <=> CAST(:v AS vector) AS cosine_distance
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
        PydanticAI classification với strict output schema + retry logic.
        Input: tiêu đề + excerpt của entity mới + danh sách pillars
        Output: { pillar_node_id, confidence, reasoning } hoặc None nếu fail
        
        Retry: tối đa 2 lần, timeout tăng dần (10s → 18s), backoff 2s.
        Fail-safe: bất kỳ exception nào ở cả 2 lần đều return None (→ Tier 3)
        """
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
            "Bạn là một chuyên gia SEO thực thể (Entity SEO). Nhiệm vụ của bạn là phân loại bài viết mới vào Pillar Page phù hợp nhất. "
            "Hãy phân tích sự liên kết về mặt thực thể (Thương hiệu, hoạt chất, công dụng, nỗi đau khách hàng) giữa bài viết và các Pillar Pages. "
            "Đặc biệt đối chiếu các thực thể được liệt kê trong ngoặc vuông ở phần tóm tắt bài viết. "
            "Chỉ trả về JSON theo schema được yêu cầu. Nếu không chắc chắn, đặt confidence < 0.70."
        )

        user_msg = (
            f"Bài viết mới:\nTiêu đề: {title}\nTóm tắt & Thực thể: {excerpt[:500]}\n\n"
            f"Danh sách Pillar Pages để phân loại:\n{pillar_list_text}\n\n"
            f"Hãy phân tích và chọn Pillar phù hợp nhất về mặt thực thể ngữ nghĩa, trả về confidence score (0.0-1.0) và lý do lập luận (reasoning)."
        )

        # Use LiteLLM via PydanticAI
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

        agent: Agent[None, PillarMatch] = Agent(
            system_prompt=system_prompt,
            output_type=PillarMatch,
        )

        valid_ids = {p["id"] for p in pillars}

        # Retry loop: 2 attempts, increasing timeout, 2s backoff between attempts
        _timeouts = [10.0, 18.0]
        for attempt, timeout in enumerate(_timeouts, start=1):
            try:
                match = await trinity_bridge.run(
                    agent,
                    user_msg,
                    timeout=timeout,
                )

                # Validate pillar_node_id thực sự tồn tại trong danh sách
                if match.pillar_node_id not in valid_ids:
                    logger.warning(
                        f"[SeoMatch] Attempt {attempt}: AI hallucinated pillar_node_id "
                        f"{match.pillar_node_id!r}. Retrying..." if attempt < len(_timeouts) else
                        f"[SeoMatch] Attempt {attempt}: AI hallucinated pillar_node_id. Giving up."
                    )
                    if attempt < len(_timeouts):
                        await asyncio.sleep(2.0)
                        continue
                    return None

                logger.info(f"[SeoMatch] PydanticAI success on attempt {attempt} (conf={match.confidence:.2f})")
                return {
                    "pillar_node_id": match.pillar_node_id,
                    "confidence": round(match.confidence, 3),
                    "reasoning": match.reasoning,
                }

            except (asyncio.TimeoutError, TimeoutError):
                logger.warning(f"[SeoMatch] PydanticAI timeout on attempt {attempt}/{len(_timeouts)} (timeout={timeout}s)")
                if attempt < len(_timeouts):
                    await asyncio.sleep(2.0)
            except Exception as e:
                logger.error(f"[SeoMatch] PydanticAI error on attempt {attempt}: {e}")
                if attempt < len(_timeouts):
                    await asyncio.sleep(2.0)

        logger.warning("[SeoMatch] PydanticAI exhausted all retries — falling back to Tier 3")
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

    async def bulk_match_unclassified(self, db: AsyncSession) -> dict:
        """
        Quét và chạy AI matching tự động cho toàn bộ các node đang ở trạng thái 'unclassified'.
        """
        tenant = current_tenant_id.get() or "default"
        
        # 1. Lấy toàn bộ nodes chưa được phân loại (is_pillar = False và chưa có edges nào liên quan)
        from sqlalchemy import select, exists
        from backend.database.models.seo import SeoNode, SeoEdge
        
        stmt = select(SeoNode).where(
            SeoNode.tenant_id == tenant,
            SeoNode.deleted_at.is_(None),
            SeoNode.is_pillar.is_(False),
            ~exists().where(
                (SeoEdge.source_node_id == SeoNode.id) | (SeoEdge.target_node_id == SeoNode.id)
            )
        )
        nodes = (await db.execute(stmt)).scalars().all()
        
        success_count = 0
        failed_count = 0
        auto_matched = 0
        ai_suggested = 0
        unclassified = 0
        
        for node in nodes:
            try:
                # Lấy dữ liệu title/excerpt gốc từ core tables để chạy matching
                from sqlalchemy import text as sa_text
                if node.entity_type.lower() == "article":
                    row = (await db.execute(
                        sa_text("SELECT title, excerpt, slug FROM articles WHERE id = :id AND deleted_at IS NULL"),
                        {"id": node.entity_id}
                    )).mappings().first()
                else:
                    row = (await db.execute(
                        sa_text("SELECT name as title, short_description as excerpt, slug FROM product_bases WHERE id = :id AND deleted_at IS NULL"),
                        {"id": node.entity_id}
                    )).mappings().first()
                
                if not row:
                    continue
                
                res = await self.match_entity(
                    db=db,
                    entity_type=node.entity_type.lower(),
                    entity_id=node.entity_id,
                    title=str(row["title"] or ""),
                    content_excerpt=str(row["excerpt"] or ""),
                    slug=str(row["slug"] or ""),
                )
                await db.commit()
                success_count += 1
                if res.match_tier == "auto":
                    auto_matched += 1
                elif res.match_tier == "ai_suggested":
                    ai_suggested += 1
                else:
                    unclassified += 1
            except Exception as e:
                await db.rollback()
                logger.error(f"[SeoMatch] Bulk match failed for node {node.id}: {e}", exc_info=True)
                failed_count += 1
                
        return {
            "total_nodes_processed": len(nodes),
            "success": success_count,
            "failed": failed_count,
            "auto_matched": auto_matched,
            "ai_suggested": ai_suggested,
            "unclassified": unclassified
        }


# ─── DI Provider ──────────────────────────────────────────────────────────────

async def provide_seo_matching_service() -> SeoMatchingService:
    return SeoMatchingService()


seo_matching_service = SeoMatchingService()
