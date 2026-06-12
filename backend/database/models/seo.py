"""
SEO Pillar & Cluster — Isolated Graph Models
============================================
Rule: ZERO modification to core tables (articles, product_bases).
Pattern mirrors existing article_embeddings / product_embeddings isolation.

Tables:
  seo_nodes            — polymorphic node registry (article OR product)
  seo_edges            — directed link/cluster relationships
  seo_pillar_embeddings — pgvector embeddings for AI similarity matching
"""
from typing import Optional
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import String, Boolean, Float, Text, Index, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.models.base import Base, AuditMixin, SoftDeleteMixin, TenantMixin
from backend.utils.uid import new_id_default
import enum


class SeoEntityType(str, enum.Enum):
    ARTICLE = "ARTICLE"
    PRODUCT = "PRODUCT"


class SeoLinkType(str, enum.Enum):
    PILLAR_CLUSTER = "pillar_cluster"   # AI hoặc manual xác nhận
    RELATED = "related"                 # Liên quan nhẹ, không phải cluster chính
    MANUAL = "manual"                   # Admin gán tay, không qua AI
    AI_SUGGESTED = "ai_suggested"       # AI đề xuất, chưa confirmed


class SeoNode(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    """
    Polymorphic SEO Node Registry.
    
    Đây là điểm neo (anchor) của mọi thực thể trong SEO graph.
    Một Article hoặc Product được đăng ký vào đây để tham gia graph.
    
    IMPORTANT: entity_id là soft-reference — không có native FK đến core tables.
    Cleanup được xử lý qua Event Bus + ARQ integrity job.
    
    Denormalized fields (node_label, node_slug, node_url):
    Cho phép graph query mà không cần JOIN vào core tables.
    """
    __tablename__ = "seo_nodes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)

    # Polymorphic reference — soft link đến core tables
    entity_type: Mapped[str] = mapped_column(
        SAEnum(SeoEntityType, name="seo_entity_type_enum", create_type=True),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # Pillar designation
    is_pillar: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    pillar_topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Denormalized display fields — updated via sync job or at registration
    node_label: Mapped[str] = mapped_column(String(500), nullable=False)
    node_slug: Mapped[str] = mapped_column(String(500), nullable=False)
    node_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # AI summary — short text used as input for PydanticAI classification
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # SGE Entity Intelligence — populated by SeoEntityExtractor after publish
    # Format: [{"type": "Brand", "name": "Miccosmo", "confidence": 0.95}, ...]
    entities_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Search intent classification: informational_why | informational_how | informational_what
    #                               | comparison | transactional | pillar | unknown
    intent_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Explicit pillar URL for schema isPartOf linking (fallback to node_url of pillar)
    pillar_url_override: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Relationships
    outgoing_edges: Mapped[list["SeoEdge"]] = relationship(
        "SeoEdge",
        foreign_keys="SeoEdge.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan",
    )
    incoming_edges: Mapped[list["SeoEdge"]] = relationship(
        "SeoEdge",
        foreign_keys="SeoEdge.target_node_id",
        back_populates="target_node",
        cascade="all, delete-orphan",
    )
    pillar_embedding: Mapped[Optional["SeoPillarEmbedding"]] = relationship(
        "SeoPillarEmbedding", back_populates="node", uselist=False
    )

    __table_args__ = (
        # Một entity chỉ được đăng ký 1 lần trong 1 tenant
        sa.UniqueConstraint("entity_type", "entity_id", "tenant_id", name="uq_seo_node_entity_tenant"),
        Index("ix_seo_nodes_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_seo_nodes_pillar", "is_pillar", "tenant_id"),
    )


class SeoEdge(Base, AuditMixin, TenantMixin):
    """
    Directed SEO Edge — Link relationship between two SeoNodes.
    
    source → target thường là: Pillar → Cluster
    Nhưng cũng có thể là: Cluster ↔ Cluster (related)
    
    ai_confidence: None nếu manual, float 0..1 nếu từ AI
    is_confirmed: False = AI suggested (hiển thị highlight), True = admin duyệt hoặc manual
    """
    __tablename__ = "seo_edges"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)

    source_node_id: Mapped[str] = mapped_column(
        String, sa.ForeignKey("seo_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_node_id: Mapped[str] = mapped_column(
        String, sa.ForeignKey("seo_nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    link_type: Mapped[str] = mapped_column(
        SAEnum(SeoLinkType, name="seo_link_type_enum", create_type=True),
        default=SeoLinkType.AI_SUGGESTED,
        nullable=False,
        index=True,
    )

    # AI metadata
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Confirmation state — drives frontend visual differentiation
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    override_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # user_id if manual

    source_node: Mapped["SeoNode"] = relationship(
        "SeoNode", foreign_keys=[source_node_id], back_populates="outgoing_edges"
    )
    target_node: Mapped["SeoNode"] = relationship(
        "SeoNode", foreign_keys=[target_node_id], back_populates="incoming_edges"
    )

    __table_args__ = (
        # Tránh duplicate edge giữa hai nodes cùng tenant
        sa.UniqueConstraint("source_node_id", "target_node_id", "tenant_id", name="uq_seo_edge_source_target"),
        Index("ix_seo_edges_tenant", "tenant_id"),
        Index("ix_seo_edges_confirmed", "is_confirmed", "tenant_id"),
    )


class SeoPillarEmbedding(Base, AuditMixin):
    """
    pgvector Embedding cho Pillar Nodes.
    
    Pattern giống hệt ArticleEmbedding và ProductEmbedding đã có.
    Column 'embedding' là pgvector column — dùng CAST(:v AS vector) khi query.
    content_hash dùng để detect stale embedding (từ EmbeddingIndexer pattern).
    """
    __tablename__ = "seo_pillar_embeddings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    node_id: Mapped[str] = mapped_column(
        String, sa.ForeignKey("seo_nodes.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    # pgvector column — stored as Text, cast to vector in raw SQL
    embedding: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    node: Mapped["SeoNode"] = relationship("SeoNode", back_populates="pillar_embedding")
