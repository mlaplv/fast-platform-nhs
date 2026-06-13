"""
SEO Graph Service — CRUD & Graph Builder
=========================================
Xử lý:
  - Đăng ký/cập nhật/xóa SeoNode
  - Tạo/cập nhật/xóa SeoEdge
  - Build graph payload cho force-graph frontend
  - Integrity cleanup cho orphan nodes
"""
import logging
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, text

from backend.database.models.seo import SeoNode, SeoEdge, SeoEntityType, SeoLinkType
from backend.database import current_tenant_id
from backend.utils.uid import new_id_default
from backend.schemas.seo import (
    RegisterNodeRequest, UpdateNodeRequest,
    CreateEdgeRequest, UpdateEdgeRequest, CreateBulkEdgeRequest,
    SeoGraphResponse, GraphNodeItem, GraphLinkItem,
)

logger = logging.getLogger("api-gateway")

# ─── Color Palette ─────────────────────────────────────────────────────────────
_GROUP_COLORS = {
    "pillar": "#6366f1",          # Indigo — Pillar Page
    "cluster": "#a5b4fc",         # Light indigo — Cluster (confirmed)
    "unclassified": "#f59e0b",    # Amber — Chưa phân loại / cần review
}
_LINK_COLORS = {
    "confirmed": "#6366f1",
    "ai_suggested": "#f97316",    # Orange — highlight AI suggested
    "manual": "#10b981",          # Emerald — manual override
    "related": "#94a3b8",         # Slate — liên quan nhẹ
}


