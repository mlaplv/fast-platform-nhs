import uuid
from typing import Optional, List
from backend.utils.uid import new_id_default
import sqlalchemy as sa
from sqlalchemy import String, ForeignKey, Integer, JSON, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.models.base import Base, AuditMixin, SoftDeleteMixin, TenantMixin

class MediaRegistry(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    """
    AI-Professional Media Registry (V65.0)
    Hệ thống quản lý tài nguyên tập trung, hỗ trợ AI-metadata và truy vấn thần tốc.
    """
    __tablename__ = 'media_registry'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    filename: Mapped[str] = mapped_column(String, index=True)
    file_path: Mapped[str] = mapped_column(String, unique=True)
    file_size: Mapped[int] = mapped_column(Integer) # Bytes
    mime_type: Mapped[str] = mapped_column(String(50))

    # Visual Intelligence
    dimensions: Mapped[Optional[str]] = mapped_column(String(20)) # e.g. "1920x1080"
    blurhash: Mapped[Optional[str]] = mapped_column(String(100)) # Chuẩn UX quốc tế: Load ảnh mờ trước
    alt_text: Mapped[Optional[str]] = mapped_column(String)

    # Relationships & Ownership
    campaign_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('content_campaigns.id', ondelete='SET NULL'), index=True)
    owner_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('users.id', ondelete='SET NULL'), index=True)

    # Elite V2.2: Many-to-Many Tracking Optimization
    # Flag này giúp File Manager liệt kê ảnh "Mồ côi" cực nhanh mà không cần JOIN.
    is_linked: Mapped[bool] = mapped_column(Boolean, default=False, server_default=sa.text('false'), index=True)

    # AI & Professional Metadata (Extensible)
    media_metadata: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)

    provider: Mapped[str] = mapped_column(String(20), default="local") # local, s3, r2
    is_public: Mapped[bool] = mapped_column(sa.Boolean, default=True, server_default=sa.text('true')) # V10.0 RBAC

    # Inverse relationships
    campaign: Mapped[Optional["ContentCampaign"]] = relationship("ContentCampaign", backref="media_assets")
    usages: Mapped[List["MediaUsage"]] = relationship("MediaUsage", back_populates="asset", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_media_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_media_campaign_provider", "campaign_id", "provider"),
        Index("ix_media_is_linked", "tenant_id", "is_linked"),
    )

class MediaUsage(Base, AuditMixin, TenantMixin):
    """
    Elite V2.2: Junction table for many-to-many media tracking.
    Cho phép một ảnh được sử dụng tại nhiều Sản phẩm, Bài viết, Banner khác nhau.
    """
    __tablename__ = 'media_usage'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    asset_id: Mapped[str] = mapped_column(String, ForeignKey('media_registry.id', ondelete='CASCADE'), index=True)
    
    # Định danh đối tượng sử dụng (e.g. Product ID, News ID)
    entity_id: Mapped[str] = mapped_column(String, index=True)
    # Loại đối tượng (e.g. 'product', 'news', 'banner', 'category')
    entity_type: Mapped[str] = mapped_column(String(30), index=True)

    # Relationships
    asset: Mapped["MediaRegistry"] = relationship("MediaRegistry", back_populates="usages")

    __table_args__ = (
        Index("ix_media_usage_lookup", "entity_type", "entity_id"),
        Index("ix_media_usage_asset_entity", "asset_id", "entity_type", "entity_id", unique=True),
    )
