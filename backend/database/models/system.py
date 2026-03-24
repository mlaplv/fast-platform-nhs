from typing import Optional
import sqlalchemy as sa
from sqlalchemy import (
    String, ForeignKey, Integer, JSON, Boolean, Float
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.models.base import Base, AuditMixin, SoftDeleteMixin, TenantMixin

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

class SystemSetting(Base, AuditMixin):
    __tablename__ = 'system_settings'

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
