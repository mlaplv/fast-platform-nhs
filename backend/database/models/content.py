from typing import Optional, List, Union
import sqlalchemy as sa
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
    parent_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('categories.id'))
    parent: Mapped[Optional["Category"]] = relationship("Category", back_populates="children", remote_side=[id])
    children: Mapped[List["Category"]] = relationship("Category", back_populates="parent")
    
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
    status: Mapped[str] = mapped_column(String, default="DRAFT")
    category: Mapped[str] = mapped_column(String, default="Tin tức")
    views: Mapped[int] = mapped_column(Integer, default=0)
    
    author_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('users.id'))
    author: Mapped[Optional["User"]] = relationship("User", back_populates="articles")

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
    embedding: Mapped[str] = mapped_column(Text)

class ContentCampaign(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'content_campaigns'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, sa.ForeignKey('users.id'))
    user: Mapped[Optional["User"]] = relationship("User", back_populates="content_campaigns")
    source_input: Mapped[str] = mapped_column(Text)
    reviewer_type: Mapped[str] = mapped_column(String, default="ADMIN_MANUAL")
    current_step: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default="WAITING_FOR_REVIEW")
    
    # The Golden Thread
    gold_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Step Data
    topic_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    assets_data: Mapped[Optional[Union[List[object], dict]]] = mapped_column(JSON, default=list)
    outline_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    draft_content: Mapped[Optional[str]] = mapped_column(Text)
    search_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_score: Mapped[float] = mapped_column(sa.Float, default=1.0)
    
    # --- PROFESSIONAL CTO HELPERS (Phase 42) ---
    def get_gold_config(self) -> dict:
        """Returns the creation configuration from gold_metadata or topic_data safely."""
        gold = self.gold_metadata or {}
        config = gold.get("creation_config")
        if config: return config

        topic = self.topic_data or {}
        return topic.get("creation_config") or {}

    def get_gold_val(self, key: str, fallback: object = None) -> object:
        """Surgically extracts a value from gold_metadata or falls back to topic_data."""
        gold = self.gold_metadata or {}
        if key in gold: return gold[key]
        
        topic = self.topic_data or {}
        return topic.get(key, fallback)

    # Deferred Loading for heavy fields (Rule R102)
    final_html: Mapped[Optional[str]] = deferred(mapped_column(Text))
    
    # Relationships
    events: Mapped[List["CampaignEvent"]] = relationship("CampaignEvent", back_populates="campaign", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_campaigns_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_campaigns_status", "status"),
    )

class CampaignEvent(Base, AuditMixin, TenantMixin):
    __tablename__ = 'campaign_events'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String, sa.ForeignKey('content_campaigns.id', ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String, index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    
    campaign: Mapped["ContentCampaign"] = relationship("ContentCampaign", back_populates="events")

    __table_args__ = (
        Index("ix_campaign_events_tenant", "tenant_id"),
    )
