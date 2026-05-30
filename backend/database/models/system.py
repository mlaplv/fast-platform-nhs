from datetime import datetime
from typing import Optional
import sqlalchemy as sa
from sqlalchemy import (
    String, ForeignKey, Integer, JSON, Boolean, Float, Enum as SQLEnum, Text, Index
)
import enum
import uuid
from backend.utils.uid import new_id_default
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.models.base import Base, AuditMixin, SoftDeleteMixin, TenantMixin

class Draft(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'drafts'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    proposed_by: Mapped[str] = mapped_column(String)
    target_model: Mapped[str] = mapped_column(String)
    target_id: Mapped[Optional[str]] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    payload: Mapped[dict[str, object]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    
    reviewer_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('users.id'))

class AgentTelemetryLog(Base, AuditMixin, TenantMixin):
    __tablename__ = 'agent_telemetry_logs'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    session_id: Mapped[str] = mapped_column(String)
    agent_name: Mapped[str] = mapped_column(String)
    intent_hash: Mapped[str] = mapped_column(String)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_token: Mapped[float] = mapped_column(Float, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

class ChatMessage(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'chat_messages'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    session_id: Mapped[str] = mapped_column(String)
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('users.id'))
    user: Mapped[Optional["User"]] = relationship("User", back_populates="chat_messages")
    role: Mapped[str] = mapped_column(String)
    content: Mapped[dict[str, object]] = mapped_column(JSON)
    modality: Mapped[str] = mapped_column(String, default="text")

    # [Elite V2.2 — Bug #3 Fix] Composite indexes for O(log n) history queries
    # Pattern: Zalo/Messenger keyset pagination standard
    __table_args__ = (
        Index("ix_chat_user_time", "user_id", "created_at"),      # /sessions/account/messages
        Index("ix_chat_session_time", "session_id", "created_at"), # /sessions/{id}/messages
        Index("ix_chat_deleted_at", "deleted_at"),                 # WHERE deleted_at IS NULL
    )

class Notification(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'notifications'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('users.id'))
    user: Mapped[Optional["User"]] = relationship("User", back_populates="notifications")
    type: Mapped[str] = mapped_column(String, default="INFO")
    message: Mapped[str] = mapped_column(String)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index("ix_notifications_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_notifications_user_read", "user_id", "is_read", "deleted_at"),
    )

class SystemSetting(Base, AuditMixin):
    __tablename__ = 'system_settings'

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)

class ReviewEntityType(str, enum.Enum):
    PRODUCT = "PRODUCT"
    CATEGORY = "CATEGORY"
    NEWS = "NEWS"

class SystemReview(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'system_reviews'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    
    # Polymorphic Router
    entity_type: Mapped[ReviewEntityType] = mapped_column(SQLEnum(ReviewEntityType), index=True)
    entity_id: Mapped[str] = mapped_column(String, index=True) # ID của Product hoặc News
    
    # Review Data
    customer_name: Mapped[str] = mapped_column(String(255))
    customer_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    customer_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rating: Mapped[int] = mapped_column(Integer) # 1-5
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)

    # Elite V2.2: Rich Meta & Attachments (Explicit JSONB for Postgres Performance)
    attributes: Mapped[Optional[dict[str, object]]] = mapped_column(sa.dialects.postgresql.JSONB, nullable=True) # e.g. {"Thấm thấu": "Tham nhanh", ...}
    attachments: Mapped[Optional[list[dict[str, object]]]] = mapped_column(sa.dialects.postgresql.JSONB, nullable=True) # e.g. [{"url": "...", "type": "image"}]
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    
    __table_args__ = (
        Index("ix_sys_reviews_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_sys_reviews_entity", "entity_type", "entity_id"),
        Index("ix_sys_reviews_created_at_status", "created_at", "status"),
        Index("ix_sys_reviews_entity_status_time", "entity_type", "entity_id", "status", "created_at"),
    )

class SupportChatHistory(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'support_chat_history'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    session_id: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String) # user, assistant
    content: Mapped[str] = mapped_column(Text)
    intent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    product_slug: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    
    # Elite V2.2: Identify customer in history for Zalo/Staff Bridge
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Elite V2.2.1: Revoke message support (Admin control)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index("ix_support_chat_session_created", "session_id", "created_at"),
    )

