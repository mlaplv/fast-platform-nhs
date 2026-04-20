from typing import Optional, List
import sqlalchemy as sa
from sqlalchemy import (
    String, ForeignKey, Table, Column, Index, JSON, Float
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.models.base import Base, AuditMixin, SoftDeleteMixin, TenantMixin
from backend.constants.voice import DEFAULT_GREETING, DEFAULT_FAREWELL

# association tables
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

import uuid

class User(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'users'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[Optional[str]] = mapped_column(String)
    phone: Mapped[Optional[str]] = mapped_column(String, index=True) # Elite V2.2
    password: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="ACTIVE")
    
    # Profile Elite V3.0
    gender: Mapped[Optional[str]] = mapped_column(String) # MALE, FEMALE, OTHER
    dob: Mapped[Optional[sa.DateTime]] = mapped_column(sa.DateTime(timezone=True))
    avatar_url: Mapped[Optional[str]] = mapped_column(String)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict) # Elite V3.0: Skin profile, tier, etc.

    security_stamp: Mapped[str] = mapped_column(String, default=lambda: str(uuid.uuid4()))
    
    # Relationships
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")
    drafts: Mapped[List["Draft"]] = relationship("Draft", foreign_keys="Draft.reviewer_id")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    content_campaigns: Mapped[List["ContentCampaign"]] = relationship("ContentCampaign", back_populates="user", cascade="all, delete-orphan")
    articles: Mapped[List["Article"]] = relationship("Article", back_populates="author")
    chat_messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="user")
    voice_profile: Mapped[Optional["VoiceProfile"]] = relationship("VoiceProfile", back_populates="user", uselist=False)
    loyalty: Mapped[Optional["UserLoyalty"]] = relationship("UserLoyalty", uselist=False)
    
    # RBAC M2M
    roles: Mapped[List["Role"]] = relationship("Role", secondary=user_roles, back_populates="users")

    __table_args__ = (
        Index("ix_users_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_users_phone_tenant", "tenant_id", "phone", "deleted_at", unique=True),
    )

class VoiceProfile(Base, AuditMixin):
    __tablename__ = 'voice_profiles'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey('users.id'), unique=True)
    user: Mapped["User"] = relationship("User", back_populates="voice_profile")
    wake_words: Mapped[list[str]] = mapped_column(JSON, default=list)
    sleep_words: Mapped[list[str]] = mapped_column(JSON, default=list)
    greeting_template: Mapped[str] = mapped_column(String, default=DEFAULT_GREETING)
    farewell_template: Mapped[str] = mapped_column(String, default=DEFAULT_FAREWELL)
    capabilities: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    chat_settings: Mapped[dict[str, object]] = mapped_column(JSON, default=lambda: {
        "selective_persistence": True,
        "save_ai_responses": False,
        "auto_purge_days": 30,
        "cache_limit": 10
    })
    stt_anchors: Mapped[list[str]] = mapped_column(JSON, default=list)
    mic_sensitivity: Mapped[float] = mapped_column(Float, default=0.6)
    gemini_keys_enc: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True) # V70: Secure keys
    ai_models: Mapped[list[str]] = mapped_column(JSON, default=list) # V75: Model waterfall
    primary_model: Mapped[Optional[str]] = mapped_column(String, nullable=True) # V75: Main model
    discovered_models: Mapped[list[str]] = mapped_column(JSON, default=list) # V75.7: Cached suggestions

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
