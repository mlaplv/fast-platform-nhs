import sqlalchemy as sa
from datetime import datetime, timezone
from typing import Optional, List, Union, Dict
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, JSON, DateTime, ForeignKey, text, Column, Table, Index
)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship, deferred
from backend.constants.voice import DEFAULT_GREETING, DEFAULT_FAREWELL

Base = declarative_base()

# Helper for UTC now
def utcnow():
    return datetime.now(timezone.utc)

# --- THIẾT QUÂN LUẬT MIXINS ---

class AuditMixin:
    """Standardized audit fields for transparency."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class SoftDeleteMixin:
    """Standardized soft delete logic (Rule R38)."""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class TenantMixin:
    """Standardized multi-tenancy support."""
    tenant_id: Mapped[str] = mapped_column(String, default="default", index=True)

# RBAC Association Tables (ManyToMany)
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", String, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

class User(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'users'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[Optional[str]] = mapped_column(String)
    password: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="ACTIVE")
    
    # Relationships
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")
    drafts: Mapped[List["Draft"]] = relationship("Draft", foreign_keys="Draft.reviewer_id")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    content_campaigns: Mapped[List["ContentCampaign"]] = relationship("ContentCampaign", back_populates="user", cascade="all, delete-orphan")
    articles: Mapped[List["Article"]] = relationship("Article", back_populates="author")
    chat_messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="user")
    voice_profile: Mapped[Optional["VoiceProfile"]] = relationship("VoiceProfile", back_populates="user", uselist=False)
    
    # RBAC M2M
    roles: Mapped[List["Role"]] = relationship("Role", secondary=user_roles, back_populates="users")

    # [XOHI] Optimized Index for multi-tenant soft-delete lookups
    __table_args__ = (
        Index("ix_users_tenant_deleted", "tenant_id", "deleted_at"),
    )

class VoiceProfile(Base, AuditMixin):
    __tablename__ = 'voice_profiles'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey('users.id'), unique=True)
    user: Mapped["User"] = relationship("User", back_populates="voice_profile")
    wake_words: Mapped[list[str]] = mapped_column(JSON, default=list) # Replace array with JSON
    sleep_words: Mapped[list[str]] = mapped_column(JSON, default=list) # Replace array with JSON
    greeting_template: Mapped[str] = mapped_column(String, default=DEFAULT_GREETING)
    farewell_template: Mapped[str] = mapped_column(String, default=DEFAULT_FAREWELL)
    capabilities: Mapped[dict] = mapped_column(JSON, default=dict)
    chat_settings: Mapped[dict] = mapped_column(JSON, default=lambda: {
        "selective_persistence": True,
        "save_ai_responses": False,
        "auto_purge_days": 30,
        "cache_limit": 10
    })
    stt_anchors: Mapped[list[str]] = mapped_column(JSON, default=list)
    mic_sensitivity: Mapped[float] = mapped_column(Float, default=0.6)

class Role(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'roles'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    code: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String)
    
    # RBAC M2M
    users: Mapped[List["User"]] = relationship("User", secondary=user_roles, back_populates="roles")
    permissions: Mapped[List["Permission"]] = relationship("Permission", secondary=role_permissions, back_populates="roles")
    
    __table_args__ = (
        Index("ix_roles_tenant_deleted", "tenant_id", "deleted_at"),
    )

class Permission(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = 'permissions'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    code: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String)
    
    # RBAC M2M
    roles: Mapped[List["Role"]] = relationship("Role", secondary=role_permissions, back_populates="permissions")

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

class Order(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'orders'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey('users.id'))
    user: Mapped["User"] = relationship("User", back_populates="orders")
    total_amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    items: Mapped[Optional[dict]] = mapped_column(JSON)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String)
    history: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    
    # V56.5 Anti-Spam Shield Fields
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False)
    spam_score: Mapped[float] = mapped_column(Float, default=0.0)
    fingerprint: Mapped[Optional[str]] = mapped_column(String)
    spam_reason: Mapped[Optional[str]] = mapped_column(String)

    
    __table_args__ = (
        Index("ix_orders_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_orders_created_at", "created_at"),
    )

class ProductBase(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'product_bases'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String)
    sku: Mapped[Optional[str]] = mapped_column(String)
    price: Mapped[float] = mapped_column(Float, default=0)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="DRAFT")
    type: Mapped[str] = mapped_column(String, default="RETAIL")
    
    category_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('categories.id'))
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="products")
    
    variants: Mapped[List["ProductVariant"]] = relationship("ProductVariant", back_populates="product_base")
    rentals: Mapped[List["RentalContract"]] = relationship("RentalContract", back_populates="product_base")
    embedding: Mapped[Optional["ProductEmbedding"]] = relationship("ProductEmbedding", back_populates="product_base", uselist=False)
    
    __table_args__ = (
        Index("ix_products_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_products_created_at", "created_at"),
    )

class ProductVariant(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = 'product_variants'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    product_base_id: Mapped[str] = mapped_column(String, ForeignKey('product_bases.id'))
    product_base: Mapped["ProductBase"] = relationship("ProductBase", back_populates="variants")
    sku: Mapped[str] = mapped_column(String, unique=True)
    price: Mapped[float] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer, default=0)

class RentalContract(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = 'rental_contracts'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    product_base_id: Mapped[str] = mapped_column(String, ForeignKey('product_bases.id'))
    product_base: Mapped["ProductBase"] = relationship("ProductBase", back_populates="rentals")
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String, default="ACTIVE")
    terms: Mapped[Optional[dict]] = mapped_column(JSON)

class Draft(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'drafts'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    proposed_by: Mapped[str] = mapped_column(String)
    target_model: Mapped[str] = mapped_column(String)
    target_id: Mapped[Optional[str]] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    
    reviewer_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('users.id'))

class AgentTelemetryLog(Base, AuditMixin, TenantMixin):
    __tablename__ = 'agent_telemetry_logs'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String)
    agent_name: Mapped[str] = mapped_column(String)
    intent_hash: Mapped[str] = mapped_column(String)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_token: Mapped[float] = mapped_column(Float, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

class ChatMessage(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'chat_messages'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String)
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('users.id'))
    user: Mapped[Optional["User"]] = relationship("User", back_populates="chat_messages")
    role: Mapped[str] = mapped_column(String)
    content: Mapped[dict] = mapped_column(JSON)
    modality: Mapped[str] = mapped_column(String, default="text")

class Notification(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'notifications'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('users.id'))
    user: Mapped[Optional["User"]] = relationship("User", back_populates="notifications")
    type: Mapped[str] = mapped_column(String, default="INFO")
    message: Mapped[str] = mapped_column(String)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

class ProductEmbedding(Base, AuditMixin):
    __tablename__ = 'product_embeddings'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    product_base_id: Mapped[str] = mapped_column(String, ForeignKey('product_bases.id'), unique=True)
    product_base: Mapped["ProductBase"] = relationship("ProductBase", back_populates="embedding")
    embedding: Mapped[str] = mapped_column(Text)

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
    
    # The Golden Thread (Khóa cứng sau Bước 1)
    gold_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Step Data
    topic_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    assets_data: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    outline_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    draft_content: Mapped[Optional[str]] = mapped_column(Text)
    search_count: Mapped[int] = mapped_column(Integer, default=0)
    # R102: Deferred Loading for heavy fields (Saves RAM on list queries)
    final_html: Mapped[Optional[str]] = deferred(mapped_column(Text))
    
    # Relationships
    events: Mapped[List["CampaignEvent"]] = relationship("CampaignEvent", back_populates="campaign", cascade="all, delete-orphan")

    # --- PROFESSIONAL CTO HELPERS (Phase 42) ---
    def get_gold_config(self) -> dict:
        """Returns the creation configuration from gold_metadata safely."""
        gold = self.gold_metadata or {}
        return gold.get("creation_config") or {}

    def get_gold_val(self, key: str, default: any = None) -> any:
        """Surgically extracts a value from gold_metadata or falls back to topic_data."""
        gold = self.gold_metadata or {}
        if key in gold: return gold[key]
        
        topic = self.topic_data or {}
        return topic.get(key, default)

    __table_args__ = (
        Index("ix_campaigns_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_campaigns_status", "status"),
    )

class CampaignEvent(Base, AuditMixin, TenantMixin):
    """V60.2: Standardized Event Log (Decoupled from Campaign table to avoid bloat)"""
    __tablename__ = 'campaign_events'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String, sa.ForeignKey('content_campaigns.id', ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String, index=True) # e.g., ERROR, PROGRESS, STEP_COMPLETE
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    
    campaign: Mapped["ContentCampaign"] = relationship("ContentCampaign", back_populates="events")

    __table_args__ = (
        Index("ix_campaign_events_tenant", "tenant_id"),
    )
