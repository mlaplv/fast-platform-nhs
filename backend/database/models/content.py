from typing import Optional, List, Union
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    String, ForeignKey, Integer, Text, JSON, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, deferred
from backend.database.models.base import Base, AuditMixin, SoftDeleteMixin, TenantMixin

class Category(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'categories'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String)
    parent_id: Mapped[Optional[str]] = mapped_column(String, sa.ForeignKey('categories.id'))
    parent: Mapped[Optional["Category"]] = relationship("Category", back_populates="children", remote_side=[id])
    children: Mapped[List["Category"]] = relationship("Category", back_populates="parent")
    
    # R102 Professional Upgrade: SEO & Fashion
    description: Mapped[Optional[str]] = mapped_column(Text)
    seo_title: Mapped[Optional[str]] = mapped_column(String)
    seo_description: Mapped[Optional[str]] = mapped_column(String)
    image: Mapped[Optional[str]] = mapped_column(String) # Category banner / icon URL
    icon: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Emoji or SVG icon path
    position: Mapped[int] = mapped_column(sa.Integer, default=0)
    show_on_mobile: Mapped[bool] = mapped_column(sa.Boolean, default=True)
    show_on_desktop: Mapped[bool] = mapped_column(sa.Boolean, default=True)
    category_metadata: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, server_default='{}') # Elite V2.2: FAQ & Extension metadata

    products: Mapped[List["ProductBase"]] = relationship("ProductBase", back_populates="category")

    __table_args__ = (
        Index("ix_categories_tenant_deleted", "tenant_id", "deleted_at"),
    )

class Article(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'articles'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String)
    excerpt: Mapped[Optional[str]] = mapped_column(String)
    content: Mapped[Optional[str]] = mapped_column(Text)
    seo_title: Mapped[Optional[str]] = mapped_column(String)
    seo_description: Mapped[Optional[str]] = mapped_column(String)
    seo_keywords: Mapped[Optional[str]] = mapped_column(String)
    seo_og_image: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="DRAFT")
    category: Mapped[str] = mapped_column(String, default="Bài viết")
    category_id: Mapped[Optional[str]] = mapped_column(String, sa.ForeignKey('categories.id'))
    views: Mapped[int] = mapped_column(Integer, default=0)
    featured_image: Mapped[Optional[str]] = mapped_column(String)

    # GEO 2026: Article metadata (FAQs, etc.) — mirrors product_metadata pattern
    article_metadata: Mapped[Optional[dict[str, object]]] = mapped_column(JSON, default=dict)
    
    author_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('users.id'))
    author: Mapped[Optional["User"]] = relationship("User", back_populates="articles")
    category_rel: Mapped[Optional["Category"]] = relationship("Category")

    embedding: Mapped[Optional["ArticleEmbedding"]] = relationship("ArticleEmbedding", back_populates="article", uselist=False)

    __table_args__ = (
        Index("ix_articles_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_articles_created_at", "created_at"),
    )

class ArticleEmbedding(Base, AuditMixin):
    __tablename__ = 'article_embeddings'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    article_id: Mapped[str] = mapped_column(String, ForeignKey('articles.id'), unique=True)
    article: Mapped["Article"] = relationship("Article", back_populates="embedding")
    embedding: Mapped[str] = mapped_column(sa.Text)

class ContentCampaign(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'content_campaigns'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, sa.ForeignKey('users.id'))
    user: Mapped[Optional["User"]] = relationship("User", back_populates="content_campaigns")
    source_input: Mapped[str] = mapped_column(Text)
    reviewer_type: Mapped[str] = mapped_column(String, default="ADMIN_MANUAL")
    current_step: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default="WAITING_FOR_REVIEW")
    category: Mapped[str] = mapped_column(String, default="CREATIVE_CONTENT", index=True)
    
    gold_metadata: Mapped[Optional[dict[str, object]]] = mapped_column(JSON, default=dict)
    topic_data: Mapped[Optional[dict[str, object]]] = mapped_column(JSON, default=dict)
    assets_data: Mapped[Optional[Union[list[object], dict[str, object]]]] = mapped_column(JSON, default=list)
    outline_data: Mapped[Optional[dict[str, object]]] = mapped_column(JSON, default=dict)
    draft_content: Mapped[Optional[str]] = mapped_column(Text)
    search_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_score: Mapped[float] = mapped_column(sa.Float, default=1.0)
    
    final_html: Mapped[Optional[str]] = deferred(mapped_column(Text))
    events: Mapped[List["CampaignEvent"]] = relationship("CampaignEvent", back_populates="campaign", cascade="all, delete-orphan")

    def get_gold_config(self) -> dict[str, object]:
        gold = self.gold_metadata or {}
        config = gold.get("creation_config")
        if isinstance(config, dict): return config
        topic = self.topic_data or {}
        config = topic.get("creation_config")
        return config if isinstance(config, dict) else {}

    def get_gold_val(self, key: str, fallback: Optional[object] = None) -> Optional[object]:
        gold = self.gold_metadata or {}
        if key in gold: return gold[key]
        topic = self.topic_data or {}
        return topic.get(key, fallback)

    __table_args__ = (
        Index("ix_campaigns_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_campaigns_status", "status"),
    )

class CampaignEvent(Base, AuditMixin, TenantMixin):
    __tablename__ = 'campaign_events'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String, sa.ForeignKey('content_campaigns.id', ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String, index=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    campaign: Mapped["ContentCampaign"] = relationship("ContentCampaign", back_populates="events")

    __table_args__ = (
        Index("ix_campaign_events_tenant", "tenant_id"),
    )

class Appointment(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'appointments'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    start_time: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), index=True)
    end_time: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    type: Mapped[str] = mapped_column(String, default="STRATEGY")
    status: Mapped[str] = mapped_column(String, default="UPCOMING")
    recurring_type: Mapped[str] = mapped_column(String, default="none") # none, daily, weekly, monthly
    recurring_metadata: Mapped[Optional[dict[str, object]]] = mapped_column(JSON, default=dict)
    
    campaign_id: Mapped[Optional[str]] = mapped_column(String, sa.ForeignKey('content_campaigns.id', ondelete="SET NULL"), index=True)
    campaign: Mapped[Optional["ContentCampaign"]] = relationship("ContentCampaign")
    metadata_json: Mapped[Optional[dict[str, object]]] = mapped_column(JSON, default=dict)

    __table_args__ = (
        Index("ix_appointments_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_appointments_time_range", "start_time", "end_time"),
    )

class ContentScout(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'content_scouts'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    topic: Mapped[str] = mapped_column(String, index=True)
    report_data: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    
    # CNS V62.2: TTL for cache (24h default)
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), index=True)

    __table_args__ = (
        Index("ix_scouts_tenant_topic", "tenant_id", "topic"),
    )