class SeoGraphService:

    # ─── Node CRUD ────────────────────────────────────────────────────────────

    async def register_node(self, db: AsyncSession, data: RegisterNodeRequest) -> SeoNode:
        """Đăng ký entity vào SEO graph. Upsert nếu đã tồn tại."""
        tenant = current_tenant_id.get() or "default"
        db_entity_type = SeoEntityType(data.entity_type.upper())

        # Safeguard: Only allow articles under the category "Bài viết"
        if db_entity_type == SeoEntityType.ARTICLE:
            category_row = await db.execute(
                text("SELECT category FROM articles WHERE id = :id AND deleted_at IS NULL"),
                {"id": data.entity_id}
            )
            cat = category_row.scalar()
            if cat and cat != "Bài viết":
                raise ValueError(
                    f"Chỉ được đăng ký các bài viết thuộc danh mục 'Bài viết' vào đồ thị SEO (Bài viết này thuộc danh mục: '{cat}')"
                )

        existing = await db.scalar(
            select(SeoNode).where(
                SeoNode.entity_type == db_entity_type,
                SeoNode.entity_id == data.entity_id,
                SeoNode.tenant_id == tenant,
            )
        )

        if existing:
            # Upsert & Restore if soft-deleted
            existing.deleted_at = None
            existing.is_pillar = existing.is_pillar or (data.is_pillar if data.is_pillar is not None else False)
            existing.pillar_topic = data.pillar_topic or existing.pillar_topic
            existing.node_label = data.node_label or existing.node_label
            existing.node_slug = data.node_slug or existing.node_slug
            existing.node_url = data.node_url or existing.node_url
            existing.ai_summary = data.ai_summary or existing.ai_summary
            existing.updated_at = datetime.now(timezone.utc)
            return existing

        node = SeoNode(
            id=new_id_default(),
            entity_type=db_entity_type,
            entity_id=data.entity_id,
            is_pillar=data.is_pillar,
            pillar_topic=data.pillar_topic,
            node_label=data.node_label,
            node_slug=data.node_slug,
            node_url=data.node_url,
            ai_summary=data.ai_summary,
            tenant_id=tenant,
        )
        db.add(node)
        return node

    async def update_node(self, db: AsyncSession, node_id: str, data: UpdateNodeRequest) -> Optional[SeoNode]:
        tenant = current_tenant_id.get() or "default"
        node = await db.scalar(
            select(SeoNode).where(SeoNode.id == node_id, SeoNode.tenant_id == tenant, SeoNode.deleted_at.is_(None))
        )
        if not node:
            return None
        if data.is_pillar is not None:
            node.is_pillar = data.is_pillar
        if data.pillar_topic is not None:
            node.pillar_topic = data.pillar_topic
        if data.node_label:
            node.node_label = data.node_label
        if data.node_url:
            node.node_url = data.node_url
        if data.ai_summary:
            node.ai_summary = data.ai_summary
        node.updated_at = datetime.now(timezone.utc)
        return node

    async def soft_delete_node(self, db: AsyncSession, node_id: str) -> bool:
        """Soft delete node bằng ID và xóa các edges liên quan."""
        tenant = current_tenant_id.get() or "default"
        now = datetime.now(timezone.utc)
        
        node = await db.scalar(
            select(SeoNode).where(
                SeoNode.id == node_id,
                SeoNode.tenant_id == tenant,
                SeoNode.deleted_at.is_(None)
            )
        )
        if not node:
            return False
            
        node.deleted_at = now
        node.updated_at = now
        
        # Xóa các edge liên kết với node này
        await db.execute(
            delete(SeoEdge).where(
                ((SeoEdge.source_node_id == node_id) | (SeoEdge.target_node_id == node_id)) &
                (SeoEdge.tenant_id == tenant)
            )
        )
        return True

    async def soft_delete_node_by_entity(self, db: AsyncSession, entity_type: str, entity_id: str) -> int:
        """Gọi từ Event Bus khi core entity bị soft-delete hoặc chuyển về nháp."""
        tenant = current_tenant_id.get() or "default"
        now = datetime.now(timezone.utc)
        db_entity_type = SeoEntityType(entity_type.upper())
        
        # 1. Fetch matching nodes first to get their IDs
        nodes = (await db.execute(
            select(SeoNode.id).where(
                SeoNode.entity_type == db_entity_type,
                SeoNode.entity_id == entity_id,
                SeoNode.tenant_id == tenant,
                SeoNode.deleted_at.is_(None),
            )
        )).scalars().all()
        
        if not nodes:
            return 0
            
        # 2. Soft delete the nodes
        res = await db.execute(
            update(SeoNode)
            .where(SeoNode.id.in_(nodes))
            .values(deleted_at=now, updated_at=now)
        )
        
        # 3. Delete the edges
        await db.execute(
            delete(SeoEdge).where(
                ((SeoEdge.source_node_id.in_(nodes)) | (SeoEdge.target_node_id.in_(nodes))) &
                (SeoEdge.tenant_id == tenant)
            )
        )
        
        count = res.rowcount
        if count:
            logger.info(f"[SeoGraph] Soft-deleted {count} seo_node(s) and their edges for {entity_type}:{entity_id}")
        return count

    # ─── Edge CRUD ────────────────────────────────────────────────────────────

    async def create_edge(self, db: AsyncSession, data: CreateEdgeRequest, user_id: Optional[str] = None) -> SeoEdge:
        """Tạo edge. Upsert nếu source→target đã tồn tại."""
        tenant = current_tenant_id.get() or "default"

        existing = await db.scalar(
            select(SeoEdge).where(
                SeoEdge.source_node_id == data.source_node_id,
                SeoEdge.target_node_id == data.target_node_id,
                SeoEdge.tenant_id == tenant,
            )
        )
        if existing:
            existing.link_type = data.link_type
            existing.ai_confidence = data.ai_confidence
            existing.ai_reasoning = data.ai_reasoning
            existing.is_confirmed = data.is_confirmed
            existing.override_by = user_id
            existing.updated_at = datetime.now(timezone.utc)
            return existing

        edge = SeoEdge(
            id=new_id_default(),
            source_node_id=data.source_node_id,
            target_node_id=data.target_node_id,
            link_type=data.link_type,
            ai_confidence=data.ai_confidence,
            ai_reasoning=data.ai_reasoning,
            is_confirmed=data.is_confirmed,
            override_by=user_id,
            tenant_id=tenant,
        )
        db.add(edge)
        return edge

    async def create_bulk_edges(self, db: AsyncSession, data: CreateBulkEdgeRequest, user_id: Optional[str] = None) -> dict:
        """Tạo/cập nhật hàng loạt edges giữa một source_node và nhiều target_nodes trong 1 transaction duy nhất."""
        tenant = current_tenant_id.get() or "default"
        
        if not data.target_node_ids:
            return {"success": True, "added": 0, "updated": 0}

        # Query all existing edges matching the pattern to avoid N+1 queries
        res = await db.scalars(
            select(SeoEdge).where(
                SeoEdge.source_node_id == data.source_node_id,
                SeoEdge.target_node_id.in_(data.target_node_ids),
                SeoEdge.tenant_id == tenant,
            )
        )
        existing_map = {e.target_node_id: e for e in res.all()}
        
        added_count = 0
        updated_count = 0
        
        for target_id in data.target_node_ids:
            if target_id in existing_map:
                existing = existing_map[target_id]
                existing.link_type = data.link_type
                existing.is_confirmed = data.is_confirmed
                existing.override_by = user_id
                existing.updated_at = datetime.now(timezone.utc)
                updated_count += 1
            else:
                edge = SeoEdge(
                    id=new_id_default(),
                    source_node_id=data.source_node_id,
                    target_node_id=target_id,
                    link_type=data.link_type,
                    is_confirmed=data.is_confirmed,
                    override_by=user_id,
                    tenant_id=tenant,
                )
                db.add(edge)
                added_count += 1
                
        await db.commit()
        return {
            "success": True,
            "added": added_count,
            "updated": updated_count,
        }

    async def update_edge(self, db: AsyncSession, edge_id: str, data: UpdateEdgeRequest, user_id: Optional[str] = None) -> Optional[SeoEdge]:
        """Dùng khi admin override (drag-and-drop trên graph)."""
        tenant = current_tenant_id.get() or "default"
        edge = await db.scalar(
            select(SeoEdge).where(SeoEdge.id == edge_id, SeoEdge.tenant_id == tenant)
        )
        if not edge:
            return None
        if data.source_node_id:
            edge.source_node_id = data.source_node_id
        if data.target_node_id:
            edge.target_node_id = data.target_node_id
        if data.link_type:
            edge.link_type = data.link_type
        if data.is_confirmed is not None:
            edge.is_confirmed = data.is_confirmed
        edge.override_by = user_id
        edge.updated_at = datetime.now(timezone.utc)
        return edge

    async def delete_edge(self, db: AsyncSession, edge_id: str) -> bool:
        tenant = current_tenant_id.get() or "default"
        res = await db.execute(
            delete(SeoEdge).where(SeoEdge.id == edge_id, SeoEdge.tenant_id == tenant)
        )
        return res.rowcount > 0

    # ─── Graph Builder ────────────────────────────────────────────────────────

    async def build_graph(self, db: AsyncSession, pillar_id: Optional[str] = None) -> SeoGraphResponse:
        """
        Build full Node-Link JSON payload or Sub-graph for a specific Pillar Node.
        Query seo_nodes + seo_edges, tính val/color server-side.
        Không JOIN vào core tables — dùng denormalized fields.
        """
        import asyncio
        tenant = current_tenant_id.get() or "default"

        if pillar_id:
            # 1. Tải thông tin Pillar Node
            pillar = await db.scalar(
                select(SeoNode).where(
                    SeoNode.id == pillar_id,
                    SeoNode.tenant_id == tenant,
                    SeoNode.deleted_at.is_(None)
                )
            )
            if not pillar:
                return SeoGraphResponse(
                    meta={
                        "total_nodes": 0,
                        "total_edges": 0,
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "pillars": 0,
                        "unclassified": 0,
                    },
                    nodes=[],
                    links=[],
                )

            # 2. Tìm các edge kết nối trực tiếp tới pillar này
            edges_query = select(SeoEdge).where(
                SeoEdge.tenant_id == tenant,
                (SeoEdge.source_node_id == pillar_id) | (SeoEdge.target_node_id == pillar_id)
            )
            edges_res = await db.execute(edges_query)
            edge_rows = edges_res.scalars().all()

            # Lấy tất cả các Node IDs liên quan (bao gồm cả pillar và các cluster con)
            connected_node_ids = {e.source_node_id for e in edge_rows} | {e.target_node_id for e in edge_rows}
            connected_node_ids.add(pillar_id)

            # 3. Tải thông tin các Node con này
            nodes_query = select(SeoNode).where(
                SeoNode.tenant_id == tenant,
                SeoNode.id.in_(connected_node_ids),
                SeoNode.deleted_at.is_(None)
            )
            nodes_res = await db.execute(nodes_query)
            node_rows = nodes_res.scalars().all()
        else:
            # Chế độ tải toàn bộ đồ thị: thực hiện song song bằng asyncio.gather để giảm latency tối đa
            node_task = db.execute(
                select(SeoNode).where(
                    SeoNode.tenant_id == tenant,
                    SeoNode.deleted_at.is_(None),
                )
            )
            edge_task = db.execute(
                select(SeoEdge).where(SeoEdge.tenant_id == tenant)
            )
            nodes_res, edges_res = await asyncio.gather(node_task, edge_task)
            node_rows = nodes_res.scalars().all()
            edge_rows = edges_res.scalars().all()

        # 4. Count edges per node for val scaling
        node_edge_count: dict[str, int] = {}
        for edge in edge_rows:
            node_edge_count[edge.source_node_id] = node_edge_count.get(edge.source_node_id, 0) + 1
            node_edge_count[edge.target_node_id] = node_edge_count.get(edge.target_node_id, 0) + 1

        # 5. Build set of connected node ids (to detect unclassified)
        connected_ids = {e.source_node_id for e in edge_rows} | {e.target_node_id for e in edge_rows}

        # 6. Assemble nodes
        graph_nodes: List[GraphNodeItem] = []
        for n in node_rows:
            if n.is_pillar:
                group = "pillar"
                val = 20
            elif n.id in connected_ids:
                group = "cluster"
                val = max(6, min(14, 4 + node_edge_count.get(n.id, 0) * 2))
            else:
                group = "unclassified"
                val = 5

            graph_nodes.append(GraphNodeItem(
                id=n.id,
                entity_type=n.entity_type,
                entity_id=n.entity_id,
                label=n.node_label,
                slug=n.node_slug,
                url=n.node_url,
                is_pillar=n.is_pillar,
                pillar_topic=n.pillar_topic,
                group=group,
                val=val,
                color=_GROUP_COLORS[group],
            ))

        # 7. Assemble edges (chỉ lấy các edge mà cả source và target đều tồn tại trong danh sách node hoạt động)
        active_node_ids = {node.id for node in node_rows}
        graph_links: List[GraphLinkItem] = []
        for e in edge_rows:
            if e.source_node_id not in active_node_ids or e.target_node_id not in active_node_ids:
                continue

            if e.is_confirmed:
                color = _LINK_COLORS.get(e.link_type, _LINK_COLORS["confirmed"])
            else:
                color = _LINK_COLORS["ai_suggested"]

            graph_links.append(GraphLinkItem(
                id=e.id,
                source=e.source_node_id,
                target=e.target_node_id,
                link_type=e.link_type,
                ai_confidence=e.ai_confidence,
                is_confirmed=e.is_confirmed,
                curvature=0.2,
                color=color,
            ))

        return SeoGraphResponse(
            meta={
                "total_nodes": len(graph_nodes),
                "total_edges": len(graph_links),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "pillars": sum(1 for n in graph_nodes if n.is_pillar),
                "unclassified": sum(1 for n in graph_nodes if n.group == "unclassified"),
            },
            nodes=graph_nodes,
            links=graph_links,
        )

    # ─── Integrity Cleanup (ARQ Job) ──────────────────────────────────────────

    async def reconcile_orphan_nodes(self, db: AsyncSession) -> dict:
        """
        Nightly ARQ job: Soft-delete seo_nodes có entity gốc đã bị xóa.
        Tách thành 2 queries độc lập (article, product).
        """
        now = datetime.now(timezone.utc)
        total = 0

        # Cleanup orphan article nodes
        res_art = await db.execute(text("""
            UPDATE seo_nodes sn
            SET deleted_at = :now, updated_at = :now
            WHERE sn.entity_type = 'ARTICLE'
              AND sn.deleted_at IS NULL
              AND NOT EXISTS (
                  SELECT 1 FROM articles a
                  WHERE a.id = sn.entity_id AND a.deleted_at IS NULL
              )
        """), {"now": now})
        total += res_art.rowcount

        # Cleanup orphan product nodes
        res_prod = await db.execute(text("""
            UPDATE seo_nodes sn
            SET deleted_at = :now, updated_at = :now
            WHERE sn.entity_type = 'PRODUCT'
              AND sn.deleted_at IS NULL
              AND NOT EXISTS (
                  SELECT 1 FROM product_bases p
                  WHERE p.id = sn.entity_id AND p.deleted_at IS NULL
              )
        """), {"now": now})
        total += res_prod.rowcount

        if total:
            logger.info(f"[SeoGraph] Reconcile: soft-deleted {total} orphan seo_node(s)")

        return {"orphans_cleaned": total}


# ─── DI Provider ──────────────────────────────────────────────────────────────

async def provide_seo_graph_service() -> SeoGraphService:
    return SeoGraphService()


seo_graph_service = SeoGraphService()
