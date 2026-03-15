from typing import Optional
import sqlalchemy as sa
from sqlalchemy import String, ForeignKey, Integer, JSON, Index
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

    # AI & Professional Metadata (Extensible)
    # Lưu: { "ai_tags": ["laptop", "office"], "original_url": "...", "compression_level": 85 }
    media_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    provider: Mapped[str] = mapped_column(String(20), default="local") # local, s3, r2
    is_public: Mapped[bool] = mapped_column(sa.Boolean, default=True, server_default=sa.text('true')) # V10.0 RBAC

    # Inverse relationships
    campaign: Mapped[Optional["ContentCampaign"]] = relationship("ContentCampaign", backref="media_assets")

    __table_args__ = (
        Index("ix_media_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_media_campaign_provider", "campaign_id", "provider"),
    )
