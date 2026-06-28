"""
SEO Pillar & Cluster — Litestar Controller
"""
import logging
from typing import Optional
from litestar import Controller, get, post, patch, delete, Request
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.schemas.common import SuccessResponse
from backend.schemas.seo import (
    RegisterNodeRequest, UpdateNodeRequest,
    CreateEdgeRequest, UpdateEdgeRequest, CreateBulkEdgeRequest,
    SeoGraphResponse, TriggerMatchRequest, MatchResultResponse,
)
from backend.services.seo_graph_service import SeoGraphService, provide_seo_graph_service
from backend.services.seo_matching_service import SeoMatchingService, provide_seo_matching_service

logger = logging.getLogger("api-gateway")


class SeoController(Controller):
    """SEO Pillar & Cluster Management API."""
    path = "/api/v1/seo"
    guards = [PermissionGuard(PermissionEnum.CONTENT_READ)]
    dependencies = {
        "graph_svc": Provide(provide_seo_graph_service),
        "match_svc": Provide(provide_seo_matching_service),
    }

    # ─── Graph ────────────────────────────────────────────────────────────────

    @get("/graph", guards=[PermissionGuard(PermissionEnum.CONTENT_READ)])
    async def get_graph(
        self,
        db_session: AsyncSession,
        graph_svc: SeoGraphService,
        pillar_id: Optional[str] = None,
    ) -> SeoGraphResponse:
        """
        Trả về Node-Link JSON để render force-graph trên frontend.
        Hỗ trợ query parameter `pillar_id` để lấy đồ thị mạng lưới thu nhỏ của riêng Pillar đó.
        """
        return await graph_svc.build_graph(db_session, pillar_id=pillar_id)

    # ─── Node CRUD ────────────────────────────────────────────────────────────

    @post("/nodes", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)], status_code=201)
    async def register_node(
        self,
        db_session: AsyncSession,
        graph_svc: SeoGraphService,
        match_svc: SeoMatchingService,
        data: RegisterNodeRequest,
    ) -> SuccessResponse:
        """Đăng ký entity vào SEO graph. Nếu is_pillar=True sẽ tạo embedding ngay."""
        node = await graph_svc.register_node(db_session, data)
        await db_session.flush()

        # Tạo pillar embedding ngay khi node được designate là pillar (kể cả không có pillar_topic)
        if data.is_pillar:
            await match_svc.upsert_pillar_embedding(
                db_session, node.id,
                label=data.node_label,
                summary=data.ai_summary,
            )

        await db_session.commit()
        return SuccessResponse(message="Node đã được đăng ký vào SEO graph.", data={"node_id": node.id})

    @patch("/nodes/{node_id:str}", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def update_node(
        self,
        db_session: AsyncSession,
        graph_svc: SeoGraphService,
        match_svc: SeoMatchingService,
        node_id: str,
        data: UpdateNodeRequest,
    ) -> SuccessResponse:
        """Cập nhật node. Nếu is_pillar thay đổi → cập nhật embedding."""
        node = await graph_svc.update_node(db_session, node_id, data)
        if not node:
            raise NotFoundException(f"Không tìm thấy SEO node: {node_id}")

        # Re-embed nếu vừa được designate là pillar
        if data.is_pillar is True:
            await match_svc.upsert_pillar_embedding(
                db_session, node.id,
                label=node.node_label,
                summary=node.ai_summary,
            )

        await db_session.commit()
        return SuccessResponse(message="Cập nhật node thành công.")

    @delete("/nodes/{node_id:str}", status_code=200, guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def delete_node(
        self,
        db_session: AsyncSession,
        graph_svc: SeoGraphService,
        node_id: str,
    ) -> SuccessResponse:
        """Xóa node khỏi SEO graph."""
        deleted = await graph_svc.soft_delete_node(db_session, node_id)
        if not deleted:
            raise NotFoundException(f"Không tìm thấy SEO node: {node_id}")
        await db_session.commit()
        return SuccessResponse(message="Xóa node khỏi đồ thị SEO thành công.")

    # ─── Edge CRUD ────────────────────────────────────────────────────────────

    @post("/edges", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)], status_code=201)
    async def create_edge(
        self,
        db_session: AsyncSession,
        graph_svc: SeoGraphService,
        data: CreateEdgeRequest,
    ) -> SuccessResponse:
        """Tạo link thủ công giữa hai nodes."""
        db_add_edge = await graph_svc.create_edge(db_session, data)
        await db_session.commit()
        return SuccessResponse(message="Edge đã được tạo.", data={"edge_id": db_add_edge.id})

    @post("/edges/bulk", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)], status_code=201)
    async def create_bulk_edges(
        self,
        db_session: AsyncSession,
        graph_svc: SeoGraphService,
        data: CreateBulkEdgeRequest,
    ) -> SuccessResponse:
        """Tạo/cập nhật hàng loạt edges trong 1 transaction duy nhất."""
        result = await graph_svc.create_bulk_edges(db_session, data)
        return SuccessResponse(message="Edges đã được xử lý hàng loạt thành công.", data=result)

    @patch("/edges/{edge_id:str}", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def update_edge(
        self,
        db_session: AsyncSession,
        graph_svc: SeoGraphService,
        edge_id: str,
        data: UpdateEdgeRequest,
    ) -> SuccessResponse:
        """
        Override edge — gọi khi admin drag-and-drop node trên graph.
        Optimistic update đã được frontend xử lý, đây là server confirmation.
        """
        edge = await graph_svc.update_edge(db_session, edge_id, data)
        if not edge:
            raise NotFoundException(f"Không tìm thấy SEO edge: {edge_id}")
        await db_session.commit()
        return SuccessResponse(message="Edge đã được cập nhật.", data={"edge_id": edge.id})

    @delete("/edges/{edge_id:str}", status_code=200, guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)])
    async def delete_edge(
        self,
        db_session: AsyncSession,
        graph_svc: SeoGraphService,
        edge_id: str,
    ) -> SuccessResponse:
        deleted = await graph_svc.delete_edge(db_session, edge_id)
        if not deleted:
            raise NotFoundException(f"Không tìm thấy SEO edge: {edge_id}")
        await db_session.commit()
        return SuccessResponse(message="Edge đã được xóa.")

    # ─── AI Matching ──────────────────────────────────────────────────────────

    @post("/match", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)], status_code=200)
    async def trigger_match(
        self,
        db_session: AsyncSession,
        match_svc: SeoMatchingService,
        data: TriggerMatchRequest,
    ) -> MatchResultResponse:
        """
        Trigger AI matching thủ công cho một entity cụ thể.
        Dùng khi admin muốn re-match hoặc match lần đầu cho entity cũ.
        """
        # Lấy thông tin entity từ core tables
        from sqlalchemy import select, text as sa_text
        ent_type_lower = data.entity_type.lower()
        if ent_type_lower == "article":
            row = (await db_session.execute(
                sa_text("SELECT title, excerpt, slug FROM articles WHERE id = :id AND deleted_at IS NULL"),
                {"id": data.entity_id}
            )).mappings().first()
        else:
            row = (await db_session.execute(
                sa_text("SELECT name as title, short_description as excerpt, slug FROM product_bases WHERE id = :id AND deleted_at IS NULL"),
                {"id": data.entity_id}
            )).mappings().first()

        if not row:
            raise NotFoundException(f"Entity {data.entity_type}:{data.entity_id} không tồn tại.")

        result = await match_svc.match_entity(
            db=db_session,
            entity_type=ent_type_lower,
            entity_id=data.entity_id,
            title=str(row["title"] or ""),
            content_excerpt=str(row["excerpt"] or ""),
            slug=str(row["slug"] or ""),
        )
        await db_session.commit()

        # Auto-trigger contextual link analysis for articles immediately after manual matching
        if ent_type_lower == "article":
            try:
                from backend.infra.arq_config import get_redis_settings
                from arq import create_pool
                from backend.database import current_tenant_id
                
                tenant_id = current_tenant_id.get() or "default"
                redis = await create_pool(get_redis_settings())
                try:
                    await redis.enqueue_job(
                        "seo_contextual_link_job",
                        article_id=data.entity_id,
                        tenant_id=tenant_id,
                        _queue_name="high",
                    )
                finally:
                    await redis.aclose()
                logger.info(f"[SEO] Queued seo_contextual_link_job (high queue) for article:{data.entity_id} via manual trigger")
            except Exception as e:
                logger.warning(f"[SEO] Failed to queue seo_contextual_link_job after manual match: {e}")

        return result

    @post("/match/bulk", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)], status_code=200)
    async def trigger_bulk_match(
        self,
        db_session: AsyncSession,
        match_svc: SeoMatchingService,
    ) -> SuccessResponse:
        """
        Quét và chạy AI matching tự động cho toàn bộ các node đang ở trạng thái 'unclassified'
        ở chế độ chạy nền (background job) để tránh lỗi Gateway Timeout (504).
        """
        from backend.infra.arq_config import get_redis_settings
        from arq import create_pool
        from backend.database import current_tenant_id
        
        tenant_id = current_tenant_id.get() or "osmo.vn"
        try:
            redis_pool = await create_pool(get_redis_settings())
            try:
                await redis_pool.enqueue_job("seo_bulk_match_job", tenant_id, _queue_name="high")
            finally:
                await redis_pool.aclose()
            logger.info(f"🧬 [SeoController] Enqueued bulk matching background job for tenant {tenant_id}")
            return SuccessResponse(
                message="Hệ thống đã kích hoạt chạy AI Matching hàng loạt trong nền. Tiến trình sẽ tự động hoàn tất trong vài phút.",
                data={"status": "enqueued"},
            )
        except Exception as e:
            logger.error(f"❌ [SeoController] Failed to enqueue bulk matching job: {e}", exc_info=True)
            # Fallback sang chạy đồng bộ nếu Redis gặp sự cố
            result = await match_svc.bulk_match_unclassified(db_session)
            await db_session.commit()
            return SuccessResponse(
                message=f"Hoàn tất chạy AI Matching hàng loạt (đồng bộ) cho {result['total_nodes_processed']} nodes do sự cố kết nối hàng đợi.",
                data=result,
            )

    @post("/reconcile", guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)], status_code=200)
    async def manual_reconcile(
        self,
        db_session: AsyncSession,
        graph_svc: SeoGraphService,
    ) -> SuccessResponse:
        """Kích hoạt orphan cleanup thủ công (thay vì chờ nightly job)."""
        result = await graph_svc.reconcile_orphan_nodes(db_session)
        await db_session.commit()
        return SuccessResponse(
            message=f"Reconcile hoàn tất. Đã xóa {result['orphans_cleaned']} orphan node(s).",
            data=result,
        )

    # ─── Contextual Link Review (SGE Entity-Contextual Linking) ───────────────

    @get(
        "/contextual-links/pillar/{pillar_node_id:str}",
        guards=[PermissionGuard(PermissionEnum.CONTENT_READ)],
    )
    async def get_pillar_contextual_links(
        self,
        db_session: AsyncSession,
        pillar_node_id: str,
    ) -> dict:
        """Liệt kê tất cả các đề xuất contextual link trỏ về một Pillar Node cụ thể bằng Join tối ưu."""
        from sqlalchemy import select
        from backend.database.models.seo import SeoContextualLink, SeoNode
        from backend.database.models.content import Article
        from backend.database import current_tenant_id

        tenant = current_tenant_id.get() or "default"

        # 1. Đảm bảo Node này tồn tại và là Pillar (1 query đơn giản)
        pillar = await db_session.scalar(
            select(SeoNode).where(
                SeoNode.id == pillar_node_id,
                SeoNode.is_pillar == True,
                SeoNode.tenant_id == tenant,
                SeoNode.deleted_at.is_(None)
            )
        )
        if not pillar:
            raise NotFoundException(f"Pillar Node {pillar_node_id} không tồn tại hoặc không phải là Pillar.")

        # 2. Truy vấn tất cả links trỏ về target_node_id này kèm Join trực tiếp lấy Title của Article nguồn (1 query duy nhất)
        query = (
            select(SeoContextualLink, Article.title)
            .select_from(SeoContextualLink)
            .outerjoin(Article, SeoContextualLink.source_article_id == Article.id)
            .where(
                SeoContextualLink.target_node_id == pillar_node_id,
                SeoContextualLink.tenant_id == tenant,
            )
            .order_by(SeoContextualLink.created_at.desc())
        )
        res = await db_session.execute(query)
        rows = res.all()

        stats = {"pending": 0, "approved": 0, "rejected": 0, "applied": 0}
        links_data = []

        for l, article_title in rows:
            st = l.status if isinstance(l.status, str) else l.status.value
            if st in stats:
                stats[st] += 1

            links_data.append({
                "id": l.id,
                "source_article_id": l.source_article_id,
                "target_node_id": l.target_node_id,
                "target_url": l.target_url,
                "original_sentence": l.original_sentence,
                "linked_sentence": l.linked_sentence,
                "anchor_text": l.anchor_text,
                "matched_entity_type": l.matched_entity_type if isinstance(l.matched_entity_type, str) else l.matched_entity_type.value,
                "matched_entity_name": l.matched_entity_name,
                "ai_confidence": l.ai_confidence,
                "ai_reasoning": l.ai_reasoning,
                "sentence_index": l.sentence_index,
                "status": st,
                "reviewed_by": l.reviewed_by,
                "content_hash": l.content_hash,
                "link_rel": l.link_rel,
                "created_at": l.created_at.isoformat() if l.created_at else "",
                "target_label": pillar.node_label,
                "source_article_title": article_title or "Không xác định",
            })

        return {
            "pillar_node_id": pillar_node_id,
            "pillar_title": pillar.node_label,
            "links": links_data,
            "stats": stats,
        }

    @post(
        "/contextual-links/bulk-analyze",
        guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)],
        status_code=200,
    )
    async def trigger_bulk_contextual_link_analysis(
        self,
        db_session: AsyncSession,
    ) -> SuccessResponse:
        """Quét toàn bộ bài viết Cluster và trigger job sinh link ngữ cảnh hàng loạt trong nền."""
        from backend.infra.arq_config import get_redis_settings
        from arq import create_pool
        from backend.database import current_tenant_id
        from sqlalchemy import select
        from backend.database.models.content import Article

        tenant_id = current_tenant_id.get() or "default"
        
        # 1. Quét tất cả các bài viết thuộc category "Bài viết" và đã published
        articles = (await db_session.execute(
            select(Article.id, Article.content).where(
                Article.category == "Bài viết",
                Article.status == "PUBLISHED",
                Article.deleted_at.is_(None)
            )
        )).all()

        enqueued_count = 0
        try:
            redis_pool = await create_pool(get_redis_settings())
            try:
                for art in articles:
                    if not art.content:
                        continue
                    
                    await redis_pool.enqueue_job(
                        "seo_contextual_link_job",
                        article_id=art.id,
                        tenant_id=tenant_id,
                        _queue_name="high",
                    )
                    enqueued_count += 1
            finally:
                await redis_pool.aclose()

            logger.info(f"🧬 [SeoController] Enqueued bulk contextual link analysis for {enqueued_count} articles, tenant={tenant_id}")
            return SuccessResponse(
                message=f"Hệ thống đã nhận lệnh và đang phân tích link ngữ cảnh cho {enqueued_count} bài viết trong nền.",
                data={"enqueued_count": enqueued_count},
            )
        except Exception as e:
            logger.error(f"❌ [SeoController] Failed to enqueue bulk contextual link jobs: {e}", exc_info=True)
            return SuccessResponse(
                message=f"Có lỗi xảy ra khi đưa các bài viết vào hàng đợi: {str(e)}",
                data={"error": True},
            )

    @get(
        "/contextual-links",
        guards=[PermissionGuard(PermissionEnum.CONTENT_READ)],
    )
    async def list_all_contextual_links(
        self,
        db_session: AsyncSession,
        status: Optional[str] = None,
        source_article_id: Optional[str] = None,
        target_node_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Liệt kê toàn bộ đề xuất link ngữ cảnh và thống kê tổng quan toàn sàn bằng Single Join Query tối ưu."""
        import asyncio
        from sqlalchemy import select, func
        from sqlalchemy.orm import aliased
        from backend.database.models.seo import SeoContextualLink, SeoNode
        from backend.database.models.content import Article
        from backend.database import current_tenant_id

        tenant = current_tenant_id.get() or "default"

        # 1. Thống kê stats toàn hệ thống (Group By tối ưu)
        stats_query = (
            select(SeoContextualLink.status, func.count(SeoContextualLink.id))
            .where(SeoContextualLink.tenant_id == tenant)
            .group_by(SeoContextualLink.status)
        )

        # 2. Query danh sách link kết hợp Join trực tiếp lấy Title & Label (Chỉ 1 roundtrip)
        PillarNode = aliased(SeoNode)
        query = (
            select(
                SeoContextualLink,
                Article.title.label("source_article_title"),
                PillarNode.node_label.label("target_label"),
            )
            .select_from(SeoContextualLink)
            .outerjoin(Article, SeoContextualLink.source_article_id == Article.id)
            .outerjoin(PillarNode, SeoContextualLink.target_node_id == PillarNode.id)
            .where(SeoContextualLink.tenant_id == tenant)
        )

        if status:
            query = query.where(SeoContextualLink.status == status)
        if source_article_id:
            query = query.where(SeoContextualLink.source_article_id == source_article_id)
        if target_node_id:
            query = query.where(SeoContextualLink.target_node_id == target_node_id)

        query = query.order_by(SeoContextualLink.created_at.desc()).limit(limit).offset(offset)

        # Chạy tuần tự các truy vấn để tránh lỗi concurrency trên AsyncSession
        stats_res = await db_session.execute(stats_query)
        links_res = await db_session.execute(query)

        stats = {"pending": 0, "approved": 0, "rejected": 0, "applied": 0}
        for st, count in stats_res.all():
            st_val = st.value if hasattr(st, "value") else st
            if st_val in stats:
                stats[st_val] = count

        links_data = []
        for l, art_title, tgt_label in links_res.all():
            links_data.append({
                "id": l.id,
                "source_article_id": l.source_article_id,
                "source_article_title": art_title or "Không xác định",
                "target_node_id": l.target_node_id,
                "target_label": tgt_label or "Không xác định",
                "target_url": l.target_url,
                "original_sentence": l.original_sentence,
                "linked_sentence": l.linked_sentence,
                "anchor_text": l.anchor_text,
                "matched_entity_type": l.matched_entity_type if isinstance(l.matched_entity_type, str) else l.matched_entity_type.value,
                "matched_entity_name": l.matched_entity_name,
                "ai_confidence": l.ai_confidence,
                "ai_reasoning": l.ai_reasoning,
                "sentence_index": l.sentence_index,
                "status": l.status if isinstance(l.status, str) else l.status.value,
                "reviewed_by": l.reviewed_by,
                "content_hash": l.content_hash,
                "link_rel": l.link_rel,
                "created_at": l.created_at.isoformat() if l.created_at else "",
            })

        return {
            "links": links_data,
            "stats": stats,
        }

    @get(
        "/contextual-links/{article_id:str}",
        guards=[PermissionGuard(PermissionEnum.CONTENT_READ)],
    )
    async def get_contextual_links(
        self,
        db_session: AsyncSession,
        article_id: str,
    ) -> dict:
        """Liệt kê tất cả contextual link suggestions cho một bài viết bằng Join tối ưu."""
        import hashlib
        from sqlalchemy import select
        from backend.database.models.seo import SeoContextualLink, SeoNode
        from backend.database.models.content import Article
        from backend.database import current_tenant_id

        tenant = current_tenant_id.get() or "default"

        article = await db_session.scalar(
            select(Article).where(Article.id == article_id, Article.deleted_at.is_(None))
        )
        if not article:
            raise NotFoundException(f"Bài viết {article_id} không tồn tại.")

        current_hash = hashlib.md5((article.content or "").encode()).hexdigest()

        # Truy vấn kết hợp Join trực tiếp lấy label của Target Node (1 query duy nhất)
        query = (
            select(SeoContextualLink, SeoNode.node_label)
            .select_from(SeoContextualLink)
            .outerjoin(SeoNode, SeoContextualLink.target_node_id == SeoNode.id)
            .where(
                SeoContextualLink.source_article_id == article_id,
                SeoContextualLink.tenant_id == tenant,
            )
            .order_by(SeoContextualLink.sentence_index.asc())
        )
        res = await db_session.execute(query)
        rows = res.all()

        stats = {"pending": 0, "approved": 0, "rejected": 0, "applied": 0}
        links_data = []
        is_stale = False

        for l, target_label in rows:
            st = l.status if isinstance(l.status, str) else l.status.value
            if st in stats:
                stats[st] += 1
            if l.content_hash != current_hash:
                is_stale = True

            links_data.append({
                "id": l.id,
                "source_article_id": l.source_article_id,
                "target_node_id": l.target_node_id,
                "target_url": l.target_url,
                "original_sentence": l.original_sentence,
                "linked_sentence": l.linked_sentence,
                "anchor_text": l.anchor_text,
                "matched_entity_type": l.matched_entity_type if isinstance(l.matched_entity_type, str) else l.matched_entity_type.value,
                "matched_entity_name": l.matched_entity_name,
                "ai_confidence": l.ai_confidence,
                "ai_reasoning": l.ai_reasoning,
                "sentence_index": l.sentence_index,
                "status": st,
                "reviewed_by": l.reviewed_by,
                "content_hash": l.content_hash,
                "link_rel": l.link_rel,
                "link_title": l.link_title,
                "link_target": l.link_target,
                "created_at": l.created_at.isoformat() if l.created_at else "",
                "target_label": target_label or "Không xác định",
            })

        return {
            "article_id": article_id,
            "article_title": article.title,
            "content_hash": current_hash,
            "is_stale": is_stale,
            "links": links_data,
            "stats": stats,
        }

    @patch(
        "/contextual-links/{link_id:str}",
        guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)],
    )
    async def update_contextual_link(
        self,
        db_session: AsyncSession,
        link_id: str,
        data: dict,
    ) -> SuccessResponse:
        """Approve/Reject/Edit một contextual link suggestion."""
        import re
        from sqlalchemy import select
        from backend.database.models.seo import SeoContextualLink, SeoContextualLinkStatus
        from backend.database import current_tenant_id

        tenant = current_tenant_id.get() or "default"

        link = await db_session.scalar(
            select(SeoContextualLink).where(
                SeoContextualLink.id == link_id,
                SeoContextualLink.tenant_id == tenant,
            )
        )
        if not link:
            raise NotFoundException(f"Contextual link {link_id} không tồn tại.")

        new_status = data.get("status")
        new_anchor = data.get("anchor_text")
        new_target_url = data.get("target_url")
        new_rel = data.get("link_rel")
        new_title = data.get("link_title")
        new_target = data.get("link_target")

        if new_status:
            if new_status not in ("approved", "rejected"):
                return SuccessResponse(message="Status phải là 'approved' hoặc 'rejected'.", data={"error": True})
            link.status = SeoContextualLinkStatus(new_status)

        # Cập nhật anchor text nếu thay đổi
        if new_anchor and new_anchor != link.anchor_text:
            if new_anchor not in link.original_sentence:
                return SuccessResponse(
                    message=f"Anchor text '{new_anchor}' không tồn tại trong câu gốc.",
                    data={"error": True}
                )
            link.anchor_text = new_anchor

        # Cập nhật các trường khác nếu được gửi lên
        if new_target_url is not None:
            link.target_url = new_target_url
        if new_rel is not None:
            link.link_rel = new_rel or None
        if new_title is not None:
            link.link_title = new_title or None
        if new_target is not None:
            link.link_target = new_target or None

        # Tái dựng linked_sentence với các thuộc tính chuẩn SEO & SGE mới nhất
        attrs = []
        if link.link_rel and link.link_rel.strip().lower() not in ["", "dofollow"]:
            attrs.append(f'rel="{link.link_rel.strip()}"')
        if link.link_title:
            attrs.append(f'title="{link.link_title.strip()}"')
        if link.link_target:
            attrs.append(f'target="{link.link_target.strip()}"')

        attr_str = " " + " ".join(attrs) if attrs else ""
        a_tag = f'<a href="{link.target_url}" class="sge-contextual-link" data-sge-source="ai"{attr_str}>{link.anchor_text}</a>'
        link.linked_sentence = link.original_sentence.replace(link.anchor_text, a_tag, 1)

        await db_session.commit()

        # Invalidate news content cache
        if link.source_article_id:
            from backend.services.xohi_memory import xohi_memory
            try:
                if xohi_memory._use_redis and xohi_memory.client:
                    await xohi_memory.client.delete(f"news:content:{link.source_article_id}")
            except Exception as ce:
                logger.warning(f"Failed to clear news cache: {ce}")

        return SuccessResponse(message="Cập nhật contextual link thành công.")

    @post(
        "/contextual-links/{article_id:str}/apply",
        guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)],
        status_code=200,
    )
    async def apply_contextual_links(
        self,
        db_session: AsyncSession,
        request: Request,
        article_id: str,
    ) -> SuccessResponse:
        """Apply tất cả approved contextual links vào nội dung bài viết."""
        from backend.services.seo_contextual_linker import seo_contextual_linker

        user = request.scope.get("state", {}).get("user")
        reviewer_id = user.get("id") if user else None

        result = await seo_contextual_linker.apply_approved_links(
            db_session, article_id, reviewer_id=reviewer_id
        )
        await db_session.commit()

        # Invalidate news content cache
        from backend.services.xohi_memory import xohi_memory
        try:
            if xohi_memory._use_redis and xohi_memory.client:
                await xohi_memory.client.delete(f"news:content:{article_id}")
        except Exception as ce:
            logger.warning(f"Failed to clear news cache: {ce}")

        if result["applied_count"] == 0 and result["skipped_stale"] > 0:
            return SuccessResponse(
                message=f"Không thể apply. {result['skipped_stale']} link bị skip vì nội dung bài viết đã thay đổi. Cần re-analyze.",
                data=result,
            )

        if result["applied_count"] == 0 and result.get("skipped_inject_fail", 0) > 0:
            return SuccessResponse(
                message=f"Không thể chèn {result['skipped_inject_fail']} link do cấu trúc HTML không tương thích. Hãy chạy Phân tích lại.",
                data=result,
            )

        return SuccessResponse(
            message=f"Đã apply {result['applied_count']} link vào nội dung bài viết.",
            data=result,
        )

    @post(
        "/contextual-links/{link_id:str}/revert",
        guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)],
        status_code=200,
    )
    async def revert_contextual_link(
        self,
        db_session: AsyncSession,
        link_id: str,
    ) -> SuccessResponse:
        """Gỡ bỏ link đã chèn khỏi registry bằng cách đổi status về APPROVED."""
        from sqlalchemy import select
        from backend.database.models.seo import SeoContextualLink, SeoContextualLinkStatus
        from backend.database import current_tenant_id

        tenant = current_tenant_id.get() or "default"

        link = await db_session.scalar(
            select(SeoContextualLink).where(
                SeoContextualLink.id == link_id,
                SeoContextualLink.tenant_id == tenant,
            )
        )
        if not link:
            raise NotFoundException(f"Contextual link {link_id} không tồn tại.")

        if link.status != SeoContextualLinkStatus.APPLIED:
            return SuccessResponse(
                message="Liên kết này chưa được áp dụng (APPLIED).",
                data={"error": True}
            )

        link.status = SeoContextualLinkStatus.APPROVED
        await db_session.commit()

        # Invalidate news content cache
        if link.source_article_id:
            from backend.services.xohi_memory import xohi_memory
            try:
                if xohi_memory._use_redis and xohi_memory.client:
                    await xohi_memory.client.delete(f"news:content:{link.source_article_id}")
            except Exception as ce:
                logger.warning(f"Failed to clear news cache: {ce}")

        return SuccessResponse(message="Đã loại bỏ cập nhật liên kết thành công.")

    @post(
        "/contextual-links/pillar/{pillar_node_id:str}/apply",
        guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)],
        status_code=200,
    )
    async def apply_pillar_contextual_links(
        self,
        db_session: AsyncSession,
        request: Request,
        pillar_node_id: str,
    ) -> SuccessResponse:
        """Apply hàng loạt tất cả approved links trỏ về Pillar node hiện tại từ các Cluster articles."""
        from backend.database.models.seo import SeoContextualLink, SeoContextualLinkStatus
        from backend.services.seo_contextual_linker import seo_contextual_linker
        from sqlalchemy import select
        from backend.database import current_tenant_id

        tenant_id = current_tenant_id.get() or "default"
        user = request.scope.get("state", {}).get("user")
        reviewer_id = user.get("id") if user else None

        # 1. Tìm các unique source articles có approved links trỏ về pillar này
        res = await db_session.execute(
            select(SeoContextualLink.source_article_id).where(
                SeoContextualLink.target_node_id == pillar_node_id,
                SeoContextualLink.status == SeoContextualLinkStatus.APPROVED,
                SeoContextualLink.tenant_id == tenant_id,
            )
        )
        unique_src_ids = list(set(res.scalars().all()))

        if not unique_src_ids:
            return SuccessResponse(
                message="Không có đề xuất liên kết đã duyệt (Approved) nào cần chèn.",
                data={"applied_count": 0, "skipped_stale": 0, "processed_articles": 0}
            )

        total_applied = 0
        total_skipped = 0
        total_inject_fail = 0

        # 2. Xử lý apply cho từng article trong 1 session duy nhất
        for src_id in unique_src_ids:
            res_apply = await seo_contextual_linker.apply_approved_links(
                db_session, src_id, reviewer_id=reviewer_id
            )
            total_applied += res_apply["applied_count"]
            total_skipped += res_apply["skipped_stale"]
            total_inject_fail += res_apply.get("skipped_inject_fail", 0)

        await db_session.commit()

        # Invalidate news content cache for all processed source articles
        from backend.services.xohi_memory import xohi_memory
        try:
            if xohi_memory._use_redis and xohi_memory.client:
                for src_id in unique_src_ids:
                    await xohi_memory.client.delete(f"news:content:{src_id}")
        except Exception as ce:
            logger.warning(f"Failed to clear news cache: {ce}")

        return SuccessResponse(
            message=f"Đã chèn thành công {total_applied} liên kết vào {len(unique_src_ids)} bài viết. (Bỏ qua {total_skipped} link hết hạn, {total_inject_fail} link không khớp HTML).",
            data={
                "applied_count": total_applied,
                "skipped_stale": total_skipped,
                "skipped_inject_fail": total_inject_fail,
                "processed_articles": len(unique_src_ids),
            }
        )

    @post(
        "/contextual-links/pillar/{pillar_node_id:str}/analyze",
        guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)],
        status_code=200,
    )
    async def trigger_pillar_contextual_link_analysis(
        self,
        db_session: AsyncSession,
        pillar_node_id: str,
    ) -> SuccessResponse:
        """Tìm các Cluster articles liên kết với Pillar node hiện tại và trigger job phân tích link ngữ cảnh dưới nền."""
        from backend.infra.arq_config import get_redis_settings
        from arq import create_pool
        from backend.database import current_tenant_id
        from backend.database.models.seo import SeoNode, SeoEdge
        from sqlalchemy import select

        tenant_id = current_tenant_id.get() or "default"

        # 1. Đảm bảo Pillar Node tồn tại
        pillar = await db_session.scalar(
            select(SeoNode).where(
                SeoNode.id == pillar_node_id,
                SeoNode.tenant_id == tenant_id,
                SeoNode.deleted_at.is_(None)
            )
        )
        if not pillar:
            raise NotFoundException(f"Không tìm thấy Pillar Node {pillar_node_id}")

        # 2. Tìm tất cả các Cluster Nodes của Pillar này (source_node_id == pillar_node_id)
        edges = (await db_session.execute(
            select(SeoEdge.target_node_id).where(
                SeoEdge.source_node_id == pillar_node_id,
                SeoEdge.tenant_id == tenant_id
            )
        )).scalars().all()

        if not edges:
            return SuccessResponse(
                message="Pillar này chưa có bài viết Cluster nào liên kết. Vui lòng phân loại thêm bài viết vào Pillar trước.",
                data={"enqueued_count": 0}
            )

        # 3. Lọc ra các Nodes có entity_type là ARTICLE
        nodes = (await db_session.execute(
            select(SeoNode.entity_id).where(
                SeoNode.id.in_(edges),
                SeoNode.entity_type == "ARTICLE",
                SeoNode.tenant_id == tenant_id,
                SeoNode.deleted_at.is_(None)
            )
        )).scalars().all()

        article_ids = list(set(nodes))
        if not article_ids:
            return SuccessResponse(
                message="Không tìm thấy bài viết Cluster nào thuộc Pillar này để quét.",
                data={"enqueued_count": 0}
            )

        enqueued_count = 0
        try:
            redis_pool = await create_pool(get_redis_settings())
            try:
                for art_id in article_ids:
                    await redis_pool.enqueue_job(
                        "seo_contextual_link_job",
                        article_id=art_id,
                        tenant_id=tenant_id,
                        _queue_name="high",
                    )
                    enqueued_count += 1
            finally:
                await redis_pool.aclose()

            logger.info(f"🧬 [SeoController] Enqueued contextual link analysis for {enqueued_count} cluster articles of pillar {pillar_node_id}")
            return SuccessResponse(
                message=f"Đã bắt đầu quét phân tích link ngữ cảnh cho {enqueued_count} bài viết Cluster dưới nền. Đề xuất mới sẽ xuất hiện sau vài phút.",
                data={"enqueued_count": enqueued_count},
            )
        except Exception as e:
            logger.error(f"❌ [SeoController] Failed to enqueue contextual link jobs for pillar {pillar_node_id}: {e}", exc_info=True)
            return SuccessResponse(
                message=f"Có lỗi xảy ra khi kích hoạt hàng đợi quét: {str(e)}",
                data={"error": True},
            )

    @post(
        "/contextual-links/pillar/{pillar_node_id:str}/auto-link",
        guards=[PermissionGuard(PermissionEnum.CONTENT_WRITE)],
        status_code=200,
    )
    async def trigger_pillar_auto_link(
        self,
        db_session: AsyncSession,
        pillar_node_id: str,
    ) -> SuccessResponse:
        """Kích hoạt tiến trình tự động đi link từ các Cluster con trỏ về Pillar node hiện tại."""
        from backend.infra.arq_config import get_redis_settings
        from arq import create_pool
        from backend.database import current_tenant_id
        from backend.database.models.seo import SeoNode
        from sqlalchemy import select

        tenant_id = current_tenant_id.get() or "default"

        # Đảm bảo Node này tồn tại và là Pillar
        pillar = await db_session.scalar(
            select(SeoNode).where(
                SeoNode.id == pillar_node_id,
                SeoNode.is_pillar == True,
                SeoNode.tenant_id == tenant_id,
                SeoNode.deleted_at.is_(None)
            )
        )
        if not pillar:
            raise NotFoundException(f"Pillar Node {pillar_node_id} không tồn tại hoặc không phải là Pillar.")

        try:
            redis_pool = await create_pool(get_redis_settings())
            try:
                await redis_pool.enqueue_job(
                    "seo_pillar_auto_link_job",
                    pillar_id=pillar_node_id,
                    tenant_id=tenant_id,
                    force_scan=True,
                    _queue_name="high",
                )
            finally:
                await redis_pool.aclose()
            logger.info(f"🧬 [SeoController] Enqueued seo_pillar_auto_link_job for pillar {pillar_node_id}, tenant={tenant_id}")
            return SuccessResponse(
                message="Đã bắt đầu quét tìm đề xuất link từ các Cluster con dưới nền. Gợi ý mới sẽ xuất hiện ở bảng Chờ duyệt sau vài phút.",
                data={"status": "enqueued"},
            )
        except Exception as e:
            logger.error(f"❌ [SeoController] Failed to enqueue pillar auto-link job: {e}", exc_info=True)
            return SuccessResponse(
                message=f"Lỗi khi kích hoạt tiến trình tự động đi link: {str(e)}",
                data={"error": True},
            )