class SupportKnowledgeCategory(str, enum.Enum):
    """Enum for knowledge base categorization (Elite V2.2)"""
    GENERAL  = "GENERAL"
    POLICY   = "POLICY"
    SHIPPING = "SHIPPING"
    PRODUCT  = "PRODUCT"
    PROMO    = "PROMO"
    INFO_INGREDIENTS = "INFO_INGREDIENTS"
    INFO_ADDRESS     = "INFO_ADDRESS"
    INFO_HOTLINE     = "INFO_HOTLINE"
    PRICE_QUERY      = "PRICE_QUERY"
    INFO_SHIPPING    = "INFO_SHIPPING"

class SupportKnowledge(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    """
    Elite V2.2: RAG Knowledge Base for Support Agent.
    Stores pre-approved Q&A, policies, and brand information.
    """
    __tablename__ = 'support_knowledge'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    
    category: Mapped[SupportKnowledgeCategory] = mapped_column(SQLEnum(SupportKnowledgeCategory), default=SupportKnowledgeCategory.GENERAL, index=True)
    
    # Extended RAG (Elite V2.2)
    product_id: Mapped[Optional[str]] = mapped_column(String, sa.ForeignKey('product_bases.id'), index=True, nullable=True)
    source_type: Mapped[str] = mapped_column(String(20), default="TEXT") # TEXT, URL, PDF, HTML
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # the url or minio path
    
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    
    # Metadata for search & relevance
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    tags: Mapped[Optional[dict[str, object]]] = mapped_column(JSON, nullable=True) # list of tags
    priority: Mapped[int] = mapped_column(Integer, default=0) # higher = more relevant
    
    __table_args__ = (
        Index("ix_support_knowledge_tenant_active", "tenant_id", "is_active"),
    )

class SupportKnowledgeEmbedding(Base, AuditMixin, TenantMixin):
    """Elite V2.2: pgvector persistence for Knowledge Base."""
    __tablename__ = 'support_knowledge_embeddings'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    knowledge_id: Mapped[str] = mapped_column(String, sa.ForeignKey('support_knowledge.id'), unique=True, index=True)
    embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Will be cast to vector in SQL operations

class UnifiedAgentTask(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    """
    Elite V2.2: Universal Task Persistence for AI Operatives.
    Stores metadata for background jobs (Helen & XoHi).
    """
    __tablename__ = 'unified_agent_tasks'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    
    agent_id: Mapped[str] = mapped_column(String, index=True)
    task_id: Mapped[str] = mapped_column(String, unique=True, index=sa.Index("ix_unified_task_task_id"))
    session_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    
    status: Mapped[str] = mapped_column(String, default="PENDING", index=True) # PENDING, RUNNING, DONE, FAILED
    payload: Mapped[dict[str, object]] = mapped_column(JSON)
    result: Mapped[Optional[dict[str, object]]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Tracking for 3-day retention policy
    completed_at: Mapped[Optional[sa.DateTime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_unified_task_tenant_status", "tenant_id", "status"),
        Index("ix_unified_task_agent_status", "agent_id", "status"),
    )

class AuditLog(Base, TenantMixin):
    """
    Elite V2.2: Forensic Audit Trail.
    Lưu vết mọi thao tác thay đổi dữ liệu nhạy cảm.
    """
    __tablename__ = 'audit_logs'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    
    # Actor Info
    actor_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Action Info
    action: Mapped[str] = mapped_column(String(20), index=True) # INSERT, UPDATE, DELETE
    target_table: Mapped[str] = mapped_column(String(50), index=True)
    target_id: Mapped[str] = mapped_column(String(50), index=True)
    
    # Data Change (Old vs New)
    changes: Mapped[dict[str, object]] = mapped_column(sa.dialects.postgresql.JSONB)
    
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now(), index=True)

    __table_args__ = (
        Index("ix_audit_logs_target", "target_table", "target_id"),
        Index("ix_audit_logs_actor_time", "actor_id", "created_at"),
    )
