from typing import Optional
import sqlalchemy as sa
from sqlalchemy import (
    String, ForeignKey, Integer, JSON, Boolean, Float, Enum as SQLEnum, Text, Index
)
import enum
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.models.base import Base, AuditMixin, SoftDeleteMixin, TenantMixin

class Draft(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'drafts'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    proposed_by: Mapped[str] = mapped_column(String)
    target_model: Mapped[str] = mapped_column(String)
    target_id: Mapped[Optional[str]] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    
    reviewer_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('users.id'))

class AgentTelemetryLog(Base, AuditMixin, TenantMixin):
    __tablename__ = 'agent_telemetry_logs'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String)
    agent_name: Mapped[str] = mapped_column(String)
    intent_hash: Mapped[str] = mapped_column(String)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_token: Mapped[float] = mapped_column(Float, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

class ChatMessage(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'chat_messages'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String)
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('users.id'))
    user: Mapped[Optional["User"]] = relationship("User", back_populates="chat_messages")
    role: Mapped[str] = mapped_column(String)
    content: Mapped[dict] = mapped_column(JSON)
    modality: Mapped[str] = mapped_column(String, default="text")

class Notification(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'notifications'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('users.id'))
    user: Mapped[Optional["User"]] = relationship("User", back_populates="notifications")
    type: Mapped[str] = mapped_column(String, default="INFO")
    message: Mapped[str] = mapped_column(String)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

class SystemSetting(Base, AuditMixin):
    __tablename__ = 'system_settings'

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)

class ReviewEntityType(str, enum.Enum):
    PRODUCT = "PRODUCT"
    NEWS = "NEWS"

class SystemReview(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'system_reviews'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
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
    
    __table_args__ = (
        Index("ix_sys_reviews_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_sys_reviews_entity", "entity_type", "entity_id"),
        Index("ix_sys_reviews_created_at_status", "created_at", "status"),
    )
