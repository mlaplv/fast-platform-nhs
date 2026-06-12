"""
SEO Pillar & Cluster — Litestar Controller
"""
import logging
from typing import Optional
from litestar import Controller, get, post, patch, delete
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum
from backend.schemas.common import SuccessResponse
from backend.schemas.seo import (
    RegisterNodeRequest, UpdateNodeRequest,
    CreateEdgeRequest, UpdateEdgeRequest,
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
    ) -> SeoGraphResponse:
        """
        Trả về toàn bộ Node-Link JSON để render force-graph trên frontend.
        Color và val đã được tính sẵn server-side.
        """
        return await graph_svc.build_graph(db_session)

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
        edge = await graph_svc.create_edge(db_session, data)
        await db_session.commit()
        return SuccessResponse(message="Edge đã được tạo.", data={"edge_id": edge.id})

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
            await redis_pool.enqueue_job("seo_bulk_match_job", tenant_id, _queue_name="high")
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
